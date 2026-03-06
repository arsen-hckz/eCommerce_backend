web: gunicorn core.wsgi --log-file -
web: python manage.py migrate && gunicorn core.wsgi --bind 0.0.0.0:8080 --log-file -