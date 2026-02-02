#!/bin/bash
# ARSAKA_PUGUH - Frontend Deployment to VPS
# Run this from Windows PowerShell or Git Bash (NOT WSL)
# All credentials embedded - just run!

set -e

echo "=========================================="
echo "🚀 ARSAKA_PUGUH Frontend Deployment"
echo "=========================================="
echo ""

# VPS Configuration
VPS_IP="72.61.209.158"
VPS_USER="root"
VPS_PASS="Bait174663@vps"

echo "📦 Step 1: Creating source package..."
cd frontend
tar czf ../frontend-source.tar.gz \
    src public index.html \
    package.json package-lock.json \
    vite.config.ts tsconfig.json tsconfig.node.json \
    tailwind.config.js postcss.config.js \
    Dockerfile nginx.conf .env.production 2>/dev/null || tar czf ../frontend-source.tar.gz src public index.html package.json package-lock.json vite.config.ts tsconfig.json tsconfig.node.json tailwind.config.js postcss.config.js Dockerfile nginx.conf
cd ..
echo "✅ Package created: frontend-source.tar.gz"
echo ""

echo "🚀 Step 2: Uploading to VPS..."
sshpass -p "${VPS_PASS}" scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
    frontend-source.tar.gz ${VPS_USER}@${VPS_IP}:/root/signage/ || {
    echo "❌ Upload failed. Check network connection."
    exit 1
}
echo "✅ Source uploaded"

sshpass -p "${VPS_PASS}" scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
    nomad/frontend.nomad ${VPS_USER}@${VPS_IP}:/root/signage/nomad/ || {
    echo "❌ Nomad job upload failed"
    exit 1
}
echo "✅ Nomad job uploaded"
echo ""

echo "🐳 Step 3: Building Docker image on VPS..."
sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${VPS_USER}@${VPS_IP} << 'ENDSSH'
set -e
cd /root/signage

# Extract source
echo "Extracting source..."
rm -rf frontend-build
mkdir frontend-build
cd frontend-build
tar xzf ../frontend-source.tar.gz

# Build production bundle
echo "Installing dependencies..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm ci

echo "Building production bundle..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm run build

# Build Docker image
echo "Building Docker image..."
docker build -t arsaka-puguh-frontend:phase-a .

echo ""
echo "✅ Docker image built successfully:"
docker images | grep arsaka-puguh-frontend
ENDSSH
echo ""

echo "🎯 Step 4: Deploying to Nomad..."
sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/signage

echo "Running Nomad deployment..."
nomad job run nomad/frontend.nomad

echo ""
echo "Waiting for deployment to stabilize..."
sleep 5

echo ""
echo "Deployment status:"
nomad job status puguh-frontend
ENDSSH
echo ""

echo "🧹 Step 5: Cleanup..."
rm -f frontend-source.tar.gz
echo "✅ Local cleanup complete"
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Frontend deployed successfully!"
echo ""
echo "📍 Frontend URL:"
echo "   http://${VPS_IP}:3000/"
echo ""
echo "📊 Quick checks:"
echo "   Health: curl http://${VPS_IP}:3000/health"
echo "   Status: ssh root@${VPS_IP} 'nomad job status puguh-frontend'"
echo "   Logs:   ssh root@${VPS_IP} 'nomad logs -job puguh-frontend'"
echo ""
echo "🌐 Open in browser: http://${VPS_IP}:3000/"
echo ""
