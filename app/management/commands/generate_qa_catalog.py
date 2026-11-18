"""Create a deterministic, fully playable synthetic QA marketplace catalog."""

from __future__ import annotations

import random
from itertools import product
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from PIL import Image, ImageDraw, ImageFont

from app.audio_utils import generar_preview_audio
from app.models import (
    Genero_Musical,
    HistorialCompra,
    HistorialVenta,
    Track,
    Usuario,
    Venta,
)
from ._qa_safety import validate_local_database
from .prepare_demo_catalog import _make_demo_wav


CATALOG_MARKER = "qa-catalog:v1:"
ARTIST_USERNAME_PREFIX = "qa-cat-prod-"

ARTIST_NAMES = (
    ("Vela", "Cromática"), ("Cobre", "Errante"), ("Marea", "Vectorial"),
    ("Órbita", "Tibia"), ("Nébula", "Rítmica"), ("Lumen", "Boreal"),
    ("Ceniza", "Pixel"), ("Delta", "Tonal"), ("Norte", "Iridiscente"),
    ("Senda", "Lunar"), ("Azul", "Telúrico"), ("Páramo", "Sintético"),
)
ADJECTIVES = (
    "Ámbar", "Quieto", "Eléctrico", "Lunar", "Dorado", "Distante",
    "Tibio", "Cobalto", "Silente", "Violeta", "Inverso", "Flotante",
    "Nocturno", "Salino", "Suave", "Magnético", "Velado", "Abierto",
)
NOUNS = (
    "Pulso", "Jardín", "Satélite", "Pasaje", "Espejo", "Horizonte",
    "Andén", "Cristal", "Faro", "Cuaderno", "Rastro", "Prisma",
    "Cauce", "Umbral", "Vértice", "Brújula", "Eco", "Marea",
)
PLACES = (
    "la Azotea", "el Puerto", "la Avenida", "el Invernadero", "la Bahía",
    "el Pasillo", "la Estación", "el Observatorio", "la Costanera",
    "el Patio", "la Ventana", "el Planetario", "la Terminal", "el Taller",
)
WEATHER = ("la Lluvia", "el Viento", "la Niebla", "el Calor", "la Marea")

MOODS = (
    "Oscuro", "Enérgico", "Chill / Relax", "Triste / Nostálgico",
    "Bailable", "Agresivo",
)
SCALES = (
    "A Minor", "C Minor", "D Minor", "E Minor", "F Minor", "G Minor",
    "F# Minor", "G Major", "C Major", "F Major",
)
SCALE_ROOTS_HZ = {
    "A Minor": 55.0, "C Minor": 65.41, "D Minor": 73.42,
    "E Minor": 82.41, "F Minor": 87.31, "G Minor": 98.0,
    "F# Minor": 92.5, "G Major": 98.0, "C Major": 65.41,
    "F Major": 87.31,
}
RESOURCE_TYPES = ("instrumental", "acapella", "loop", "drumkit")
SUBGENRES = {
    "Hip-Hop": ("Lo-fi Rap", "Jazz Rap", "Underground", "Abstract"),
    "Rock": ("Indie Rock", "Alt Rock", "Post Rock", "Garage"),
    "Hip-Hop/rap": ("Lo-fi Rap", "Jazz Rap", "Underground", "Abstract"),
    "Electronica": ("Ambient", "Breakbeat", "Synthwave", "Downtempo"),
    "Reggaeton": ("Dembow", "Perreo", "Latin Club", "Romántico"),
    "R&B": ("Neo Soul", "Contemporary", "Alternative R&B", "Slow Jam"),
    "Jazz": ("Fusion", "Cool Jazz", "Nu Jazz", "Modal"),
    "Metal": ("Doom", "Post Metal", "Industrial", "Progressive"),
    "Soul": ("Neo Soul", "Vintage Soul", "Funk Soul", "Gospel Soul"),
    "Pop": ("Indie Pop", "Dream Pop", "Electro Pop", "Synth Pop"),
}


def _title_pool():
    titles = [f"{adjective} {noun} de {place}" for adjective, noun, place in product(ADJECTIVES, NOUNS, PLACES)]
    titles.extend(f"{noun} bajo {weather}" for noun, weather in product(NOUNS, WEATHER))
    titles.extend(f"{adjective} {noun}" for adjective, noun in product(ADJECTIVES, NOUNS))
    return titles


def _make_cover(seed: int, title: str) -> bytes:
    rng = random.Random(seed)
    palette = (
        (20, 29, 50), (53, 34, 73), (13, 78, 82), (105, 49, 44),
        (45, 57, 94), (85, 63, 31), (24, 73, 64), (73, 40, 63),
    )
    image = Image.new("RGB", (512, 512), palette[seed % len(palette)])
    draw = ImageDraw.Draw(image)
    accent = tuple(rng.randint(145, 245) for _ in range(3))
    for index in range(4):
        inset = 30 + index * 35
        draw.ellipse(
            (inset, inset, 512 - inset, 512 - inset),
            outline=accent,
            width=2 + (index % 2),
        )
    for index in range(8):
        x = rng.randrange(20, 490)
        y = rng.randrange(20, 490)
        radius = rng.randrange(3, 14)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent)
    draw.rectangle((22, 412, 490, 490), fill=(9, 13, 25))
    draw.text((38, 429), "BEATSCLOUD · QA AUDIO", fill=(246, 240, 222), font=ImageFont.load_default(size=22))
    draw.text((38, 462), title[:42], fill=accent, font=ImageFont.load_default(size=17))
    from io import BytesIO

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _safe_owned_media_name(name: str, media_root: Path):
    parts = Path(name).parts
    if "qa-catalog" not in parts:
        raise CommandError("Safety stop: generated media escaped the qa-catalog namespace.")
    path = Path(media_root, name).resolve()
    root = media_root.resolve()
    if not path.is_relative_to(root):
        raise CommandError("Safety stop: generated media path is outside MEDIA_ROOT.")
    return path


class Command(BaseCommand):
    help = "Create a deterministic playable synthetic catalog in the isolated QA database."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=120, help="Number of tracks (1–300).")
        parser.add_argument("--seed", type=int, default=20261118, help="Deterministic random seed.")
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete only records/media carrying this command's QA marker, then regenerate.",
        )

    def handle(self, *args, **options):
        validate_local_database(settings.DATABASES["default"])
        count = options["count"]
        seed = options["seed"]
        if not 1 <= count <= 300:
            raise CommandError("--count must be between 1 and 300.")
        if seed < 0:
            raise CommandError("--seed must be a non-negative integer.")

        rng = random.Random(seed)
        titles = _title_pool()
        if count > len(titles):
            raise CommandError(f"At most {len(titles)} unique generated titles are available.")
        rng.shuffle(titles)
        genres = [label for _, label in Genero_Musical.GENERO_CHOICES]
        if not genres:
            raise CommandError("No genres are configured in Genero_Musical.")

        media_root = Path(settings.MEDIA_ROOT).resolve()
        media_root.mkdir(parents=True, exist_ok=True)
        created_media = []

        if options["reset"]:
            with transaction.atomic():
                obsolete_media = self._remove_generated_records()
            # Database rows are committed before deleting files. A failed DB
            # transaction must never leave existing QA rows pointing at files
            # that this command already removed.
            for storage, name, path in obsolete_media:
                if path.is_file():
                    storage.delete(name)

        try:
            with transaction.atomic():
                producers = self._producers(seed)
                for index in range(count):
                    identifier = f"{CATALOG_MARKER}{seed}:{index:04d}"
                    existing = list(Track.objects.filter(original_filename=identifier))
                    if len(existing) > 1:
                        raise CommandError(f"Duplicate QA marker found: {identifier}")
                    if existing:
                        self._assert_complete(existing[0], media_root)
                        continue

                    local_rng = random.Random((seed << 16) + index)
                    title = titles[index]
                    genre_name = genres[index % len(genres)]
                    genre, _ = Genero_Musical.objects.get_or_create(descripcion=genre_name)
                    producer = producers[index % len(producers)]
                    bpm = 60 if index == 0 else 180 if index == 1 else max(61, min(179, round(local_rng.triangular(65, 178, 112))))
                    duration = (8, 12, 16)[index % 3]
                    scale = SCALES[index % len(SCALES)]
                    mood = MOODS[(index * 5 + seed) % len(MOODS)]
                    resource_type = RESOURCE_TYPES[(index + seed) % len(RESOURCE_TYPES)]
                    price = self._price(index, local_rng)
                    subgenre_choices = SUBGENRES.get(genre_name, ("Alternative", "Studio", "Modern"))
                    subgenre = subgenre_choices[(index + seed) % len(subgenre_choices)]
                    description = self._description(title, genre_name, subgenre, mood, local_rng)
                    style = (index + seed) % 4

                    track = Track(
                        nombre_track=title,
                        precio=price,
                        descripcion=description,
                        genero=genre,
                        usuario=producer,
                        subgenre=subgenre,
                        resource_type=resource_type,
                        bpm=bpm,
                        scale_key=scale,
                        mood=mood,
                        # Track has no local stems/MIDI file fields. Do not claim
                        # deliverables that are not present in the record.
                        has_stems=False,
                        has_wav=True,
                        has_midi=False,
                        allow_free_download=price == 0,
                        has_watermark=price > 0,
                        duration=duration,
                        original_filename=identifier,
                        storage_backend="local",
                        media_status="ready",
                    )
                    wav = _make_demo_wav(
                        bpm=bpm,
                        root_hz=SCALE_ROOTS_HZ[scale],
                        seed=(seed * 1009 + index * 37) % 2_147_483_647,
                        duration=duration,
                        style=style,
                    )
                    track.track.save(
                        f"qa-catalog/{identifier.replace(':', '_')}.wav",
                        ContentFile(wav),
                        save=False,
                    )
                    created_media.append(track.track.name)
                    track.foto.save(
                        f"qa-catalog/{identifier.replace(':', '_')}.png",
                        ContentFile(_make_cover(seed * 1009 + index, title)),
                        save=False,
                    )
                    created_media.append(track.foto.name)
                    track.save()
                    generar_preview_audio(track, namespace="qa-catalog")
                    created_media.append(track.preview.name)
                    self._add_synthetic_likes(track, producers, producer, local_rng)
                self._prepare_cart_fixture()

        except Exception:
            storage = Track._meta.get_field("track").storage
            cover_storage = Track._meta.get_field("foto").storage
            preview_storage = Track._meta.get_field("preview").storage
            field_storages = {
                "canciones": storage,
                "tracks": cover_storage,
                "previews": preview_storage,
            }
            for name in reversed(created_media):
                top = Path(name).parts[0] if Path(name).parts else ""
                file_storage = field_storages.get(top)
                if file_storage:
                    file_storage.delete(name)
            raise

        generated = Track.objects.filter(original_filename__startswith=CATALOG_MARKER).count()
        ready = Track.objects.filter(
            original_filename__startswith=CATALOG_MARKER,
            media_status="ready",
        ).exclude(track="").exclude(preview="").count()
        self.stdout.write(self.style.SUCCESS(
            f"QA catalog: {generated} tagged tracks in the database; {ready} have original audio and preview."
        ))
        self.stdout.write(f"Seed: {seed}; this run requested: {count}; genres available: {len(genres)}.")
        self.stdout.write("Tracks use synthetic local WAVs; they are not commercial compositions.")

    def _producers(self, seed):
        producers = []
        for index, (first, second) in enumerate(ARTIST_NAMES, start=1):
            username = f"{ARTIST_USERNAME_PREFIX}{index:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@beatcloud.local",
                    "is_active": True,
                    "first_name": first,
                    "last_name": second,
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            profile, _ = Usuario.objects.get_or_create(
                user=user,
                defaults={
                    "tipo_usu": Usuario.PRODUCTOR,
                    "nombre_artistico": f"{first} {second}",
                    "descripcion": (
                        f"Productor ficticio del catálogo QA. Explora texturas de estudio y "
                        f"arreglos originales de demostración ({seed % 997:03d})."
                    ),
                },
            )
            if profile.tipo_usu != Usuario.PRODUCTOR:
                profile.tipo_usu = Usuario.PRODUCTOR
                profile.save(update_fields=["tipo_usu"])
            producers.append(profile)
        return producers

    @staticmethod
    def _price(index, rng):
        bucket = index % 20
        if bucket == 0:
            return 0
        if bucket <= 3:
            return rng.randint(700, 5000)
        if bucket <= 7:
            return rng.randint(5001, 10000)
        if bucket <= 17:
            return rng.randint(10001, 20000)
        return rng.randint(20001, 45000)

    @staticmethod
    def _description(title, genre, subgenre, mood, rng):
        openings = (
            "Una producción original de demostración con espacio para una voz al frente.",
            "Batería marcada y capas armónicas pensadas para explorar distintos arreglos.",
            "Textura sintética creada localmente para comprobar el flujo de escucha y catálogo.",
            "Una maqueta instrumental ficticia con dinámica abierta y detalles de estudio.",
        )
        closings = (
            "Los archivos son material técnico de QA y no se ofrecen como licencias comerciales.",
            "Usa esta pista para revisar búsqueda, metadatos, portada y permisos de audio.",
            "La composición se generó por procedimiento y no utiliza samples de terceros.",
            "El clip acompaña pruebas locales de reproducción; no representa una obra terminada.",
        )
        return f"{rng.choice(openings)} {title} combina referencias de {genre} y {subgenre}; mood {mood.lower()}. {rng.choice(closings)}"

    @staticmethod
    def _add_synthetic_likes(track, producers, owner, rng):
        available = [profile for profile in producers if profile.pk != owner.pk]
        for profile in rng.sample(available, k=rng.randrange(0, min(4, len(available)) + 1)):
            profile.tracks_gustados.add(track)

    @staticmethod
    def _assert_complete(track, media_root):
        if track.storage_backend != "local" or track.media_status != "ready":
            raise CommandError(
                f"Existing generated track {track.pk} is not local/ready; use --reset to regenerate."
            )
        for field in (track.track, track.preview, track.foto):
            if not field or not field.name:
                raise CommandError(
                    f"Existing generated track {track.pk} lacks media; use --reset to regenerate."
                )
            path = _safe_owned_media_name(field.name, media_root)
            if not path.is_file():
                raise CommandError(
                    f"Existing generated media for track {track.pk} is missing; use --reset to regenerate."
                )

    def _remove_generated_records(self):
        media_root = Path(settings.MEDIA_ROOT).resolve()
        tracks = list(
            Track.objects.filter(original_filename__startswith=CATALOG_MARKER).select_related("usuario__user")
        )
        deletions = []
        for track in tracks:
            if not track.usuario.user.username.startswith(ARTIST_USERNAME_PREFIX):
                raise CommandError(
                    f"Safety stop: generated marker on track {track.pk} has a non-QA owner."
                )
            if track.storage_backend != "local":
                raise CommandError("Safety stop: reset refuses to delete non-local media.")
            for field in (track.track, track.preview, track.foto):
                if field and field.name:
                    path = _safe_owned_media_name(field.name, media_root)
                    deletions.append((field.storage, field.name, path))

        track_ids = [track.pk for track in tracks]
        if (
            Venta.objects.filter(track_id__in=track_ids, completada=True).exists()
            or HistorialVenta.objects.filter(track_id__in=track_ids).exists()
            or HistorialCompra.objects.filter(track_id__in=track_ids).exists()
        ):
            raise CommandError(
                "Reset is blocked because QA tracks have purchase history; use the isolated scripts/qa/reset.sh."
            )

        Venta.objects.filter(track_id__in=track_ids, completada=False).delete()
        Track.objects.filter(original_filename__startswith=CATALOG_MARKER).delete()
        self.stdout.write(f"Removed only {len(tracks)} command-tagged QA tracks and their namespaced media.")
        return deletions

    @staticmethod
    def _prepare_cart_fixture():
        user = User.objects.filter(username="qa-comprador-carrito").first()
        profile = Usuario.objects.filter(user=user).first() if user else None
        if profile is None:
            return
        paid_tracks = Track.objects.filter(
            original_filename__startswith=CATALOG_MARKER,
            precio__gt=0,
            media_status="ready",
        ).order_by("id_track")[:2]
        for track in paid_tracks:
            if Venta.objects.filter(
                usuario_id=profile, track=track, completada=False
            ).exists():
                continue
            iva = int(round(track.precio * 0.19))
            Venta.objects.create(
                detalle=track.nombre_track,
                fecha=timezone.localdate(),
                precio=track.precio,
                iva=iva,
                precio_total=track.precio + iva,
                usuario_id=profile,
                track=track,
                completada=False,
            )
