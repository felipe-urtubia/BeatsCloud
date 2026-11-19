import base64
import json
import os

from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


class EmailBackend(BaseEmailBackend):
    """Backend de correo Django mediante Gmail API."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        token_json = os.getenv("GMAIL_OAUTH_TOKEN_JSON")

        if not token_json:
            raise ImproperlyConfigured(
                "Falta configurar GMAIL_OAUTH_TOKEN_JSON."
            )

        try:
            datos = json.loads(token_json)

            credenciales = Credentials.from_authorized_user_info(
                datos,
                scopes=SCOPES
            )

            if not credenciales.valid:
                if not credenciales.refresh_token:
                    raise ImproperlyConfigured(
                        "Falta el refresh token de Gmail."
                    )

                credenciales.refresh(Request())

            servicio = build(
                "gmail",
                "v1",
                credentials=credenciales,
                cache_discovery=False
            )

        except Exception:
            if self.fail_silently:
                return 0
            raise

        enviados = 0

        for correo in email_messages:
            try:
                mensaje = correo.message()

                raw = base64.urlsafe_b64encode(
                    mensaje.as_bytes()
                ).decode("ascii")

                servicio.users().messages().send(
                    userId="me",
                    body={"raw": raw}
                ).execute()

                enviados += 1

            except Exception:
                if not self.fail_silently:
                    raise

        return enviados
