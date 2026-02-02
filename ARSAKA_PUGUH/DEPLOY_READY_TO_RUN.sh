#!/bin/bash
# ARSAKA_PUGUH - Frontend Deployment (Ready to Run)
# Run this from Windows PowerShell or Git Bash (NOT WSL)

set -e

echo "=========================================="
echo "ARSAKA_PUGUH - Frontend Deployment"
echo "=========================================="
echo ""

VPS_IP="72.61.209.158"
VPS_USER="root"
VPS_PASS='1(;2-Ur?F)PP73J#G-wW'

echo "📦 Step 1: Creating tarball..."
cd frontend
tar czf ../frontend-source.tar.gz \
    src public index.html \
    package.json package-lock.json \
    vite.config.ts tsconfig.json tsconfig.node.json \
    tailwind.config.js postcss.config.js \
    Dockerfile nginx.conf .env.production
cd ..
echo "✅ Tarball created"
echo ""

echo "🚀 Step 2: Uploading to VPS..."
sshpass -p "${VPS_PASS}" scp -o StrictHostKeyChecking=no \
    frontend-source.tar.gz ${VPS_USER}@${VPS_IP}:/root/signage/
sshpass -p "${VPS_PASS}" scp -o StrictHostKeyChecking=no \
    nomad/frontend.nomad ${VPS_USER}@${VPS_IP}:/root/signage/nomad/
echo "✅ Files uploaded"
echo ""

echo "🐳 Step 3: Building on VPS..."
sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/signage
rm -rf frontend-build
mkdir frontend-build
cd frontend-build
tar xzf ../frontend-source.tar.gz

echo "Installing dependencies..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine sh -c "npm ci && npm run build"

echo "Building Docker image..."
docker build -t arsaka-puguh-frontend:phase-a .

echo "✅ Image built"
docker images | grep arsaka-puguh-frontend
ENDSSH
echo ""

echo "🎯 Step 4: Deploying to Nomad..."
sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/signage
nomad job run nomad/frontend.nomad

echo ""
echo "Waiting for deployment..."
sleep 5

nomad job status puguh-frontend
ENDSSH
echo ""

echo "🧹 Step 5: Cleanup..."
rm -f frontend-source.tar.gz
echo "✅ Done"
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Frontend accessible at:"
echo "  http://${VPS_IP}:3000/"
echo ""
