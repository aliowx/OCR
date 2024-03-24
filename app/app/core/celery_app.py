from celery import Celery

from app.core.config import settings

celery_app = Celery("worker", backend="rpc://", broker=str(settings.REDIS_URI))

celery_app.conf.task_routes = {"app.celery.worker.test_celery": "main-queue"}
celery_app.conf.update(task_track_started=True)
