import unittest
from unittest.mock import patch

from django.core import signing

from app.r2_presign import (
    ALLOWED,
    MAX_BYTES,
    TOKEN_SALT,
    URL_EXPIRY_SECONDS,
)
from app.r2_registration_guard import (
    R2RegistrationGuardError,
    validate_r2_track_token,
)


OWNER = 7
KEY = "pending/7/track/" + ("c" * 32) + ".wav"
MIME = sorted(ALLOWED["track"][".wav"])[0]


def crear_token(**cambios):
    datos = {
        "owner": OWNER,
        "key": KEY,
        "size": 1024,
        "kind": "track",
        "mime": MIME,
    }

    datos.update(cambios)

    return signing.dumps(
        datos,
        salt=TOKEN_SALT,
    )


class R2RegistrationGuardTests(unittest.TestCase):

    def comprobar_error(self, token, usuario=OWNER):
        with self.assertRaises(R2RegistrationGuardError):
            validate_r2_track_token(
                upload_token=token,
                user_id=usuario,
            )

    def test_token_valido(self):
        token = crear_token()

        resultado = validate_r2_track_token(
            upload_token=token,
            user_id=OWNER,
        )

        self.assertEqual(resultado.owner, OWNER)
        self.assertEqual(resultado.pending_key, KEY)
        self.assertEqual(resultado.expected_size, 1024)
        self.assertEqual(resultado.expected_mime, MIME)

    def test_rechaza_otro_productor(self):
        self.comprobar_error(
            crear_token(),
            usuario=8,
        )

    def test_rechaza_firma_alterada(self):
        token = crear_token()
        prefijo, separador, firma = token.rpartition(":")

        self.assertTrue(separador)
        self.assertTrue(firma)

        nueva_firma = (
            ("a" if firma[0] != "a" else "b")
            + firma[1:]
        )

        self.comprobar_error(
            prefijo + separador + nueva_firma
        )

    def test_rechaza_token_caducado(self):
        token = crear_token()

        with patch(
            "app.r2_registration_guard.signing.loads",
            side_effect=signing.SignatureExpired(
                "Token expirado"
            ),
        ) as verificar:
            self.comprobar_error(token)

            self.assertEqual(
                verificar.call_args.kwargs["max_age"],
                URL_EXPIRY_SECONDS,
            )

    def test_rechaza_stems_como_cancion(self):
        self.comprobar_error(
            crear_token(kind="stems")
        )

    def test_rechaza_ruta_de_otro_productor(self):
        self.comprobar_error(
            crear_token(
                key="pending/8/track/"
                + ("c" * 32)
                + ".wav"
            )
        )

    def test_rechaza_ruta_privada(self):
        self.comprobar_error(
            crear_token(
                key="private/7/track/"
                + ("c" * 32)
                + ".wav"
            )
        )

    def test_rechaza_mime_invalido(self):
        self.comprobar_error(
            crear_token(mime="application/octet-stream")
        )

    def test_rechaza_tamano_excesivo(self):
        self.comprobar_error(
            crear_token(
                size=MAX_BYTES["track"] + 1
            )
        )

    def test_rechaza_tamano_booleano(self):
        self.comprobar_error(
            crear_token(size=True)
        )

    def test_rechaza_token_con_campos_extra(self):
        self.comprobar_error(
            crear_token(admin=True)
        )

    def test_rechaza_token_vacio(self):
        self.comprobar_error("")

    def test_rechaza_usuario_invalido(self):
        self.comprobar_error(
            crear_token(),
            usuario=0,
        )


if __name__ == "__main__":
    unittest.main()
