#!/bin/bash
# =============================================================================
# CELERY WORKER STARTUP SCRIPT
# =============================================================================
# Start Celery worker with proper configuration for video transcoding
# Usage: ./start_celery.sh [worker|beat|flower]
# =============================================================================

set -e

# Default to worker if no argument provided
MODE=${1:-worker}

# Set Python path
export PYTHONPATH="${PYTHONPATH}:/app"

# Worker configuration
WORKER_LOGLEVEL=${CELERY_LOGLEVEL:-info}
WORKER_CONCURRENCY=${CELERY_CONCURRENCY:-4}
WORKER_PREFETCH=${CELERY_PREFETCH_MULTIPLIER:-1}
WORKER_MAX_TASKS=${CELERY_MAX_TASKS_PER_CHILD:-10}

# Queue configuration
QUEUES=${CELERY_QUEUES:-default,transcoding,anthias}

echo "Starting Celery in ${MODE} mode..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Redis URL: ${REDIS_URL:-redis://redis:6379}"
echo "Log Level: ${WORKER_LOGLEVEL}"

case "$MODE" in
  worker)
    echo "Starting Celery Worker..."
    echo "Concurrency: ${WORKER_CONCURRENCY}"
    echo "Queues: ${QUEUES}"
    echo "Prefetch: ${WORKER_PREFETCH}"
    echo "Max tasks per child: ${WORKER_MAX_TASKS}"

    exec celery -A app.celery_app worker \
      --loglevel=${WORKER_LOGLEVEL} \
      --concurrency=${WORKER_CONCURRENCY} \
      --prefetch-multiplier=${WORKER_PREFETCH} \
      --max-tasks-per-child=${WORKER_MAX_TASKS} \
      --queues=${QUEUES} \
      --time-limit=7200 \
      --soft-time-limit=3600 \
      --pool=prefork \
      --without-gossip \
      --without-mingle \
      --without-heartbeat
    ;;

  beat)
    echo "Starting Celery Beat..."
    exec celery -A app.celery_app beat \
      --loglevel=${WORKER_LOGLEVEL} \
      --pidfile=/tmp/celerybeat.pid
    ;;

  flower)
    echo "Starting Flower (Celery Monitoring)..."
    FLOWER_PORT=${FLOWER_PORT:-5555}
    FLOWER_USER=${FLOWER_USER:-admin}
    FLOWER_PASSWORD=${FLOWER_PASSWORD:-admin123}

    echo "Flower URL: http://0.0.0.0:${FLOWER_PORT}"
    echo "Username: ${FLOWER_USER}"

    exec celery -A app.celery_app flower \
      --port=${FLOWER_PORT} \
      --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD} \
      --persistent=True \
      --db=/tmp/flower.db \
      --max_tasks=10000
    ;;

  *)
    echo "Invalid mode: $MODE"
    echo "Usage: $0 [worker|beat|flower]"
    exit 1
    ;;
esac