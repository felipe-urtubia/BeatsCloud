from django.db import migrations


def cargar_generos(apps, schema_editor):
    Genero = apps.get_model("app", "Genero_Musical")

    generos = [
        "Pop",
        "Rock",
        "Hip-Hop",
        "Electronica",
        "Reggaeton",
        "R&B",
        "Jazz",
        "Metal",
        "Soul",
    ]

    for nombre in generos:
        Genero.objects.using(
            schema_editor.connection.alias
        ).get_or_create(descripcion=nombre)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0027_track_r2_owner_user_id"),
    ]

    operations = [
        migrations.RunPython(
            cargar_generos,
            migrations.RunPython.noop,
        ),
    ]
