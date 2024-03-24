#! /usr/bin/env sh
set -e

########################
### run with uvicorn ###
########################
# exec uvicorn --reload --host 0.0.0.0 --port 80 --log-level info "app.main:app"

#########################
### run with gunicorn ###
#########################
export GUNICORN_CONF="/gunicorn_conf.py"
export WORKER_CLASS="uvicorn.workers.UvicornWorker"
export APP_MODULE="app.main:app"
exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" $APP_MODULE
