#!/bin/bash
# ARSAKA_PUGUH - Deploy Frontend ke VPS (Build di Server)
# Usage: ./deploy-frontend-direct.sh

set -e

echo "=========================================="
echo "ARSAKA_PUGUH - Frontend Deployment to VPS"
echo "Deploy Mode: Build on Server"
echo "=========================================="
echo ""

VPS_IP="31.97.111.175"
VPS_USER="root"
REMOTE_DIR="/opt/arsaka-puguh"

echo "📦 Step 1: Preparing files..."
echo "Creating deployment package..."

# Create temporary directory
mkdir -p /tmp/frontend-deploy
cd frontend

# Copy necessary files
cp -r src public index.html package.json package-lock.json \
      vite.config.ts tsconfig.json tsconfig.node.json \
      tailwind.config.js postcss.config.js \
      Dockerfile nginx.conf .env.production \
      /tmp/frontend-deploy/

echo "✅ Files prepared"
echo ""

echo "🚀 Step 2: Uploading to VPS..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${REMOTE_DIR}/frontend"
scp -r /tmp/frontend-deploy/* ${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/frontend/
echo "✅ Files uploaded"
echo ""

echo "🐳 Step 3: Building Docker image on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /opt/arsaka-puguh/frontend

echo "Installing dependencies..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm ci

echo "Building production bundle..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm run build

echo "Building Docker image..."
docker build -t arsaka-puguh-frontend:phase-a .

echo "✅ Docker image built successfully"
docker images | grep arsaka-puguh-frontend
ENDSSH
echo ""

echo "📋 Step 4: Uploading Nomad job..."
cd ..
scp nomad/frontend.nomad ${VPS_USER}@${VPS_IP}:/tmp/
echo "✅ Nomad job uploaded"
echo ""

echo "🎯 Step 5: Deploying to Nomad..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
nomad job run -namespace=puguh /tmp/frontend.nomad

echo ""
echo "Waiting for deployment..."
sleep 5

echo "Checking status..."
nomad job status -namespace=puguh puguh-frontend
ENDSSH
echo ""

echo "🧹 Cleanup..."
rm -rf /tmp/frontend-deploy
echo "✅ Cleanup complete"
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Frontend accessible at:"
echo "  http://${VPS_IP}:3000/"
echo ""
echo "To check status:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad job status -namespace=puguh puguh-frontend'"
echo ""
echo "To view logs:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad logs -namespace=puguh -job puguh-frontend'"
echo ""
