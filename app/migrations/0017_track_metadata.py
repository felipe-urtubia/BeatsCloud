from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0016_usuario_nombre_artistico"),
    ]

    operations = [
        migrations.AddField(
            model_name="track",
            name="resource_type",
            field=models.CharField(default="instrumental", max_length=20),
        ),
        migrations.AddField(
            model_name="track",
            name="bpm",
            field=models.PositiveSmallIntegerField(default=140),
        ),
        migrations.AddField(
            model_name="track",
            name="scale_key",
            field=models.CharField(default="Am", max_length=20),
        ),
        migrations.AddField(
            model_name="track",
            name="mood",
            field=models.CharField(default="Oscuro", max_length=40),
        ),
        migrations.AddField(
            model_name="track",
            name="has_stems",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="track",
            name="has_wav",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="track",
            name="has_midi",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="track",
            name="allow_free_download",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="track",
            name="has_watermark",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="track",
            name="duration",
            field=models.PositiveIntegerField(default=30),
        ),
    ]
