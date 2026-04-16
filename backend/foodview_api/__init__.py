# foodview_api/__init__.py
# Ensure the Celery app is loaded when Django starts so that @shared_task
# decorators in tasks.py are registered correctly.
from .celery import app as celery_app

__all__ = ("celery_app",)
