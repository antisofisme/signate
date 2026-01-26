#!/bin/bash
# ATLAS_PUGUH - Deploy Backend ke VPS
# Usage: ./deploy-backend-vps.sh

set -e  # Exit on error

echo "=========================================="
echo "ATLAS_PUGUH - Backend Deployment to VPS"
echo "=========================================="
echo ""

# Configuration
VPS_IP="31.97.111.175"
VPS_USER="root"
IMAGE_NAME="atlas-puguh-backend"
IMAGE_TAG="phase-a"
NAMESPACE="puguh"

# Step 1: Build Docker image
echo "🐳 Step 1: Building Backend Docker image..."
cd backend
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
echo "✅ Docker image built!"
echo ""

# Step 2: Save image as tar
echo "💾 Step 2: Saving Docker image..."
docker save ${IMAGE_NAME}:${IMAGE_TAG} | gzip > ../backend-image.tar.gz
echo "✅ Image saved to backend-image.tar.gz"
echo ""

# Step 3: Upload to VPS
echo "🚀 Step 3: Uploading image to VPS..."
scp ../backend-image.tar.gz ${VPS_USER}@${VPS_IP}:/tmp/
echo "✅ Image uploaded!"
echo ""

# Step 4: Load image on VPS
echo "📥 Step 4: Loading image on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /tmp
docker load < backend-image.tar.gz
rm backend-image.tar.gz
echo "✅ Image loaded on VPS!"
ENDSSH
echo ""

# Step 5: Upload updated Nomad job
echo "📋 Step 5: Uploading Nomad job..."
cd ..
scp nomad/backend-api.nomad ${VPS_USER}@${VPS_IP}:/tmp/
echo "✅ Nomad job uploaded!"
echo ""

# Step 6: Update Nomad job to use custom image
echo "🔧 Step 6: Updating Nomad job configuration..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
# Update backend-api.nomad to use custom image
sed -i 's|image = "python:3.11-slim"|image = "atlas-puguh-backend:phase-a"|' /tmp/backend-api.nomad
sed -i 's|command = "sh"|# command = "sh"|' /tmp/backend-api.nomad
sed -i 's|args = \[|# args = [|' /tmp/backend-api.nomad
sed -i '/^          "-c",$/,/^EOF$/s/^/# /' /tmp/backend-api.nomad
sed -i 's|^        \]$|# ]|' /tmp/backend-api.nomad
echo "✅ Nomad job updated to use custom image!"
ENDSSH
echo ""

# Step 7: Deploy to Nomad
echo "🎯 Step 7: Deploying to Nomad..."
ssh ${VPS_USER}@${VPS_IP} << ENDSSH
nomad job run -namespace=${NAMESPACE} /tmp/backend-api.nomad
echo ""
echo "✅ Backend deployed!"
echo ""
echo "Checking deployment status..."
sleep 5
nomad job status -namespace=${NAMESPACE} puguh-backend
ENDSSH
echo ""

# Cleanup
echo "🧹 Cleaning up..."
rm -f backend-image.tar.gz
echo "✅ Cleanup complete!"
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Backend should be accessible at:"
echo "  http://${VPS_IP}:25536/api/"
echo "  http://${VPS_IP}:25536/api/docs (Swagger UI)"
echo ""
echo "To check status:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad job status -namespace=${NAMESPACE} puguh-backend'"
echo ""
echo "To view logs:"
echo "  ssh ${VPS_USER}@${VPS_IP} 'nomad logs -namespace=${NAMESPACE} -job puguh-backend'"
echo ""
echo "To test Rules endpoint:"
echo "  curl http://${VPS_IP}:25536/api/rules"
echo ""
