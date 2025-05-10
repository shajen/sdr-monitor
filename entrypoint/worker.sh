#!/bin/bash

exec /app/manage.py runscript monitor_worker --script-args="--reader --cleaner --classifier --spectrograms_total_size_gb ${SPECTROGRAMS_TOTAL_SIZE_GB:-0} --transmissions_total_size_gb ${TRANSMISSIONS_TOTAL_SIZE_GB:-0}"
