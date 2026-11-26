from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "app",
            "0035_historialcompra_origen_adquisicion",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="cuenta_cerrada_en",
            field=models.DateTimeField(
                blank=True,
                editable=False,
                null=True,
            ),
        ),
    ]
