"""Prepare an isolated, local BeatsCloud catalog for a live demonstration."""

from __future__ import annotations

import math
import random
import secrets
import wave
from array import array
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from app.audio_utils import generar_preview_audio
from app.models import Genero_Musical, Track, Usuario
from ._qa_safety import validate_local_database


DEMO_USERNAME = "demo-productor"
TRACKS = (
    {
        "title": "DEMO · Pulso Nocturno",
        "genre": "Hip-Hop",
        "price": 12000,
        "bpm": 92,
        "scale": "Am",
        "mood": "Oscuro",
        "seed": 11,
        "root": 55.0,
    },
    {
        "title": "DEMO · Costa Eléctrica",
        "genre": "Electronica",
        "price": 16500,
        "bpm": 118,
        "scale": "F#m",
        "mood": "Enérgico",
        "seed": 23,
        "root": 46.25,
    },
    {
        "title": "DEMO · Brisa de Vinilo",
        "genre": "R&B",
        "price": 9000,
        "bpm": 84,
        "scale": "Dm",
        "mood": "Chill / Relax",
        "seed": 37,
        "root": 73.42,
    },
    {
        "title": "DEMO · Avenida de Medianoche",
        "genre": "Reggaeton",
        "price": 14000,
        "bpm": 100,
        "scale": "Gm",
        "mood": "Bailable",
        "seed": 49,
        "root": 49.0,
    },
    {
        "title": "DEMO · Lluvia en la Ventana",
        "genre": "Jazz",
        "price": 7500,
        "bpm": 76,
        "scale": "Cm",
        "mood": "Triste / Nostálgico",
        "seed": 61,
        "root": 65.41,
    },
)


def _make_demo_wav(
    *, bpm: int, root_hz: float, seed: int, duration: int = 12, style: int = 0
) -> bytes:
    """Synthesize a short original drum-and-bass loop using Python stdlib."""
    sample_rate = 22050
    frame_count = sample_rate * duration
    beat_seconds = 60 / bpm
    rng = random.Random(seed)
    samples = array("h")
    kick_patterns = ((0, 2), (0, 3), (0,), (0, 2, 3))
    snare_patterns = ((1, 3), (1,), (2,), (1, 3))
    chord_shapes = ((1.0, 1.25, 1.5), (1.0, 1.2, 1.5), (1.0, 4 / 3, 1.5), (1.0, 1.5, 2.0))
    kick_pattern = kick_patterns[style % len(kick_patterns)]
    snare_pattern = snare_patterns[style % len(snare_patterns)]
    chord = chord_shapes[style % len(chord_shapes)]

    for frame in range(frame_count):
        t = frame / sample_rate
        beat_position = t / beat_seconds
        beat_index = int(beat_position)
        beat_phase = (beat_position - beat_index) * beat_seconds
        eighth_position = beat_position * 2
        eighth_index = int(eighth_position)
        eighth_phase = (eighth_position - eighth_index) * beat_seconds / 2

        kick = 0.0
        if beat_index % 4 in kick_pattern:
            kick = math.sin(2 * math.pi * (48 + 95 * math.exp(-beat_phase * 24)) * beat_phase)
            kick *= 0.66 * math.exp(-beat_phase * 15)

        snare = 0.0
        if beat_index % 4 in snare_pattern:
            snare = rng.uniform(-1, 1) * 0.19 * math.exp(-beat_phase * 21)

        hat = rng.uniform(-1, 1) * 0.045 * math.exp(-eighth_phase * 95)
        bar_phase = (t % (beat_seconds * 4)) / (beat_seconds * 4)
        pad = (
            math.sin(2 * math.pi * root_hz * t)
            + 0.55 * math.sin(2 * math.pi * root_hz * chord[1] * t)
            + 0.35 * math.sin(2 * math.pi * root_hz * chord[2] * t)
        ) * (0.075 + 0.025 * math.sin(math.pi * bar_phase))
        bass = math.sin(2 * math.pi * root_hz * 0.5 * t) * 0.16

        value = max(-0.92, min(0.92, kick + snare + hat + pad + bass))
        samples.append(int(value * 32767))

    if samples.itemsize != 2:
        samples.byteswap()
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())
    return output.getvalue()


def _make_demo_cover(seed: int) -> bytes:
    colors = ((16, 24, 48), (49, 23, 67), (8, 72, 78), (93, 39, 38), (48, 47, 87))
    base = colors[seed % len(colors)]
    image = Image.new("RGB", (512, 512), base)
    draw = ImageDraw.Draw(image)
    draw.ellipse((90, 70, 430, 410), outline=(125, 234, 220), width=5)
    draw.ellipse((145, 125, 375, 355), outline=(241, 189, 93), width=3)
    draw.line((64, 430, 448, 430), fill=(241, 189, 93), width=4)
    draw.text((64, 452), "BEATSCLOUD · DEMO", fill="white", font=ImageFont.load_default(size=24))
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


class Command(BaseCommand):
    help = "Create an idempotent, local-only catalog with original demo audio."

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]
        validate_local_database(
            database, prefixes=("beatscloud_demo_", "beatscloud_qa_")
        )

        genres = {label for _, label in Genero_Musical.GENERO_CHOICES}
        tracks_by_genre = {item["genre"] for item in TRACKS}
        missing_genres = tracks_by_genre - genres
        if missing_genres:
            raise CommandError(
                "Demo genres are not configured in Genero_Musical: "
                + ", ".join(sorted(missing_genres))
            )

        created_password = None
        with transaction.atomic():
            user = User.objects.filter(username=DEMO_USERNAME).first()
            if user is None:
                created_password = secrets.token_urlsafe(24)
                user = User.objects.create_user(
                    username=DEMO_USERNAME,
                    email="demo-productor@beatcloud.local",
                    password=created_password,
                    is_active=True,
                    first_name="Productor",
                    last_name="Demo",
                )
            profile, _ = Usuario.objects.get_or_create(
                user=user,
                defaults={
                    "tipo_usu": Usuario.PRODUCTOR,
                    "nombre_artistico": "BeatCloud Demo",
                    "descripcion": "Perfil y pistas originales para demostración académica.",
                },
            )
            changed_fields = []
            if profile.tipo_usu != Usuario.PRODUCTOR:
                profile.tipo_usu = Usuario.PRODUCTOR
                changed_fields.append("tipo_usu")
            if profile.nombre_artistico != "BeatCloud Demo":
                profile.nombre_artistico = "BeatCloud Demo"
                changed_fields.append("nombre_artistico")
            if changed_fields:
                profile.save(update_fields=changed_fields)

            for _, label in Genero_Musical.GENERO_CHOICES:
                Genero_Musical.objects.get_or_create(descripcion=label)

            for item in TRACKS:
                track, created = Track.objects.get_or_create(
                    nombre_track=item["title"],
                    defaults={
                        "precio": item["price"],
                        "descripcion": (
                            "Instrumental sintético original generado para la "
                            "demostración académica de BeatsCloud. No es una licencia comercial."
                        ),
                        "genero": Genero_Musical.objects.get(descripcion=item["genre"]),
                        "usuario": profile,
                        "subgenre": "Demo original",
                        "resource_type": "instrumental",
                        "bpm": item["bpm"],
                        "scale_key": item["scale"],
                        "mood": item["mood"],
                        "has_stems": False,
                        "has_wav": True,
                        "has_midi": False,
                        "has_watermark": True,
                        "duration": 12,
                        "storage_backend": "local",
                        "media_status": "ready",
                    },
                )
                if track.track:
                    if not track.preview:
                        generar_preview_audio(track)
                    continue

                if not created:
                    track.precio = item["price"]
                    track.genero = Genero_Musical.objects.get(descripcion=item["genre"])
                    track.usuario = profile
                    track.bpm = item["bpm"]
                    track.scale_key = item["scale"]
                    track.mood = item["mood"]
                    track.storage_backend = "local"
                    track.media_status = "ready"

                track.track.save(
                    f"demo_{item['seed']}.wav",
                    ContentFile(_make_demo_wav(bpm=item["bpm"], root_hz=item["root"], seed=item["seed"])),
                    save=False,
                )
                track.foto.save(
                    f"demo_cover_{item['seed']}.png",
                    ContentFile(_make_demo_cover(item["seed"])),
                    save=False,
                )
                track.original_filename = f"DEMO_{item['seed']}.wav"
                track.save()
                if not track.preview:
                    generar_preview_audio(track)

        total = Track.objects.filter(nombre_track__startswith="DEMO ·").count()
        ready = Track.objects.filter(
            nombre_track__startswith="DEMO ·",
            usuario=profile,
            media_status="ready",
        ).exclude(track="").exclude(preview="").count()
        if total != len(TRACKS) or ready != len(TRACKS):
            raise CommandError(
                f"Demo catalog incomplete: {ready}/{len(TRACKS)} tracks have original and preview audio."
            )

        self.stdout.write(self.style.SUCCESS(f"Ready demo tracks: {ready}"))
        self.stdout.write(f"Producer username: {user.username}")
        if created_password:
            self.stdout.write(f"Temporary password (shown once): {created_password}")
        else:
            self.stdout.write("Existing demo account preserved; password was not changed.")
