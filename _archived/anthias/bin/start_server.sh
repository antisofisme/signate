#!/bin/bash
# ============================================================================
# Anthias Storage Server Startup Script
# ============================================================================
# Starts the Django application using Gunicorn WSGI server
# Port: 8080 (configured in settings.py via LISTEN and PORT env vars)
# ============================================================================

set -e

echo "============================================================================"
echo "Starting Anthias Storage Server"
echo "============================================================================"

cd /usr/src/app

# Run Django migrations
echo "Running database migrations..."
python3 manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn WSGI server..."
exec python3 run_gunicorn.py
