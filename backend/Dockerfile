# ─────────────────────────────────────────────────────────────────────────────
# Ingrexa Backend — Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install all Python dependencies in an isolated layer.
#           This keeps the final image lean (avoids re-downloading on code change).
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# System packages needed to compile Python packages (psycopg2, pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first — lets Docker cache this layer separately.
# Only re-runs pip install when requirements.txt actually changes.
COPY requirements.txt .

# Install dependencies into a separate folder so we can copy them cleanly
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime — lean final image with only what we need to run the server
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Same system libs needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy the entire Django project
COPY . .

# Create non-root user for security (never run as root in production)
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Collect static files for WhiteNoise to serve
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Run production WSGI server (Gunicorn, not Django dev server)
# --workers: 4 workers to handle concurrent requests
# --timeout: 120 seconds for long AI analysis calls
CMD ["gunicorn", "foodview_api.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--log-level", "info"]
