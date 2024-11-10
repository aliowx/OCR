#! /usr/bin/env bash
set -e

python /app/app/jobs/celery/celeryworker_pre_start.py

celery -A app.jobs.celery.worker worker --loglevel=INFO -B
