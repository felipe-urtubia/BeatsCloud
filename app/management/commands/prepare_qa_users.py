"""Create local QA-only buyer, producer, and admin identities."""

from __future__ import annotations

import secrets

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
    help = "Create local demo/QA accounts; passwords are shown only when created or rotated."

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

        if passwords:
            self.stdout.write(self.style.WARNING(
                "Guarda estas contraseñas temporales en un gestor privado; no se escribieron a archivos."
            ))
            for username, password in passwords.items():
                self.stdout.write(f"{username}: {password}")
        else:
            self.stdout.write("QA accounts already exist; passwords were not changed.")
        self.stdout.write("Anonymous QA uses the site without signing in.")
