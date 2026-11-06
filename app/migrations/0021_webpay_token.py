from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0020_webpay_order_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="webpaytransaction",
            name="webpay_token",
            field=models.CharField(
                max_length=255,
                unique=True,
                null=True,
                blank=True,
                editable=False,
            ),
        ),
    ]
