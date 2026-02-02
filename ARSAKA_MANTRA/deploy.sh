#!/bin/bash
# ARSAKA_MANTRA Deployment Script
# Deploy backend and frontend to VPS

set -e

VPS_HOST="31.97.111.175"
VPS_USER="yuda"
BACKEND_DIR="ARSAKA_MANTRA/backend"
FRONTEND_DIR="ARSAKA_MANTRA/frontend"

echo "============================================"
echo "ARSAKA_MANTRA Deployment"
echo "============================================"
echo "Target: $VPS_USER@$VPS_HOST"
echo ""

# Check what to deploy
echo "Files to deploy:"
echo ""

# Backend files (AI Arbiter + Enhanced Validation)
echo "Backend:"
echo "  - core/use_cases/ai_arbiter/ (AI client, arbiters)"
echo "  - core/use_cases/enhanced_validation.py"
echo "  - core/api/routes.py"
echo ""

# Frontend files
echo "Frontend:"
echo "  - src/pages/Validator.tsx"
echo "  - src/pages/settings/AISettings.tsx"
echo "  - src/shared/api.ts"
echo "  - src/shared/constants.ts"
echo "  - src/components/layout/SidebarLayout.tsx"
echo "  - src/App.tsx"
echo ""

# Create archive
echo "Creating deployment archive..."
DEPLOY_DIR="/tmp/mantra_deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR/backend"
mkdir -p "$DEPLOY_DIR/frontend"

# Backend files
cp -r "$(dirname "$0")/backend/core/use_cases/ai_arbiter" "$DEPLOY_DIR/backend/"
cp "$(dirname "$0")/backend/core/use_cases/enhanced_validation.py" "$DEPLOY_DIR/backend/"
cp "$(dirname "$0")/backend/core/api/routes.py" "$DEPLOY_DIR/backend/"

# Frontend files
mkdir -p "$DEPLOY_DIR/frontend/src/pages/settings"
mkdir -p "$DEPLOY_DIR/frontend/src/shared"
mkdir -p "$DEPLOY_DIR/frontend/src/components/layout"
cp "$(dirname "$0")/frontend/src/pages/Validator.tsx" "$DEPLOY_DIR/frontend/src/pages/"
cp "$(dirname "$0")/frontend/src/pages/settings/AISettings.tsx" "$DEPLOY_DIR/frontend/src/pages/settings/"
cp "$(dirname "$0")/frontend/src/shared/api.ts" "$DEPLOY_DIR/frontend/src/shared/"
cp "$(dirname "$0")/frontend/src/shared/constants.ts" "$DEPLOY_DIR/frontend/src/shared/"
cp "$(dirname "$0")/frontend/src/components/layout/SidebarLayout.tsx" "$DEPLOY_DIR/frontend/src/components/layout/"
cp "$(dirname "$0")/frontend/src/App.tsx" "$DEPLOY_DIR/frontend/src/"

# Create tarball
cd /tmp
tar -czf mantra_deploy.tar.gz -C "$DEPLOY_DIR" .

echo "Archive created: /tmp/mantra_deploy.tar.gz"
echo ""

echo "============================================"
echo "Deployment Instructions"
echo "============================================"
echo ""
echo "1. Copy archive to VPS:"
echo "   scp /tmp/mantra_deploy.tar.gz $VPS_USER@$VPS_HOST:/tmp/"
echo ""
echo "2. SSH to VPS and extract:"
echo "   ssh $VPS_USER@$VPS_HOST"
echo "   cd /tmp && tar -xzf mantra_deploy.tar.gz"
echo ""
echo "3. Deploy backend:"
echo "   docker cp /tmp/backend/ai_arbiter mantra-backend:/app/core/use_cases/"
echo "   docker cp /tmp/backend/enhanced_validation.py mantra-backend:/app/core/use_cases/"
echo "   docker cp /tmp/backend/routes.py mantra-backend:/app/core/api/"
echo ""
echo "4. Set AI provider (optional):"
echo "   docker exec mantra-backend sh -c 'echo \"AI_PROVIDER=groq\" >> /app/.env'"
echo "   docker exec mantra-backend sh -c 'echo \"GROQ_API_KEY=gsk_xxx\" >> /app/.env'"
echo ""
echo "5. Restart backend:"
echo "   docker restart mantra-backend"
echo ""
echo "6. Deploy frontend (rebuild):"
echo "   cd /opt/mantra/frontend"
echo "   cp -r /tmp/frontend/src/* src/"
echo "   bun run build"
echo "   docker restart mantra-frontend"
echo ""
echo "7. Verify:"
echo "   curl http://$VPS_HOST:8002/api/v1/ai/providers"
echo "   curl http://$VPS_HOST:8002/health"
echo ""
echo "============================================"
