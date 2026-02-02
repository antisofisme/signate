#!/bin/bash
# Deploy User Approval Flow to MANTRA Backend
# Run this from your local machine with SSH access to VPS

VPS_HOST="31.97.111.175"
VPS_USER="yuda"
CONTAINER="mantra-backend"

echo "=== Deploying User Approval Flow to MANTRA Backend ==="

# Copy files to VPS
echo "1. Copying files to VPS..."
scp core/api/routes.py ${VPS_USER}@${VPS_HOST}:/tmp/routes.py
scp core/use_cases/enhanced_validation.py ${VPS_USER}@${VPS_HOST}:/tmp/enhanced_validation.py

# SSH into VPS and deploy
echo "2. Deploying to container..."
ssh ${VPS_USER}@${VPS_HOST} << 'EOF'
# Copy files into container
docker cp /tmp/routes.py mantra-backend:/app/core/api/routes.py
docker cp /tmp/enhanced_validation.py mantra-backend:/app/core/use_cases/enhanced_validation.py

# Restart container
docker restart mantra-backend

# Wait for startup
sleep 3

# Verify
curl -s http://localhost:8001/api/v1/health | head -c 100

echo ""
echo "=== Deployment Complete ==="
EOF

echo ""
echo "Test the new approve endpoint:"
echo "curl http://${VPS_HOST}:8002/api/v1/decisions/approve -X POST -H 'Content-Type: application/json' -d '{...}'"
