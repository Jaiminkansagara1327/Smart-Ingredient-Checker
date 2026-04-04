"""
WSGI config for foodview_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodview_api.settings')

# Automatic Runtime Migrations for Render
try:
    import django
    django.setup()
    print("🚀 Auto-syncing Database Migrations...")
    call_command('migrate', '--noinput')
except Exception as e:
    print(f"⚠️ Startup Migration Failed: {e}")

application = get_wsgi_application()
