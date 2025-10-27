# Smart TV Digital Signage API - Documentation

Welcome to the Smart TV Digital Signage API documentation. This folder contains comprehensive documentation for the backend API.

---

## 📚 Documentation Files

### 1. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
**Complete API reference and usage guide**

Comprehensive documentation covering:
- ✅ API Overview and Architecture
- ✅ Authentication Flow (JWT)
- ✅ All 92 Endpoints by Category
- ✅ Response Standards (Quick Wins format)
- ✅ Common Use Cases with Examples
- ✅ Error Handling
- ✅ WebSocket Support
- ✅ Testing Guide

**Use this for:** Learning how to use the API, integration guide, troubleshooting

---

### 2. [openapi-enhanced.yaml](./openapi-enhanced.yaml)
**Enhanced OpenAPI 3.1 Specification**

Comprehensive OpenAPI spec with:
- ✅ Detailed descriptions for all schemas
- ✅ Security definitions (JWT Bearer)
- ✅ Request/response examples
- ✅ Error response schemas
- ✅ Quick Wins standardized response format
- ✅ Tag-based organization

**Use this for:**
- Import into Postman/Insomnia
- Generate client SDKs
- View in Swagger UI / ReDoc
- API contract validation

**How to use:**
```bash
# View in Swagger Editor
docker run -p 8080:8080 -e SWAGGER_FILE=/openapi-enhanced.yaml \
  -v $(pwd):/usr/share/nginx/html/openapi-enhanced.yaml \
  swaggerapi/swagger-editor

# Generate Python client SDK
openapi-generator-cli generate \
  -i openapi-enhanced.yaml \
  -g python \
  -o ./sdks/python

# Import to Postman
# 1. Open Postman
# 2. Click "Import"
# 3. Select "openapi-enhanced.yaml"
```

---

### 3. [API_RECOMMENDATIONS.md](./API_RECOMMENDATIONS.md)
**Comprehensive improvement recommendations and roadmap**

Includes:
- ✅ Current State Analysis (92 endpoints across 13 categories)
- ✅ Priority Recommendations (High/Medium/Low)
- ✅ Security Enhancements (Rate limiting, MFA, HTTPS)
- ✅ Performance Optimizations (Caching, query optimization)
- ✅ Documentation Improvements
- ✅ Developer Experience Enhancements
- ✅ Monitoring and Observability
- ✅ Implementation Roadmap (10-week plan)

**Use this for:** Planning future API improvements, technical debt prioritization

---

## 🚀 Quick Start

### View Auto-Generated Docs

The API automatically generates interactive documentation:

```bash
# Swagger UI (Interactive API Explorer)
http://192.168.5.12:8001/docs

# ReDoc (Clean API Reference)
http://192.168.5.12:8001/redoc

# OpenAPI JSON Spec (Auto-generated)
http://192.168.5.12:8001/openapi.json
```

### Test the API

**Option 1: Using cURL**
```bash
# Login
TOKEN=$(curl -X POST http://192.168.5.12:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# List devices
curl http://192.168.5.12:8001/api/devices \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Option 2: Using Python**
```python
import requests

# Login
response = requests.post(
    'http://192.168.5.12:8001/api/auth/login',
    json={'username': 'admin', 'password': 'password'}
)
token = response.json()['access_token']

# List devices
headers = {'Authorization': f'Bearer {token}'}
devices = requests.get(
    'http://192.168.5.12:8001/api/devices',
    headers=headers
).json()
print(devices)
```

**Option 3: Using Postman**
1. Import `openapi-enhanced.yaml` or `http://192.168.5.12:8001/openapi.json`
2. Create environment variable `TOKEN`
3. Add pre-request script for auto-login
4. Test endpoints

---

## 📊 API Summary

### Endpoint Count by Category

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Devices** | 20 | Device registration, management, commands, heartbeat |
| **Playlists** | 14 | Playlist CRUD, content management, assignments |
| **Content** | 10 | Upload, manage, assign media content |
| **Tags** | 9 | Tag management and device grouping |
| **Firebird Integration** | 8 | External database integration |
| **Speed Test** | 5 | Network speed testing |
| **Authentication** | 4 | Login, token refresh, user info |
| **Settings** | 4 | System configuration |
| **Device Logs** | 4 | Activity logging |
| **Client** | 2 | Device playlist fetching |
| **Quick Wins Demo** | 8 | Demo endpoints (DEBUG mode only) |
| **WebSocket** | 1 | Real-time communication |
| **Untagged** | 4 | Health check, ping, root |
| **Total** | **92** | |

---

## 🔐 Authentication

Most endpoints require JWT Bearer token authentication:

```http
Authorization: Bearer <access_token>
```

**Token Expiry:**
- Access Token: 30 minutes
- Refresh Token: 7 days

**Client endpoints (NO AUTH required):**
- `POST /api/devices/monitor/register` - Device self-registration
- `POST /api/devices/heartbeat` - Device heartbeat
- `GET /api/devices/check-activation/{code}` - Activation status check
- `GET /api/client/playlist` - Fetch device playlist
- `GET /api/devices/{id}/commands/pending` - Get pending commands

---

## 🎯 Common Use Cases

### 1. Register a New Monitor Device

```bash
# Step 1: Device self-registers
curl -X POST http://192.168.5.12:8001/api/devices/monitor/register \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "123456",
    "device_name": "Lobby Display",
    "platform": "Chrome"
  }'

# Step 2: Admin activates device (via Web Admin)
curl -X PUT http://192.168.5.12:8001/api/devices/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# Step 3: Device starts heartbeat (every 30s)
curl -X POST http://192.168.5.12:8001/api/devices/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "screen_width": 1920, "screen_height": 1080}'
```

### 2. Upload Content and Assign to Device

```bash
# Step 1: Upload content
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@banner.jpg" \
  -F "title=Welcome Banner" \
  -F "duration=10"

# Step 2: Assign to device
curl -X POST http://192.168.5.12:8001/api/content/1/assign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "priority": 5}'
```

### 3. Create Playlist and Assign to Tag

```bash
# Step 1: Create playlist
curl -X POST http://192.168.5.12:8001/api/playlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Morning Announcements", "is_active": true, "priority": 10}'

# Step 2: Add content to playlist
curl -X POST http://192.168.5.12:8001/api/playlists/1/content \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content_ids": [1, 2, 3]}'

# Step 3: Assign to tag
curl -X POST http://192.168.5.12:8001/api/playlists/1/assign/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [1]}'
```

---

## 📝 Response Format

This API follows **Quick Wins** standardized response format.

### Success Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Example Resource"
  },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {...}
  },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 🛠️ Development

### Run API Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

### Generate OpenAPI Spec

```bash
# Auto-generated spec (latest)
curl http://192.168.5.12:8001/openapi.json > openapi.json

# Or access via code
from app.main import app
import json

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
```

---

## 📦 SDK Generation

Generate client SDKs from OpenAPI spec:

```bash
# Python Client
openapi-generator-cli generate \
  -i openapi-enhanced.yaml \
  -g python \
  -o ./sdks/python \
  --additional-properties=packageName=signage_api

# TypeScript/Axios Client
openapi-generator-cli generate \
  -i openapi-enhanced.yaml \
  -g typescript-axios \
  -o ./sdks/typescript

# JavaScript/Fetch Client
openapi-generator-cli generate \
  -i openapi-enhanced.yaml \
  -g javascript \
  -o ./sdks/javascript
```

---

## 🔍 API Testing Tools

### Postman
```bash
# Import OpenAPI spec
1. Open Postman
2. Click "Import"
3. Select "openapi-enhanced.yaml" or paste URL:
   http://192.168.5.12:8001/openapi.json
4. Create environment with base_url and token variables
```

### Insomnia
```bash
# Import OpenAPI spec
1. Open Insomnia
2. Click "Import/Export"
3. Select "Import Data" → "From File"
4. Choose "openapi-enhanced.yaml"
```

### Thunder Client (VS Code)
```bash
# Import OpenAPI spec
1. Install Thunder Client extension
2. Click "Collections" → "Import"
3. Select "openapi-enhanced.yaml"
```

---

## 📈 Monitoring

### Health Check
```bash
curl http://192.168.5.12:8001/health
```

### Metrics (if Prometheus enabled)
```bash
curl http://192.168.5.12:8001/metrics
```

### Logs
```bash
# View logs in Docker
docker logs -f signage-backend

# View structured logs (JSON format in production)
tail -f /var/log/signage-api/app.log
```

---

## 🔗 Related Documentation

- **Main Project README:** [/README.md](../../README.md)
- **Backend README:** [/backend/README.md](../README.md)
- **Frontend (Web Admin):** [/web-admin/README.md](../../web-admin/README.md)
- **Viewer (Device Client):** [/viewer/README.md](../../viewer/README.md)
- **Deployment Guide:** [/docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md)

---

## 💡 Need Help?

- **API Docs:** http://192.168.5.12:8001/docs
- **ReDoc:** http://192.168.5.12:8001/redoc
- **GitHub Issues:** https://github.com/yourusername/signate/issues
- **Email Support:** support@example.com

---

## 📄 License

MIT License - See [LICENSE](../../LICENSE) for details

---

**Last Updated:** 2025-10-27
**API Version:** 1.0.0
**Documentation Version:** 1.0.0
