#!/usr/bin/env bash
# exit on error for compilation steps
set -o errexit

echo "📦 Installing Python Dependencies..."
python -m pip install -r requirements.txt

echo "🎨 Collecting Static Files..."
python manage.py collectstatic --no-input

echo "🚀 Running Database Migrations..."
# Run migrations with graceful fallback so build does not crash if DB connection is unavailable during build step
python manage.py makemigrations --no-input || echo "⚠️ Warning: makemigrations skipped during build"
python manage.py migrate --no-input || echo "⚠️ Warning: Database migration failed during build step. Please verify DATABASE_URL in Render environment variables."

echo "✅ Build completed successfully!"
