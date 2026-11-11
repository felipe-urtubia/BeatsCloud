# Generated for BeatCloud D8. No database update until manage.py migrate.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0022_archivo_legacy_webpay"),
    ]

    operations = [
        migrations.AddField(
            model_name="track",
            name="storage_backend",
            field=models.CharField(
                max_length=8,
                choices=(("local", "Local"), ("r2", "R2")),
                default="local",
            ),
        ),
        migrations.AddField(
            model_name="track",
            name="r2_object_key",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="track",
            name="r2_stems_key",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="track",
            name="media_status",
            field=models.CharField(
                max_length=12,
                choices=(("pending", "Pending"), ("processing", "Processing"),
                         ("ready", "Ready"), ("failed", "Failed")),
                default="ready",
            ),
        ),
    ]
