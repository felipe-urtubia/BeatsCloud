from __future__ import annotations

import hashlib
import shutil
import tempfile
import wave
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from app.management.commands._qa_safety import validate_local_database
from app.models import Genero_Musical, Track, Usuario


@override_settings(MEDIA_ROOT="/tmp/beatscloud-qa-catalog-tests")
class QACatalogCommandTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory(prefix="beatscloud-qa-test-")
        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.temp_media.cleanup()

    def _run(self, *, count=4, seed=2718, reset=False):
        call_command(
            "generate_qa_catalog",
            count=count,
            seed=seed,
            reset=reset,
            stdout=__import__("io").StringIO(),
        )

    def test_generator_is_seeded_idempotent_playable_and_covers_backend_filters(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("FFmpeg is required to validate generated previews.")
        # Unit tests run against Django's temporary test DB; direct command use
        # still enforces the stricter beatscloud_qa_* database prefix.
        with patch("app.management.commands.generate_qa_catalog.validate_local_database"):
            self._run()

            generated = list(Track.objects.filter(original_filename__startswith="qa-catalog:v1:").order_by("pk"))
            self.assertEqual(len(generated), 4)
            self.assertEqual(len({track.nombre_track for track in generated}), 4)
            self.assertEqual(len({track.track.name for track in generated}), 4)
            self.assertTrue(all(track.media_status == "ready" for track in generated))
            self.assertTrue(all(track.track and track.preview and track.foto for track in generated))
            self.assertEqual({track.bpm for track in generated[:2]}, {60, 180})
            self.assertEqual({track.precio for track in generated} & {0}, {0})
            self.assertTrue(all(len(track.descripcion) <= 500 for track in generated))
            self.assertTrue(all(not track.has_stems and not track.has_midi for track in generated))

            wav_hashes = []
            for track in generated:
                original_path = Path(track.track.path)
                preview_path = Path(track.preview.path)
                cover_path = Path(track.foto.path)
                self.assertTrue(original_path.is_file())
                self.assertTrue(preview_path.is_file())
                self.assertTrue(cover_path.is_file())
                with wave.open(str(original_path), "rb") as audio:
                    self.assertGreater(audio.getnframes(), 0)
                    self.assertEqual(audio.getframerate(), 22050)
                    self.assertEqual(audio.getnframes() // audio.getframerate(), track.duration)
                wav_hashes.append(hashlib.sha256(original_path.read_bytes()).hexdigest())

            self.assertEqual(len(set(wav_hashes)), len(wav_hashes))
            page = self.client.get(reverse("api_catalogo"))
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.json()["total_resultados"], 4)
            preview = self.client.get(reverse("api_preview", args=[generated[0].pk]))
            try:
                self.assertEqual(preview.status_code, 200)
                self.assertTrue(preview["Content-Type"].startswith("audio/"))
            finally:
                if preview.streaming:
                    for _ in preview.streaming_content:
                        pass

            before = {
                track.original_filename: (
                    track.nombre_track,
                    track.precio,
                    track.bpm,
                    hashlib.sha256(Path(track.track.path).read_bytes()).hexdigest(),
                )
                for track in generated
            }
            self._run()
            self.assertEqual(
                Track.objects.filter(original_filename__startswith="qa-catalog:v1:").count(),
                4,
            )
            after = {
                track.original_filename: (
                    track.nombre_track,
                    track.precio,
                    track.bpm,
                    hashlib.sha256(Path(track.track.path).read_bytes()).hexdigest(),
                )
                for track in Track.objects.filter(original_filename__startswith="qa-catalog:v1:")
            }
            self.assertEqual(before, after)

    def test_reset_only_removes_marked_catalog_rows_and_media(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("FFmpeg is required to validate generated previews.")
        with patch("app.management.commands.generate_qa_catalog.validate_local_database"):
            self._run(count=3, seed=11)
            generated_media = list(
                Track.objects.filter(original_filename__startswith="qa-catalog:v1:")
            )
            old_paths = [Path(track.track.path) for track in generated_media]

            user = User.objects.create_user(username="unrelated-user", password="qa-test-password")
            profile = Usuario.objects.create(user=user, tipo_usu=Usuario.PRODUCTOR)
            genre, _ = Genero_Musical.objects.get_or_create(descripcion="Pop")
            unrelated = Track.objects.create(
                nombre_track="Registro preexistente ajeno",
                precio=1000,
                genero=genre,
                usuario=profile,
                original_filename="unrelated-source.wav",
                media_status="failed",
            )

            self._run(count=2, seed=12, reset=True)

            self.assertTrue(Track.objects.filter(pk=unrelated.pk).exists())
            self.assertEqual(
                Track.objects.filter(original_filename__startswith="qa-catalog:v1:").count(),
                2,
            )
            self.assertTrue(all(not path.exists() for path in old_paths))
            self.assertTrue(all(
                track.original_filename.startswith("qa-catalog:v1:12:")
                for track in Track.objects.filter(original_filename__startswith="qa-catalog:v1:")
            ))


class QADatabaseSafetyTests(TestCase):
    def test_database_guard_rejects_nonlocal_or_non_qa_targets(self):
        with self.assertRaises(CommandError):
            validate_local_database({
                "NAME": "beatsbd",
                "HOST": "127.0.0.1",
                "ENGINE": "django.db.backends.postgresql",
            })
        with self.assertRaises(CommandError):
            validate_local_database({
                "NAME": "beatscloud_qa_prod_like",
                "HOST": "db.example.invalid",
                "ENGINE": "django.db.backends.postgresql",
            })
        with self.assertRaises(CommandError):
            validate_local_database({
                "NAME": "beatscloud_qa_local",
                "HOST": "127.0.0.1",
                "ENGINE": "django.db.backends.sqlite3",
            })
        self.assertEqual(
            validate_local_database({
                "NAME": "beatscloud_qa_local",
                "HOST": "127.0.0.1",
                "ENGINE": "django.db.backends.postgresql",
            }),
            "beatscloud_qa_local",
        )

    def test_demo_database_requires_explicit_demo_prefix(self):
        config = {
            "NAME": "beatscloud_demo_local",
            "HOST": "127.0.0.1",
            "ENGINE": "django.db.backends.postgresql",
        }
        self.assertEqual(
            validate_local_database(
                config,
                prefixes=("beatscloud_qa_", "beatscloud_demo_"),
            ),
            "beatscloud_demo_local",
        )
        with self.assertRaises(CommandError):
            validate_local_database(config)


class QAUserCommandTests(TestCase):
    def test_accounts_are_active_role_scoped_and_passwords_rotate_only_on_request(self):
        from io import StringIO
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with patch("app.management.commands.prepare_qa_users.validate_local_database"):
            with TemporaryDirectory() as tmp:
                credentials_file = Path(tmp) / ".qa-private" / "credenciales-qa.txt"
                with patch("django.conf.settings.BASE_DIR", Path(tmp)):
                    first_output = StringIO()
                    call_command("prepare_qa_users", stdout=first_output)
                    self.assertNotIn("qa-comprador:", first_output.getvalue())
                    self.assertTrue(credentials_file.exists())
                    self.assertEqual(credentials_file.stat().st_mode & 0o777, 0o600)
                    saved_credentials = credentials_file.read_text(encoding="utf-8")
                    self.assertIn("qa-comprador:", saved_credentials)
                    self.assertIn("qa-productor:", saved_credentials)
                    self.assertIn("qa-admin:", saved_credentials)
            initial_passwords = {
                name: User.objects.get(username=name).password
                for name, *_ in (
                    ("qa-comprador",), ("qa-productor",), ("qa-admin",)
                )
            }
            buyer = User.objects.get(username="qa-comprador")
            producer = User.objects.get(username="qa-productor")
            admin = User.objects.get(username="qa-admin")
            self.assertTrue(buyer.is_active)
            self.assertEqual(buyer.usuario.tipo_usu, Usuario.ARTISTA)
            self.assertEqual(producer.usuario.tipo_usu, Usuario.PRODUCTOR)
            self.assertTrue(admin.is_superuser and admin.is_staff and admin.is_active)

            repeat_output = StringIO()
            with patch("django.conf.settings.BASE_DIR", credentials_file.parent.parent):
                call_command("prepare_qa_users", stdout=repeat_output)
            self.assertIn("passwords were not changed", repeat_output.getvalue())
            for username, previous_hash in initial_passwords.items():
                self.assertEqual(User.objects.get(username=username).password, previous_hash)

            with patch("django.conf.settings.BASE_DIR", credentials_file.parent.parent):
                call_command("prepare_qa_users", "--rotate-passwords", stdout=StringIO())
            for username, previous_hash in initial_passwords.items():
                self.assertNotEqual(User.objects.get(username=username).password, previous_hash)
