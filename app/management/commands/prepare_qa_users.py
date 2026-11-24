"""Create local QA-only buyer, producer, and admin identities."""

from __future__ import annotations

import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import Usuario
from ._qa_safety import validate_local_database


QA_USERS = (
    ("qa-comprador", "Comprador QA", Usuario.ARTISTA, False),
    ("qa-comprador-carrito", "Comprador QA con carrito", Usuario.ARTISTA, False),
    ("qa-productor", "Productor QA", Usuario.PRODUCTOR, False),
    ("qa-admin", "Administrador QA", Usuario.ARTISTA, True),
)


class Command(BaseCommand):
    help = "Create local demo/QA accounts; temporary passwords are stored in a private file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--rotate-passwords",
            action="store_true",
            help="Generate new temporary passwords for the three isolated QA users.",
        )

    def handle(self, *args, **options):
        validate_local_database(
            settings.DATABASES["default"],
            prefixes=("beatscloud_qa_", "beatscloud_demo_"),
        )
        passwords = {}
        with transaction.atomic():
            for username, display_name, role, is_admin in QA_USERS:
                password = secrets.token_urlsafe(24) if options["rotate_passwords"] else None
                user = User.objects.filter(username=username).first()
                created = user is None
                if created:
                    password = password or secrets.token_urlsafe(24)
                    user = User(username=username, email=f"{username}@beatcloud.local")
                    user.set_password(password)
                elif password:
                    user.set_password(password)

                user.is_active = True
                user.is_staff = is_admin
                user.is_superuser = is_admin
                if is_admin:
                    user.email = f"{username}@beatcloud.local"
                user.save()

                profile, profile_created = Usuario.objects.get_or_create(
                    user=user,
                    defaults={
                        "tipo_usu": role,
                        "nombre_artistico": display_name,
                        "descripcion": f"Cuenta local de pruebas QA: {display_name}.",
                    },
                )
                if not profile_created and profile.tipo_usu != role:
                    profile.tipo_usu = role
                    profile.save(update_fields=["tipo_usu"])
                if password:
                    passwords[username] = password

        credentials_file = Path(settings.BASE_DIR) / ".qa-private" / "credenciales-qa.txt"
        if passwords:
            existing = {}
            if credentials_file.is_file():
                for line in credentials_file.read_text(encoding="utf-8").splitlines():
                    if ": " in line and not line.lstrip().startswith("#"):
                        username, password = line.split(": ", 1)
                        existing[username] = password
            existing.update(passwords)
            credentials_file.parent.mkdir(parents=True, exist_ok=True)
            credentials_file.parent.chmod(0o700)
            credentials_file.write_text(
                "# Local QA only. Never commit or share this file.\n"
                + "".join(f"{username}: {password}\n" for username, password in sorted(existing.items())),
                encoding="utf-8",
            )
            credentials_file.chmod(0o600)
            self.stdout.write("Las credenciales QA nuevas se guardaron en un archivo local privado; no se muestran en pantalla.")
        else:
            self.stdout.write("QA accounts already exist; passwords were not changed.")
        self.stdout.write("Anonymous QA uses the site without signing in.")
