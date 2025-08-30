#!/bin/bash

set -e

echo "📦 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn --log-level=debug restaurant_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
