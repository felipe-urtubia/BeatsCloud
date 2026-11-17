import re

from django.db import migrations, models


def backfill_r2_owner_user_id(apps, schema_editor):
    Track = apps.get_model("app", "Track")
    alias = schema_editor.connection.alias

    patron = re.compile(
        r"^private/([1-9][0-9]*)/(?:track|cover)/"
    )

    tracks = Track.objects.using(alias).only(
        "pk",
        "r2_object_key",
        "r2_cover_key",
        "r2_owner_user_id",
    )

    for track in tracks.iterator():
        propietarios = set()

        for clave in (
            track.r2_object_key,
            track.r2_cover_key,
        ):
            if not isinstance(clave, str):
                continue

            coincidencia = patron.match(clave)

            if coincidencia:
                propietarios.add(int(coincidencia.group(1)))

        if len(propietarios) > 1:
            raise RuntimeError(
                f"Track {track.pk}: las claves R2 tienen "
                "propietarios originales diferentes. "
                "Se requiere revision manual."
            )

        if propietarios:
            track.r2_owner_user_id = next(iter(propietarios))
            track.save(update_fields=["r2_owner_user_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0026_track_r2_cover_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="track",
            name="r2_owner_user_id",
            field=models.PositiveBigIntegerField(
                blank=True,
                editable=False,
                null=True,
            ),
        ),
        migrations.RunPython(
            backfill_r2_owner_user_id,
            migrations.RunPython.noop,
        ),
    ]
