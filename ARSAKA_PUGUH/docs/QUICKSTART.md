# ARSAKA_PUGUH Quick Start Guide

Get up and running with ARSAKA_PUGUH in 5 minutes.

## Prerequisites

- Node.js 18+ or Bun 1.0+
- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for caching)

## Step 1: Clone and Setup

```bash
# Clone repository
git clone https://github.com/arsaka/signate.git
cd signate/ARSAKA_PUGUH

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
bun install
```

## Step 2: Database Setup

```bash
# Create database
createdb arsaka_puguh

# Run migrations
cd backend
psql -d arsaka_puguh -f migrations/001_initial_schema.sql
psql -d arsaka_puguh -f migrations/002_rules_table.sql
# ... run all migrations 001-011

# Or run all at once
for f in migrations/*.sql; do psql -d arsaka_puguh -f "$f"; done
```

## Step 3: Environment Configuration

Create `.env` file in `backend/`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/arsaka_puguh

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Midtrans (Sandbox)
MIDTRANS_SERVER_KEY=SB-Mid-server-xxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
MIDTRANS_IS_PRODUCTION=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# OAuth (Optional)
# GOOGLE_CLIENT_ID=xxx
# GOOGLE_CLIENT_SECRET=xxx
# GITHUB_CLIENT_ID=xxx
# GITHUB_CLIENT_SECRET=xxx
```

Create `.env` file in `frontend/`:

```env
VITE_API_URL=http://localhost:8001
VITE_MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
```

## Step 4: Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn core.app:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun run dev
```

## Step 5: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/docs

## Step 6: Create Your First Account

1. Open http://localhost:5173/register
2. Enter your email and password
3. Click "Create Account"
4. A default organization and project are created for you
5. You're now on the dashboard!

## Common Tasks

### Create a Project

```bash
curl -X POST http://localhost:8001/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "name": "My Project",
    "description": "My first project",
    "environment": "development"
  }' \
  "?tenant_id=550e8400-e29b-41d4-a716-446655440000"
```

### Create a Decision Rule

```bash
curl -X POST http://localhost:8001/api/v1/rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "name": "My First Rule",
    "rule_type": "approval",
    "conditions": {"amount": {"gt": 1000}},
    "actions": {"require_approval": true}
  }'
```

### Evaluate a Decision

```bash
curl -X POST http://localhost:8001/api/v1/decisions/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "context": {"amount": 1500},
    "rule_ids": ["rule-uuid-here"]
  }'
```

## Troubleshooting

### "Database connection failed"

- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in .env
- Ensure database exists: `psql -l | grep arsaka_puguh`

### "CORS error"

- Add your frontend URL to CORS_ORIGINS in backend .env
- Restart the backend server

### "Token expired"

- Login again to get a new token
- Use the refresh token endpoint: `POST /api/v1/auth/refresh`

## Next Steps

- Read the [User Guide](./USER_GUIDE.md) for detailed features
- Check [API Overview](./API_OVERVIEW.md) for all endpoints
- See [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) for production

---

*Need help? Open an issue on GitHub or contact support@arsaka.io*
