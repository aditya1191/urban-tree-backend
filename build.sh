#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# python manage.py collectstatic --no-input

python manage.py createsuperuser --username=admin --email=joyJoy_Winbourne@uml.edu --noinput

python manage.py migrate