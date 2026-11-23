MAX_PLAN_PRICE = 99_999_999

DURATION_LIMITS = {"meses": 12, "anios": 5}


def validate_plan_duration(cantidad, unidad):
    if not isinstance(unidad, str) or unidad not in DURATION_LIMITS:
        raise ValueError("Selecciona meses o anios.")

    if type(cantidad) is not int or not 1 <= cantidad <= DURATION_LIMITS[unidad]:
        raise ValueError("Selecciona una duracion valida.")



def validate_subscription_plan(data, partial=False):
    if not isinstance(data, dict) or not data:
        raise ValueError("Ingresa los datos del plan.")

    campos = {
        "detalle",
        "precio",
        "descripcion",
        "beneficios",
        "activo",
        "duracion_cantidad",
        "duracion_unidad",
    }

    if set(data) - campos:
        raise ValueError("El plan contiene campos no permitidos.")

    valores = {}

    if not partial or "detalle" in data:
        detalle = data.get("detalle")

        if not isinstance(detalle, str):
            raise ValueError("Ingresa un nombre válido.")

        detalle = detalle.strip()

        if not detalle or len(detalle) > 200:
            raise ValueError("El nombre debe tener entre 1 y 200 caracteres.")

        valores["detalle"] = detalle

    if not partial or "precio" in data:
        precio = data.get("precio")

        if (
            isinstance(precio, str)
            and precio.isascii()
            and precio.isdigit()
            and len(precio) <= 8
        ):
            precio = int(precio)

        if type(precio) is not int or not 1 <= precio <= MAX_PLAN_PRICE:
            raise ValueError("Ingresa un precio entero válido en CLP.")

        valores["precio"] = precio

    if "descripcion" in data:
        descripcion = data["descripcion"]

        if not isinstance(descripcion, str) or len(descripcion.strip()) > 1000:
            raise ValueError("La descripción admite hasta 1000 caracteres.")

        valores["descripcion"] = descripcion.strip()

    if "beneficios" in data:
        beneficios = data["beneficios"]

        if not isinstance(beneficios, list) or len(beneficios) > 10:
            raise ValueError("Puedes agregar hasta 10 beneficios.")

        limpios = []

        for beneficio in beneficios:
            if not isinstance(beneficio, str):
                raise ValueError("Cada beneficio debe ser un texto.")

            beneficio = beneficio.strip()

            if not beneficio or len(beneficio) > 200:
                raise ValueError("Cada beneficio admite entre 1 y 200 caracteres.")

            if beneficio not in limpios:
                limpios.append(beneficio)

        valores["beneficios"] = limpios

    if "activo" in data:
        if type(data["activo"]) is not bool:
            raise ValueError("El estado del plan no es válido.")

        valores["activo"] = data["activo"]

    campos_duracion = {
        "duracion_cantidad",
        "duracion_unidad",
    }

    if not partial or campos_duracion.intersection(data):
        if partial and not campos_duracion.issubset(data):
            raise ValueError("Indica cantidad y unidad de duracion.")

        cantidad = data.get("duracion_cantidad", 1)
        unidad = data.get("duracion_unidad", "meses")

        validate_plan_duration(cantidad, unidad)

        valores["duracion_cantidad"] = cantidad
        valores["duracion_unidad"] = unidad

    return valores
