#!/bin/bash
set -e

echo "=========================================="
echo "Smart TV Digital Signage - Backend API"
echo "=========================================="

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "✅ Redis is ready!"

# Run database migrations
echo ""
echo "🔄 Running database migrations..."
python scripts/run_migrations.py

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed"
else
    echo "⚠️ Migration warnings (continuing anyway...)"
fi

echo ""
echo "=========================================="

# Check if a command was provided
if [ $# -eq 0 ]; then
    echo "🚀 Starting Backend API Server..."
    echo "=========================================="
    # Start the FastAPI application (default)
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info
else
    # Execute the provided command (for celery-worker, celery-beat, etc.)
    echo "🚀 Executing command: $@"
    echo "=========================================="
    exec "$@"
fi
