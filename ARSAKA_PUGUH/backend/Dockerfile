# ============================================================================
# ATLAS_PUGUH Phase A - Dockerfile
# ============================================================================
# Multi-stage build for minimal production image
# Target: VPS deployment via Nomad
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Builder
# ----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements-phase-a.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements-phase-a.txt

# ----------------------------------------------------------------------------
# Stage 2: Runtime
# ----------------------------------------------------------------------------
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash atlas && \
    mkdir -p /app && \
    chown -R atlas:atlas /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder --chown=atlas:atlas /root/.local /home/atlas/.local

# Copy application code
COPY --chown=atlas:atlas . .

# Set Python path
ENV PATH=/home/atlas/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER atlas

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "debug"]

# ============================================================================
# BUILD INSTRUCTIONS
# ============================================================================
#
# Build image:
#   docker build -t atlas-puguh-backend:phase-a .
#
# Run locally:
#   docker run -p 8001:8001 --env-file .env atlas-puguh-backend:phase-a
#
# Push to registry (for Nomad deployment):
#   docker tag atlas-puguh-backend:phase-a your-registry/atlas-puguh-backend:phase-a
#   docker push your-registry/atlas-puguh-backend:phase-a
#
# ============================================================================
# SECURITY NOTES
# ============================================================================
#
# - Runs as non-root user (atlas, UID 1000)
# - Multi-stage build (minimal attack surface)
# - No cache files (PYTHONDONTWRITEBYTECODE=1)
# - Health check enabled
# - Minimal base image (python:3.11-slim)
#
# ============================================================================
