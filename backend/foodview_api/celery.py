"""
foodview_api/celery.py
======================
Celery application entry-point for Ingrexa.

All heavy tasks (AI ingredient analysis, OCR, emails) are offloaded here so
that Django API views can return immediately and keep Gunicorn workers free.

Broker  : Redis  (CELERY_BROKER_URL in .env)
Backend : Redis  (CELERY_RESULT_BACKEND in .env)

Usage
-----
Start a worker locally:
    celery -A foodview_api worker --loglevel=info --concurrency=2

In Docker the worker is a separate service (see docker-compose.yml).
"""

import os
from celery import Celery

# Tell Celery which Django settings module to use.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodview_api.settings")

app = Celery("ingrexa")

# Pull all CELERY_* settings from Django settings (namespace="CELERY").
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in every INSTALLED_APP's tasks.py
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Utility task to sanity-check the Celery setup."""
    print(f"[CELERY] Request: {self.request!r}")
