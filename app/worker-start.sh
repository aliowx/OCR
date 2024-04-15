#! /usr/bin/env bash
set -e

python /home/amir/projects/parking_backend/app/app/jobs/celery/celeryworker_pre_start.py

celery -A app.celery.worker worker --loglevel=INFO -Q main-queue
