#!/bin/bash

/app/manage.py collectstatic --no-input
exec /app/manage.py runserver 0.0.0.0:8000 --insecure
