"""DDPB-70: filtros y ordenamiento del catalogo en PostgreSQL."""

from django.core.exceptions import ValidationError
from django.db.models import CharField, Count, Q
from django.db.models.functions import Cast, Lower

from .metadata_validation import validate_d9_field


PAGE_SIZES = (6, 12, 24)


def catalog_page_size(params):
    raw = params.get("page_size", "6")

    try:
        size = int(raw)
    except (ValueError, TypeError):
        raise ValidationError("Tamano de pagina invalido.")

    if size not in PAGE_SIZES:
        raise ValidationError(
            "El tamano de pagina debe ser 6, 12 o 24."
        )

    return size


def apply_catalog_filters(tracks, params):

    q = params.get("q", "").strip()

    if q:
        tracks = tracks.annotate(
            catalog_bpm_text=Cast(
                "bpm", output_field=CharField()
            )
        ).filter(
            Q(nombre_track__icontains=q)
            | Q(usuario__user__username__icontains=q)
            | Q(usuario__nombre_artistico__icontains=q)
            | Q(genero__descripcion__icontains=q)
            | Q(subgenre__icontains=q)
            | Q(scale_key__icontains=q)
            | Q(catalog_bpm_text__icontains=q)
        )

    genero = params.get("genero", "").strip()

    if genero:
        tracks = tracks.filter(
            genero__descripcion__iexact=genero
        )

    tipo = params.get("tipo", "").strip()

    if tipo:
        tipo = validate_d9_field("resource_type", tipo)
        tracks = tracks.filter(resource_type=tipo)

    mood = params.get("mood", "").strip()

    if mood:
        mood = validate_d9_field("mood", mood)
        tracks = tracks.filter(mood=mood)

    tonalidad = params.get("tonalidad", "").strip()

    if tonalidad:
        tracks = tracks.filter(scale_key=tonalidad)

    bpm_min = params.get("bpm_min", "").strip()
    bpm_max = params.get("bpm_max", "").strip()

    minimo = (
        validate_d9_field("bpm", bpm_min)
        if bpm_min else None
    )

    maximo = (
        validate_d9_field("bpm", bpm_max)
        if bpm_max else None
    )

    if (
        minimo is not None
        and maximo is not None
        and minimo > maximo
    ):
        raise ValidationError(
            "El BPM minimo no puede superar al maximo."
        )

    if minimo is not None:
        tracks = tracks.filter(bpm__gte=minimo)

    if maximo is not None:
        tracks = tracks.filter(bpm__lte=maximo)

    stems = params.get("has_stems", "").strip()

    if stems:
        tracks = tracks.filter(
            has_stems=validate_d9_field(
                "has_stems", stems
            )
        )

    precio = params.get("precio", "").strip()

    if precio == "free":
        tracks = tracks.filter(precio=0)

    elif precio == "paid":
        tracks = tracks.filter(precio__gt=0)

    elif precio == "0-5000":
        tracks = tracks.filter(
            precio__gte=0, precio__lte=5000
        )

    elif precio == "5001-10000":
        tracks = tracks.filter(
            precio__gte=5001, precio__lte=10000
        )

    elif precio == "10001-20000":
        tracks = tracks.filter(
            precio__gte=10001, precio__lte=20000
        )

    elif precio == "20001-mas":
        tracks = tracks.filter(precio__gte=20001)

    orden = params.get("orden", "recientes")

    order_map = {
        "recientes": ("-id_track",),
        "antiguos": ("id_track",),
        "precio_menor": ("precio", "id_track"),
        "precio_mayor": ("-precio", "id_track"),
        "bpm_asc": ("bpm", "id_track"),
        "bpm_desc": ("-bpm", "id_track"),
        "nombre": (Lower("nombre_track").asc(), "id_track"),
        "nombre_asc": (Lower("nombre_track").asc(), "id_track"),
        "nombre_desc": (Lower("nombre_track").desc(), "id_track"),
        "genero_asc": (
            Lower("genero__descripcion").asc(),
            Lower("nombre_track").asc(),
            "id_track",
        ),
        "genero_desc": (
            Lower("genero__descripcion").desc(),
            Lower("nombre_track").asc(),
            "id_track",
        ),
    }

    if orden == "likes":
        tracks = tracks.annotate(
            catalog_likes=Count(
                "usuarios_que_dieron_like",
                distinct=True,
            )
        )

        return tracks.order_by(
            "-catalog_likes", "id_track"
        )

    return tracks.order_by(
        *order_map.get(orden, ("-id_track",))
    )
