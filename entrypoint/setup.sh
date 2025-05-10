#!/bin/bash

export DJANGO_SUPERUSER_PASSWORD=${HTTP_PASSWORD:-password}

/app/manage.py migrate
/app/manage.py createsuperuser --noinput --username ${HTTP_USER:-admin} --email admin@local.local &> /dev/null || true
