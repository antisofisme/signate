# Claude Code - Project Context

## 🎯 Quick Start for New Conversations

When starting a new conversation with Claude Code, share this context:

```
This is the Smart TV Digital Signage project located at /mnt/g/khoirul/signate.

MCP Servers available:
- PostgreSQL: postgresql://signage_user:your_password_here@192.168.5.12:5434/signage_db
- Playwright: For browser testing
- Git: Repository at /mnt/g/khoirul/signate
- Filesystem: Project root access
- Chrome DevTools: For debugging

Backend runs on 192.168.5.12:8001 (Docker)
Frontend dev server on localhost:3000
Database on 192.168.5.12:5434
```

## 📋 When to Use Which MCP

### Database Operations
**Use**: PostgreSQL MCP
**Examples**:
- "Show all devices in database"
- "Query: SELECT * FROM users WHERE active=true"
- "Check schema for devices table"

### Frontend Debugging
**Use**: Chrome DevTools or Playwright MCP
**Examples**:
- "Debug localhost:3000 and check for errors"
- "Take screenshot of web admin"
- "Inspect network requests on viewer page"

### File Operations
**Use**: Filesystem MCP
**Examples**:
- "List all TypeScript files in web-admin"
- "Read backend/app/api/content.py"
- "Find all TODO comments in code"

### Git Operations
**Use**: Git MCP
**Examples**:
- "Show git status"
- "Show commits from today"
- "List modified files"

### Testing & Automation
**Use**: Playwright MCP
**Examples**:
- "Generate test for login flow"
- "Test device registration on viewer"
- "Take screenshots of all pages"

## 🔧 Common Tasks

### Check System Status
```bash
# Backend health
curl http://192.168.5.12:8001/health

# Database (via PostgreSQL MCP)
"Query: SELECT COUNT(*) FROM devices"

# Containers
ssh gzjbbk@192.168.5.12 "docker ps | grep signage"
```

### Debug Issues
1. Frontend errors → Use Chrome DevTools MCP
2. Backend errors → Check Docker logs
3. Database issues → Use PostgreSQL MCP
4. File not found → Use Filesystem MCP

## 📝 Important Info

- **Server**: 192.168.5.12 (SSH: gzjbbk / Password@2021)
- **Database**: PostgreSQL on port 5434
- **Backend**: FastAPI on port 8001 (Docker)
- **Frontend**: React/Vite on port 3000 (dev)
- **Viewer**: Static HTML on port 8080

## 🎁 MCP Servers (9 total)

1. 🌐 Chrome DevTools - Live browser debugging
2. 🎭 Playwright - Cross-browser automation  
3. 🗄️ PostgreSQL - Database queries
4. 📁 Filesystem - File operations
5. 📝 Git - Version control
6. 🤔 Sequential Thinking - Complex problems
7. 🔍 Brave Search - Web research
8. 💾 Memory - Context persistence
9. 🎪 Puppeteer - Chrome automation

---

**Last Updated**: 2025-10-28
