#!/bin/bash
# ARSAKA_PUGUH - Deploy Frontend ke VPS
# Usage: ./deploy-frontend-vps.sh

set -e  # Exit on error

echo "=========================================="
echo "ARSAKA_PUGUH - Frontend Deployment to VPS"
echo "=========================================="
echo ""

# Configuration
VPS_IP="31.97.111.175"
VPS_USER="root"
IMAGE_NAME="arsaka-puguh-frontend"
IMAGE_TAG="phase-a"
NAMESPACE="puguh"

# Step 1: Build production bundle
echo "📦 Step 1: Building frontend production bundle..."
cd frontend
npm run build
echo "✅ Build complete!"
echo ""

# Step 2: Build Docker image
echo "🐳 Step 2: Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
echo "✅ Docker image built!"
echo ""

# Step 3: Save image as tar
echo "💾 Step 3: Saving Docker image..."
docker save ${IMAGE_NAME}:${IMAGE_TAG} | gzip > ../frontend-image.tar.gz
echo "✅ Image saved to frontend-image.tar.gz"
echo ""

# Step 4: Upload to VPS
echo "🚀 Step 4: Uploading image to VPS..."
scp ../frontend-image.tar.gz ${VPS_USER}@${VPS_IP}:/tmp/
echo "✅ Image uploaded!"
echo ""

# Step 5: Load image on VPS
echo "📥 Step 5: Loading image on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /tmp
docker load < frontend-image.tar.gz
rm frontend-image.tar.gz
echo "✅ Image loaded on VPS!"
ENDSSH
echo ""

# Step 6: Upload Nomad job
echo "📋 Step 6: Uploading Nomad job..."
cd ..
scp nomad/frontend.nomad ${VPS_USER}@${VPS_IP}:/tmp/
echo "✅ Nomad job uploaded!"
echo ""

# Step 7: Deploy to Nomad
echo "🎯 Step 7: Deploying to Nomad..."
ssh ${VPS_USER}@${VPS_IP} << ENDSSH
nomad job run -namespace=${NAMESPACE} /tmp/frontend.nomad
echo ""
echo "✅ Frontend deployed!"
echo ""
echo "Checking deployment status..."
sleep 5
nomad job status -namespace=${NAMESPACE} puguh-frontend
ENDSSH
echo ""

# Cleanup
echo "🧹 Cleaning up..."
rm -f frontend-image.tar.gz
echo "✅ Cleanup complete!"
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Frontend should be accessible at:"
echo "  http://${VPS_IP}:3000/"
echo ""
echo "To check status:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad job status -namespace=${NAMESPACE} puguh-frontend'"
echo ""
echo "To view logs:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad logs -namespace=${NAMESPACE} -job puguh-frontend'"
echo ""
