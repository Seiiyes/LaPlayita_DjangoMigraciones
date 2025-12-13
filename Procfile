web: cd la_playita_project && python manage.py collectstatic --noinput && gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:$PORT
release: cd la_playita_project && python manage.py migrate