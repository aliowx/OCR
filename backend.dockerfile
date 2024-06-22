FROM dr2.parswitch.com/devops/python:3-12

WORKDIR /app/

ENV PYTHONPATH=/app
ENV C_FORCE_ROOT=1

COPY ./app/pyproject.toml ./app/poetry.lock* /app/

RUN useradd -m -d /home/dockeruser -s /bin/bash dockeruser && \
    chown -R dockeruser:dockeruser /app/ && \
    pip install poetry fastapi uvicorn gunicorn requests && \
    poetry config virtualenvs.create false && \
    poetry install

COPY ./gunicorn_conf.py ./scripts/start-server.sh  ./scripts/prestart.sh ./scripts/run.sh /
COPY ./app/worker-start.sh /worker-start.sh
COPY ./app .
COPY ./app/app/jobs/set_data_fake/* /


# Switch to the non-root user
USER dockeruser

CMD if [ "$BUILD_TYPE" = "backend" ]; then bash /run.sh; then python ./set_data_fake.py ; else bash /worker-start.sh; fi

