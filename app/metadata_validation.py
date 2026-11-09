"""Validacion D9 compartida por formulario Django y API de edicion."""

from django.core.exceptions import ValidationError

RESOURCE_TYPES = frozenset({'instrumental', 'acapella', 'loop', 'drumkit'})
MOODS = frozenset({
    'Oscuro', 'Enérgico', 'Chill / Relax', 'Triste / Nostálgico',
    'Bailable', 'Agresivo',
})


def validate_d9_field(field, value):
    """Normaliza y valida un metadato. No consulta ni altera la base de datos."""
    if field == 'bpm':
        if isinstance(value, bool):
            raise ValidationError('BPM debe ser un número entero entre 1 y 300.')
        try:
            result = int(value)
        except (TypeError, ValueError, OverflowError):
            raise ValidationError('BPM debe ser un número entero entre 1 y 300.')
        if not 1 <= result <= 300:
            raise ValidationError('BPM debe estar entre 1 y 300.')
        return result

    if field == 'resource_type':
        if not isinstance(value, str) or value not in RESOURCE_TYPES:
            raise ValidationError('El tipo de recurso musical no es válido.')
        return value

    if field == 'mood':
        if not isinstance(value, str) or value not in MOODS:
            raise ValidationError('El estado de ánimo musical no es válido.')
        return value

    if field == 'has_stems':
        if value is None:
            return False  # Checkbox HTML no marcado.
        if isinstance(value, bool):
            return value
        if type(value) is int and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ('true', '1', 'on'):
                return True
            if normalized in ('false', '0', 'off', ''):
                return False
        raise ValidationError('has_stems solo admite true/false, 1/0 u on/off.')

    raise ValueError('Campo D9 desconocido: ' + str(field))
