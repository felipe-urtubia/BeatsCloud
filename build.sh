#!/usr/bin/env bash

set -o errexit

# Instalar dependencias
python -m pip install -r requirements.txt

# Preparar archivos estaticos
python manage.py collectstatic --noinput

# Aplicar migraciones de la base de datos
python manage.py migrate --noinput