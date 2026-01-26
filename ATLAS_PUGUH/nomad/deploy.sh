#!/bin/bash
# ATLAS_PUGUH Phase A - Nomad Deployment Script
# Usage: ./deploy.sh [postgres|backend|all|status|logs|stop]

set -e  # Exit on error

NAMESPACE="puguh"
POSTGRES_JOB="puguh-postgres"
BACKEND_JOB="puguh-backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check nomad command exists
    if ! command -v nomad &> /dev/null; then
        log_error "Nomad not found. Please install Nomad first."
        exit 1
    fi

    # Check namespace exists
    if ! nomad namespace list | grep -q "^${NAMESPACE}"; then
        log_error "Namespace '${NAMESPACE}' not found."
        log_info "Create namespace with: nomad namespace apply -description 'PUGUH Control Plane' ${NAMESPACE}"
        exit 1
    fi

    log_info "Prerequisites OK"
}

deploy_postgres() {
    log_info "Deploying PostgreSQL database..."

    # Check if already running
    if nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB} &>/dev/null; then
        log_warn "PostgreSQL job already exists. Updating..."
    fi

    # Deploy
    nomad job run -namespace=${NAMESPACE} postgres.nomad

    log_info "Waiting for PostgreSQL to be healthy..."
    sleep 10

    # Wait for health check
    for i in {1..30}; do
        if nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB} | grep -q "running"; then
            log_info "PostgreSQL is running!"
            break
        fi
        echo -n "."
        sleep 2
    done

    echo ""

    # Show allocation info
    log_info "PostgreSQL allocation:"
    nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB}
}

run_migrations() {
    log_info "Running database migrations..."

    # Get PostgreSQL allocation ID
    ALLOC_ID=$(nomad job allocs -namespace=${NAMESPACE} ${POSTGRES_JOB} | awk 'NR==2{print $1}')

    if [ -z "$ALLOC_ID" ]; then
        log_error "Cannot find PostgreSQL allocation"
        exit 1
    fi

    log_info "PostgreSQL allocation: $ALLOC_ID"

    # TODO: Copy and run migration files
    # This requires:
    # 1. Migration files accessible on VPS
    # 2. Docker exec or nomad exec to run psql commands

    log_warn "⚠️  MANUAL STEP: Run migrations manually"
    log_warn "See NOMAD_DEPLOYMENT_PHASE_A.md - Step 3: Run Database Migrations"
    echo ""
    echo "Quick command:"
    echo "  docker ps | grep postgres"
    echo "  docker exec -i <container-id> psql -U atlas_user -d atlas_puguh < migrations/001_*.sql"
}

deploy_backend() {
    log_info "Deploying Backend API..."

    # Check PostgreSQL is running
    if ! nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB} | grep -q "running"; then
        log_error "PostgreSQL is not running. Deploy PostgreSQL first."
        exit 1
    fi

    # Check if already running
    if nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB} &>/dev/null; then
        log_warn "Backend job already exists. Updating..."
    fi

    # Deploy
    nomad job run -namespace=${NAMESPACE} backend-api.nomad

    log_info "Waiting for Backend API to be healthy..."
    sleep 10

    # Wait for health check
    for i in {1..30}; do
        if nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB} | grep -q "running"; then
            log_info "Backend API is running!"
            break
        fi
        echo -n "."
        sleep 2
    done

    echo ""

    # Show allocation info
    log_info "Backend API allocation:"
    nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB}

    # Test health endpoint
    sleep 5
    log_info "Testing health endpoint..."
    if curl -f http://127.0.0.1:8001/health &>/dev/null; then
        log_info "✓ Health check passed!"
        curl -s http://127.0.0.1:8001/health | jq '.'
    else
        log_warn "⚠️  Health check failed (might need to wait longer)"
    fi
}

show_status() {
    log_info "ATLAS_PUGUH Phase A - Deployment Status"
    echo ""

    # PostgreSQL status
    echo "=== PostgreSQL Database ==="
    if nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB} &>/dev/null; then
        nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB}
    else
        log_warn "Not deployed"
    fi
    echo ""

    # Backend API status
    echo "=== Backend API ==="
    if nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB} &>/dev/null; then
        nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB}
    else
        log_warn "Not deployed"
    fi
    echo ""

    # Consul services
    echo "=== Consul Services ==="
    consul catalog services | grep -E "puguh|postgres" || log_warn "No services registered"
    echo ""
}

show_logs() {
    local JOB_NAME=$1

    if [ -z "$JOB_NAME" ]; then
        log_error "Usage: $0 logs [postgres|backend]"
        exit 1
    fi

    case $JOB_NAME in
        postgres)
            FULL_JOB_NAME=${POSTGRES_JOB}
            TASK_NAME="postgresql"
            ;;
        backend)
            FULL_JOB_NAME=${BACKEND_JOB}
            TASK_NAME="fastapi"
            ;;
        *)
            log_error "Invalid job name: $JOB_NAME"
            exit 1
            ;;
    esac

    # Get allocation ID
    ALLOC_ID=$(nomad job allocs -namespace=${NAMESPACE} ${FULL_JOB_NAME} | awk 'NR==2{print $1}')

    if [ -z "$ALLOC_ID" ]; then
        log_error "Cannot find allocation for ${FULL_JOB_NAME}"
        exit 1
    fi

    log_info "Following logs for ${FULL_JOB_NAME} (${ALLOC_ID})..."
    log_info "Press Ctrl+C to stop"
    echo ""

    nomad alloc logs -namespace=${NAMESPACE} -f ${ALLOC_ID} ${TASK_NAME}
}

stop_services() {
    log_warn "Stopping all services..."

    # Stop backend first
    if nomad job status -namespace=${NAMESPACE} ${BACKEND_JOB} &>/dev/null; then
        log_info "Stopping Backend API..."
        nomad job stop -namespace=${NAMESPACE} ${BACKEND_JOB}
    fi

    # Stop PostgreSQL
    if nomad job status -namespace=${NAMESPACE} ${POSTGRES_JOB} &>/dev/null; then
        log_warn "Stopping PostgreSQL (data will persist)..."
        nomad job stop -namespace=${NAMESPACE} ${POSTGRES_JOB}
    fi

    log_info "All services stopped"
}

# Main script
case "${1:-}" in
    postgres)
        check_prerequisites
        deploy_postgres
        run_migrations
        ;;
    backend)
        check_prerequisites
        deploy_backend
        ;;
    all)
        check_prerequisites
        deploy_postgres
        run_migrations
        echo ""
        log_info "⏳ Waiting 30 seconds for PostgreSQL to stabilize..."
        sleep 30
        deploy_backend
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs $2
        ;;
    stop)
        stop_services
        ;;
    *)
        echo "ATLAS_PUGUH Phase A - Nomad Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  all          Deploy PostgreSQL + Backend API (recommended for first deploy)"
        echo "  postgres     Deploy PostgreSQL database only"
        echo "  backend      Deploy Backend API only"
        echo "  status       Show deployment status"
        echo "  logs [job]   Follow logs (postgres|backend)"
        echo "  stop         Stop all services"
        echo ""
        echo "Examples:"
        echo "  $0 all              # Deploy everything"
        echo "  $0 status           # Check status"
        echo "  $0 logs backend     # Follow backend logs"
        echo "  $0 stop             # Stop all services"
        exit 1
        ;;
esac
