from django.conf import settings
from django.db import models


class R2UploadClaim(models.Model):
    """
    Control persistente de una subida R2.

    La clave pendiente es unica para evitar registros
    duplicados. Ninguna solicitud debe considerarse
    completada solo por crear este registro.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="beatcloud_r2_claims",
    )

    pending_key = models.CharField(
        max_length=255,
        unique=True,
    )

    expected_size = models.PositiveBigIntegerField()

    expected_mime = models.CharField(
        max_length=100,
    )

    status = models.CharField(
        max_length=16,
        choices=(
            ("reserved", "Reserved"),
            ("processing", "Processing"),
            ("ready", "Ready"),
            ("failed", "Failed"),
        ),
        default="reserved",
    )

    private_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    track = models.OneToOneField(
        "app.Track",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="r2_registration_claim",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "app_r2_upload_claim"
