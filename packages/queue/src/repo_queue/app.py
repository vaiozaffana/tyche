from collections.abc import Sequence

from celery import Celery


def create_celery(redis_url: str, *, include: Sequence[str] = ()) -> Celery:
    app = Celery(
        "tyche",
        broker=redis_url,
        backend=redis_url,
        include=list(include),
    )
    app.conf.update(
        accept_content=["json"],
        broker_connection_retry_on_startup=True,
        result_serializer="json",
        task_serializer="json",
        timezone="UTC",
    )
    return app
