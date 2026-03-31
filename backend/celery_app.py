from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analyze", "app.tasks.report"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_routes={
        "app.tasks.analyze.*": {"queue": "analysis"},
        "app.tasks.report.*": {"queue": "reports"},
    },
    task_annotations={
        "app.tasks.analyze.*": {"rate_limit": "10/m"},
        "app.tasks.report.*": {"rate_limit": "5/m"},
    },
)
