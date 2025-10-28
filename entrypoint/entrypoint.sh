#!/bin/bash

if [ $(id -u) = 0 ]; then
    chown ubuntu:ubuntu -R /app/
    exec runuser -u ubuntu -- /entrypoint/entrypoint_run.sh "$@"
else
    exec /entrypoint/entrypoint_run.sh "$@"
fi
