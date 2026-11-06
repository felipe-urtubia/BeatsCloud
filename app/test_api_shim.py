import json
import re
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.test.client import MULTIPART_CONTENT, encode_multipart
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from .models import (
    Comentario,
    Genero_Musical,
    HistorialCompra,
    Suscripcion,
    Track,
    Usuario,
    WebpayTransaction,
)


class ApiShimSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="artist", password="secret")
        self.profile = Usuario.objects.create(user=self.user, tipo_usu=Usuario.ARTISTA)
        self.genre = Genero_Musical.objects.create(descripcion="Pop")
        self.track = Track.objects.create(
            nombre_track="Track de prueba",
            precio=1000,
            genero=self.genre,
            usuario=self.profile,
        )

    def assert_method_not_allowed(self, response, allow):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], allow)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_existing_nine_method_restrictions_and_allow_headers(self):
        cases = (
            ("/api/csrf/", "post", "GET"),
            ("/api/session/", "post", "GET"),
            ("/api/auth/login/", "get", "POST"),
            ("/api/auth/logout/", "get", "POST"),
            ("/api/auth/registro/", "get", "POST"),
            ("/api/auth/activar/", "get", "POST"),
            ("/api/auth/password-reset/", "get", "POST"),
            ("/api/auth/password-reset/confirm/", "get", "POST"),
            ("/api/catalogo/", "post", "GET"),
            ("/api/usuarios/", "post", "GET"),
            (f"/api/track/{self.track.pk}/comentarios/", "put", "DELETE, GET, POST"),
            (f"/api/track/{self.track.pk}/preview/", "post", "GET"),
            (f"/api/track/{self.track.pk}/reproducir/", "post", "GET"),
            (f"/api/track/{self.track.pk}/descargar/", "post", "GET"),
        )
        for path, method, allow in cases:
            with self.subTest(path=path, method=method):
                response = getattr(self.client, method)(path)
                self.assert_method_not_allowed(response, allow)

    def test_get_endpoints_and_subscription_creation_methods(self):
        self.client.force_login(self.user)
        paths = (
            "/api/mis-ventas/",
            "/api/mis-compras/",
            f"/api/perfil/{self.user.username}/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
                self.assert_method_not_allowed(self.client.post(path), "GET")
                self.assert_method_not_allowed(self.client.put(path), "GET")
        self.assertEqual(self.client.get("/api/suscripciones/").status_code, 200)
        self.assertEqual(self.client.post("/api/suscripciones/").status_code, 403)
        self.assert_method_not_allowed(
            self.client.put("/api/suscripciones/"), "GET, POST"
        )

    def test_producer_can_create_subscription_plan(self):
        producer = User.objects.create_user(username="producer", password="valid-password")
        Usuario.objects.create(user=producer, tipo_usu=Usuario.PRODUCTOR)
        self.client.force_login(producer)

        response = self.client.post(
            "/api/suscripciones/",
            data=json.dumps({"detalle": "Plan mensual", "precio": 5000}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["detalle"], "Plan mensual")
        self.assertEqual(response.json()["precio"], 5000)
        self.assertTrue(
            Suscripcion.objects.filter(user__user=producer, detalle="Plan mensual").exists()
        )

    def test_track_detail_allows_get_patch_put_and_rejects_delete(self):
        self.client.force_login(self.user)
        path = f"/api/track/{self.track.pk}/"
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(
            self.client.patch(
                path,
                data=json.dumps({"nombre_track": "Editado"}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                path,
                data=json.dumps({"descripcion": "Descripción"}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assert_method_not_allowed(self.client.delete(path), "GET, PATCH, PUT")

    def create_pending_transaction(self, user):
        return WebpayTransaction.objects.create(
            user=user,
            buy_order=f"order-{user.pk}",
            session_id=user.username,
            amount="1000.00",
            status=WebpayTransaction.ESTADO_PENDIENTE,
        )

    def test_payment_cancel_requires_authentication(self):
        payment = self.create_pending_transaction(self.user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 401)
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)

    def test_payment_cancel_requires_provider_confirmation(self):
        payment = self.create_pending_transaction(self.user)
        self.client.force_login(self.user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 409)
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)

    def test_payment_cancel_hides_other_users_transaction(self):
        payment = self.create_pending_transaction(self.user)
        other_user = User.objects.create_user(username="other", password="secret")
        self.client.force_login(other_user)
        response = self.client.post(f"/api/pago/cancelar/{payment.pk}/")
        self.assertEqual(response.status_code, 404)
        payment.refresh_from_db()
        self.assertEqual(payment.status, WebpayTransaction.ESTADO_PENDIENTE)

    def test_logout_post_succeeds_and_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertIsNone(self.client.get("/api/session/").json())

    def test_login_api_accepts_local_react_origin_with_csrf(self):
        self.user.set_password("valid-password")
        self.user.save(update_fields=["password"])
        client = self.client_class(enforce_csrf_checks=True)

        csrf_response = client.get("/api/csrf/")
        self.assertEqual(csrf_response.status_code, 200)
        csrf_token = csrf_response.json()["detail"]
        response = client.post(
            "/api/auth/login/",
            data=json.dumps({"username": self.user.username, "password": "valid-password"}),
            content_type="application/json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["username"], self.user.username)

    def test_users_directory_returns_public_profiles_without_private_relations(self):
        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        user_data = response.json()[0]
        self.assertEqual(user_data["username"], self.user.username)
        self.assertEqual(user_data["email"], "")
        self.assertNotIn("liked_track_ids", user_data)
        self.assertNotIn("subscription_ids", user_data)

    def test_session_contains_own_likes_and_subscriptions(self):
        subscription = Suscripcion.objects.create(
            detalle="Plan de prueba",
            precio=5000,
            user=self.profile,
        )
        self.profile.tracks_gustados.add(self.track)
        self.profile.sus.add(subscription)
        self.client.force_login(self.user)

        response = self.client.get("/api/session/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liked_track_ids"], [self.track.pk])
        self.assertEqual(response.json()["subscription_ids"], [subscription.pk])

    def test_upload_api_persists_track_for_catalog_and_producer_profile(self):
        producer = User.objects.create_user(username="producer", password="test-password")
        Usuario.objects.create(user=producer, tipo_usu=Usuario.PRODUCTOR)
        self.client.force_login(producer)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with patch("mutagen.File", return_value=object()), patch(
                    "app.api_shim.generar_preview_audio"
                ):
                    response = self.client.post(
                        "/api/upload/",
                        {
                            "nombre_track": "Beat persistente",
                            "precio": "12000",
                            "descripcion": "Pista de prueba",
                            "genero": "Trap",
                            "subgenre": "Dark Latin Trap",
                            "resource_type": "loop",
                            "bpm": "112",
                            "scale_key": "C Minor",
                            "mood": "Chill / Relax",
                            "has_stems": "true",
                            "has_wav": "true",
                            "has_midi": "false",
                            "allow_free_download": "true",
                            "has_watermark": "false",
                            "duration": "95",
                            "track": SimpleUploadedFile(
                                "beat.wav", b"audio de prueba", content_type="audio/wav"
                            ),
                        },
                    )

                self.assertEqual(response.status_code, 201, response.content)
                uploaded = Track.objects.get(nombre_track="Beat persistente")
                self.assertEqual(uploaded.usuario.user, producer)
                self.assertEqual(uploaded.genero.descripcion, "Hip-Hop")
                self.assertEqual(uploaded.subgenre, "Dark Latin Trap")
                self.assertEqual(uploaded.resource_type, "loop")
                self.assertEqual(uploaded.bpm, 112)
                self.assertEqual(uploaded.scale_key, "C Minor")
                self.assertEqual(uploaded.mood, "Chill / Relax")
                self.assertTrue(uploaded.has_stems)
                self.assertTrue(uploaded.allow_free_download)
                self.assertFalse(uploaded.has_watermark)
                self.assertEqual(uploaded.duration, 95)
                self.assertTrue(uploaded.track.storage.exists(uploaded.track.name))

                catalog_track_ids = {
                    item["id_track"] for item in self.client.get("/api/catalogo/").json()["tracks"]
                }
                profile_track_ids = {
                    item["id_track"]
                    for item in self.client.get(f"/api/perfil/{producer.username}/").json()["tracks"]
                }
                self.assertIn(uploaded.pk, catalog_track_ids)
                self.assertIn(uploaded.pk, profile_track_ids)

    def test_track_update_persists_metadata_and_genre(self):
        self.profile.tipo_usu = Usuario.PRODUCTOR
        self.profile.save(update_fields=["tipo_usu"])
        self.client.force_login(self.user)
        cover_buffer = BytesIO()
        Image.new("RGB", (1, 1)).save(cover_buffer, format="PNG")

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.patch(
                    f"/api/track/{self.track.pk}/",
                    data=encode_multipart(
                        "BoUnDaRyStRiNg",
                        {
                            "nombre_track": "Metadata actualizada",
                            "precio": 0,
                            "resource_type": "acapella",
                            "bpm": 98,
                            "scale_key": "G Minor",
                            "mood": "Triste / Nostálgico",
                            "has_stems": True,
                            "has_wav": False,
                            "has_midi": True,
                            "allow_free_download": True,
                            "has_watermark": False,
                            "duration": 210,
                            "genero": "Trap",
                            "subgenre": "Latin Acapella",
                            "foto": SimpleUploadedFile(
                                "cover.png", cover_buffer.getvalue(), content_type="image/png"
                            ),
                        },
                    ),
                    content_type=MULTIPART_CONTENT,
                )

        self.assertEqual(response.status_code, 200, response.content)
        self.track.refresh_from_db()
        self.assertEqual(self.track.nombre_track, "Metadata actualizada")
        self.assertEqual(self.track.precio, 0)
        self.assertEqual(self.track.genero.descripcion, "Hip-Hop")
        self.assertEqual(self.track.subgenre, "Latin Acapella")
        self.assertEqual(self.track.resource_type, "acapella")
        self.assertEqual(self.track.bpm, 98)
        self.assertEqual(self.track.duration, 210)
        self.assertTrue(self.track.foto.name.endswith("cover.png"))

    def test_free_claim_creates_purchase_record_and_returns_signed_license(self):
        self.track.precio = 0
        self.track.save(update_fields=["precio"])
        self.client.force_login(self.user)

        claim = self.client.post(f"/api/track/{self.track.pk}/claim-free/")
        license_response = self.client.get(f"/api/track/{self.track.pk}/license/")

        self.assertEqual(claim.status_code, 200, claim.content)
        self.assertTrue(
            HistorialCompra.objects.filter(usuario=self.profile, track=self.track).exists()
        )
        self.assertEqual(license_response.status_code, 200, license_response.content)
        self.assertEqual(license_response.json()["amount_clp"], 0)
        self.assertEqual(len(license_response.json()["verification_hash"]), 64)

    def test_profile_update_persists_text_fields(self):
        self.client.force_login(self.user)

        response = self.client.patch(
            "/api/perfil/",
            data=encode_multipart(
                "BoUnDaRyStRiNg",
                {
                    "descripcion": "Productora y artista",
                    "spotify": "https://open.spotify.com/artist/example",
                    "instagram": "https://instagram.com/example",
                },
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.descripcion, "Productora y artista")
        self.assertEqual(self.profile.spotify, "https://open.spotify.com/artist/example")
        self.assertEqual(self.profile.instagram, "https://instagram.com/example")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_account_deletion_api_requires_email_code_and_deletes_account(self):
        self.user.email = "artist@example.com"
        self.user.set_password("valid-password")
        self.user.save(update_fields=["email", "password"])
        self.client.force_login(self.user)

        start = self.client.post(
            "/api/auth/account-deletion/start/",
            data=json.dumps({"password": "valid-password"}),
            content_type="application/json",
        )
        self.assertEqual(start.status_code, 200, start.content)
        self.assertEqual(len(mail.outbox), 1)
        code = re.search(r"\b\d{6}\b", mail.outbox[0].body).group()

        confirm = self.client.post(
            "/api/auth/account-deletion/confirm/",
            data=json.dumps({"codigo": code}),
            content_type="application/json",
        )

        self.assertEqual(confirm.status_code, 200, confirm.content)
        self.assertEqual(confirm.json(), {"ok": True})
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_comment_delete_requires_ownership(self):
        comment = Comentario.objects.create(
            usuario=self.user,
            track=self.track,
            contenido="Comentario de prueba",
        )
        path = f"/api/track/{self.track.pk}/comentarios/?id={comment.pk}"
        self.assertEqual(self.client.delete(path).status_code, 401)

        other_user = User.objects.create_user(username="other", password="other-pass")
        self.client.force_login(other_user)
        self.assertEqual(self.client.delete(path).status_code, 404)
        self.assertTrue(Comentario.objects.filter(pk=comment.pk).exists())

        self.client.force_login(self.user)
        self.assertEqual(self.client.delete(path).json(), {"ok": True})
        self.assertFalse(Comentario.objects.filter(pk=comment.pk).exists())

    def test_subscription_directory_includes_public_producer(self):
        Suscripcion.objects.create(
            detalle="Plan productor",
            precio=5000,
            user=self.profile,
        )

        response = self.client.get("/api/suscripciones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["user"]["id"], self.user.pk)
        self.assertEqual(response.json()[0]["user"]["email"], "")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="http://localhost:3000",
    )
    def test_registration_saves_artistic_name_and_sends_activation_email(self):
        response = self.client.post(
            "/api/auth/registro/",
            {
                "username": "mcflow-login",
                "email": "MCFlow@Example.com",
                "first_name": "María",
                "last_name": "Pérez",
                "nombre_artistico": "MC Flow",
                "password1": "StrongPass123!x",
                "password2": "StrongPass123!x",
                "tipo_usu": Usuario.ARTISTA,
            },
        )

        self.assertEqual(response.status_code, 201, response.content)
        user = User.objects.get(username="mcflow-login")
        self.assertFalse(user.is_active)
        self.assertEqual(user.first_name, "María")
        self.assertEqual(user.last_name, "Pérez")
        self.assertEqual(user.email, "mcflow@example.com")
        self.assertEqual(user.usuario.nombre_artistico, "MC Flow")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://localhost:3000/activar/", mail.outbox[0].body)
        activation_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("background-color:#0a0c10", activation_html)
        self.assertIn("background-color:#fbbf24", activation_html)
        self.assertIn("Confirmar mi cuenta", activation_html)

        public_user = next(
            item
            for item in self.client.get("/api/usuarios/").json()
            if item["username"] == "mcflow-login"
        )
        self.assertEqual(public_user["nombre_artistico"], "MC Flow")

        user.is_active = True
        user.save(update_fields=["is_active"])
        self.client.force_login(user)
        session_response = self.client.get("/api/session/")
        self.assertEqual(session_response.json()["nombre_artistico"], "MC Flow")

    def test_account_activation_validates_token_and_is_idempotent(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        payload = {"uidb64": uidb64, "token": token}

        response = self.client.post(
            "/api/auth/activar/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {"detail": "Cuenta activada. Ya puedes iniciar sesión."},
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        repeated_response = self.client.post(
            "/api/auth/activar/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(repeated_response.status_code, 200, repeated_response.content)

    def test_account_activation_requires_csrf_for_react_origin(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        client = self.client_class(enforce_csrf_checks=True)
        csrf_token = client.get("/api/csrf/").json()["detail"]

        response = client.post(
            "/api/auth/activar/",
            data=json.dumps({"uidb64": uidb64, "token": token}),
            content_type="application/json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_account_activation_rejects_invalid_expired_and_unknown_tokens(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        valid_token = default_token_generator.make_token(self.user)
        cases = (
            {"uidb64": uidb64, "token": "invalid-token"},
            {"uidb64": urlsafe_base64_encode(force_bytes(999999)), "token": valid_token},
            {"uidb64": "not-base64!", "token": valid_token},
        )
        for case in cases:
            with self.subTest(case=case):
                response = self.client.post(
                    "/api/auth/activar/",
                    data=json.dumps(case),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("no es válido", response.json()["detail"])

        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            expired_response = self.client.post(
                "/api/auth/activar/",
                data=json.dumps({"uidb64": uidb64, "token": valid_token}),
                content_type="application/json",
            )
        self.assertEqual(expired_response.status_code, 400)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="http://localhost:3000",
    )
    def test_password_reset_sends_react_link_and_reports_unknown_email(self):
        self.user.email = "artist@example.com"
        self.user.save(update_fields=["email"])

        known_response = self.client.post(
            "/api/auth/password-reset/",
            data=json.dumps({"email": "artist@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(known_response.status_code, 200, known_response.content)
        self.assertIn("Te enviamos un enlace", known_response.json()["detail"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://localhost:3000/restablecer/", mail.outbox[0].body)
        self.assertIn(
            "http://localhost:3000/restablecer/",
            mail.outbox[0].alternatives[0][0],
        )
        self.assertIn("background-color:#0a0c10", mail.outbox[0].alternatives[0][0])
        self.assertIn("background-color:#fbbf24", mail.outbox[0].alternatives[0][0])
        self.assertIn("Restablecer contraseña", mail.outbox[0].alternatives[0][0])

        unknown_response = self.client.post(
            "/api/auth/password-reset/",
            data=json.dumps({"email": "unknown@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(unknown_response.status_code, 200, unknown_response.content)
        self.assertEqual(
            unknown_response.json()["detail"],
            "No encontramos una cuenta activa asociada a ese correo.",
        )
        self.assertNotEqual(known_response.json(), unknown_response.json())
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_django_password_reset_uses_beatscloud_email_design(self):
        self.user.email = "artist@example.com"
        self.user.save(update_fields=["email"])

        response = self.client.post(
            "/recuperar/",
            {"email": "artist@example.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        reset_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("background-color:#0a0c10", reset_html)
        self.assertIn("background-color:#fbbf24", reset_html)
        self.assertIn("Restablecer contraseña", reset_html)
        self.assertIn("/recuperar/", reset_html)

    def test_password_reset_rejects_invalid_email(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            data=json.dumps({"email": "not-an-email"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_changes_password_and_invalidates_token(self):
        self.user.email = "artist@example.com"
        self.user.save(update_fields=["email"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        payload = {
            "uidb64": uidb64,
            "token": token,
            "new_password1": "StrongResetPass!938",
            "new_password2": "StrongResetPass!938",
        }

        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("StrongResetPass!938"))

        repeated_response = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(repeated_response.status_code, 400)
        self.assertIn("no es válido", repeated_response.json()["detail"])

    def test_password_reset_rejects_reusing_current_password(self):
        current_password = "CurrentSecurePass!938"
        self.user.set_password(current_password)
        self.user.save(update_fields=["password"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps({
                "uidb64": uidb64,
                "token": token,
                "new_password1": current_password,
                "new_password2": current_password,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "La nueva contraseña no puede ser igual a la contraseña actual.",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(current_password))

    def test_password_reset_rejects_mismatched_and_expired_tokens(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps({
                "uidb64": uidb64,
                "token": token,
                "new_password1": "StrongResetPass!938",
                "new_password2": "DifferentResetPass!938",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password2", response.json()["errors"])
        self.assertFalse(self.user.check_password("StrongResetPass!938"))

        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            expired_response = self.client.post(
                "/api/auth/password-reset/confirm/",
                data=json.dumps({
                    "uidb64": uidb64,
                    "token": token,
                    "new_password1": "StrongResetPass!938",
                    "new_password2": "StrongResetPass!938",
                }),
                content_type="application/json",
            )
        self.assertEqual(expired_response.status_code, 400)

    def test_password_reset_similarity_error_is_in_spanish(self):
        self.user.first_name = "ArtistSecurePassword938!"
        self.user.save(update_fields=["first_name"])
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            data=json.dumps({
                "uidb64": uidb64,
                "token": token,
                "new_password1": "ArtistSecurePassword938!",
                "new_password2": "ArtistSecurePassword938!",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "La contraseña es demasiado similar al nombre.",
            response.json()["detail"],
        )
        self.assertIn(
            "La contraseña es demasiado similar al nombre.",
            response.json()["errors"]["new_password2"],
        )

    def test_registration_requires_an_artistic_name(self):
        response = self.client.post(
            "/api/auth/registro/",
            {
                "username": "artist-without-stage-name",
                "email": "artist@example.com",
                "first_name": "Artista",
                "password1": "StrongPass123!x",
                "password2": "StrongPass123!x",
                "tipo_usu": Usuario.ARTISTA,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("nombre_artistico", response.json()["errors"])
        self.assertFalse(User.objects.filter(username="artist-without-stage-name").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_django_registration_form_saves_artistic_name(self):
        response = self.client.post(
            "/registro/",
            {
                "username": "stage-name-user",
                "email": "stage@example.com",
                "first_name": "Nombre",
                "last_name": "Apellido",
                "nombre_artistico": "Nombre Artístico",
                "password1": "StrongPass123!x",
                "password2": "StrongPass123!x",
                "tipo_usu": Usuario.PRODUCTOR,
            },
        )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="stage-name-user")
        self.assertFalse(user.is_active)
        self.assertEqual(user.usuario.nombre_artistico, "Nombre Artístico")
        self.assertEqual(len(mail.outbox), 1)
