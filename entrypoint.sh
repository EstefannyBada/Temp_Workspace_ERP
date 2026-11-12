#!/bin/sh
set -e

echo "==&gt; Ejecutando migraciones..."
python manage.py migrate --noinput

echo "==&gt; Recolectando archivos estaticos..."
python manage.py collectstatic --noinput

echo "==&gt; Iniciando servidor Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120