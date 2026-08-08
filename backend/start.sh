#!/usr/bin/env bash

echo "🚀 Starting Ingrexa Backend..."

# Run migrations gracefully on startup (will not prevent Gunicorn from launching if DB is temporary down or updating)
python manage.py migrate --no-input || echo "⚠️ Warning: Database migration skipped on startup. Proceeding to launch WSGI server..."

# Launch Gunicorn server
echo "🌐 Starting Gunicorn WSGI Server..."
exec gunicorn foodview_api.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --timeout 120
