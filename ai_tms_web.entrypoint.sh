#!/usr/bin/env bash


# python manage.py collectstatic -v 2 --noinput
gunicorn -c gunicorn_config.py ai_tms.wsgi:application --timeout 300
