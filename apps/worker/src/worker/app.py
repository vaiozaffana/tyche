from repo_queue import create_celery

from worker.settings import Settings

settings = Settings()
celery_app = create_celery(settings.redis_url, include=("worker.tasks",))
