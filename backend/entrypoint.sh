#!/bin/sh
# Entrypoint script for Django container

set -e

echo "Waiting for database..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "Database is ready!"

echo "Running migrations..."
python manage.py migrate --settings=app.settings.production

echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=app.settings.production

echo "Starting Gunicorn..."
exec gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  app.wsgi:application
