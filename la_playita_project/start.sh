#!/bin/bash

echo "Starting La Playita application..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120