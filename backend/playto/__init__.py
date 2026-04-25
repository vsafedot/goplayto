# Load the Celery app so @shared_task decorators register correctly
from .celery import app as celery_app  # noqa: F401

__all__ = ('celery_app',)
