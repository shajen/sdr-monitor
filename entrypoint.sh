#!/bin/bash

if [ "$1" ]; then
    MODE=$1
    if [ "$MODE" == "setup" ]; then
        export DJANGO_SUPERUSER_PASSWORD=${HTTP_PASSWORD:-password}
        /app/manage.py migrate
        /app/manage.py createsuperuser --noinput --username ${HTTP_USER:-admin} --email admin@local.local
        /app/manage.py collectstatic --no-input --clear
    elif [ "$MODE" == "server" ]; then
        /app/manage.py runserver 0.0.0.0:8000 --insecure
    elif [ "$MODE" == "worker" ]; then
        /app/manage.py runscript monitor_worker --script-args="--reader --cleaner --classifier --spectrograms_total_size_gb ${SPECTROGRAMS_TOTAL_SIZE_GB:-0} --transmissions_total_size_gb ${TRANSMISSIONS_TOTAL_SIZE_GB:-0}"
    else
        exec "$@"
    fi
else
    exec /bin/bash
fi
