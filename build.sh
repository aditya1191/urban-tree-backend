#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

# uncomment the below line inorder to create a superuser and set password as env variable (one-time)
# python manage.py createsuperuser --username=admin --email=joyJoy_Winbourne@uml.edu --noinput

# uncomment the below line inorder to create tables in db (one-time)
# python manage.py migrate