# API Integration Development Plan

**Branch**: `feature/api-integration`
**Created**: 2025-10-27
**Base**: `feature/firebird-integration`

## Tujuan Branch Ini

Branch ini digunakan untuk pengembangan API integrasi dengan sistem eksternal, termasuk:

### 1. Hotel PMS Integration APIs
- ✅ Firebird database integration (sudah ada)
- 🔄 Guest information API
- 🔄 Room status synchronization
- 🔄 Check-in/check-out events webhook
- 🔄 Real-time guest data updates

### 2. Third-Party Service APIs
- 🔄 Payment gateway integration (Midtrans/Xendit)
- 🔄 Weather API integration (OpenWeatherMap)
- 🔄 Analytics API (Google Analytics/Mixpanel)
- 🔄 Social media content API
- 🔄 External content providers

### 3. Internal API Enhancements
- 🔄 RESTful API versioning (v1, v2)
- 🔄 GraphQL API endpoint
- 🔄 Webhook system for third-party notifications
- 🔄 API rate limiting & throttling
- 🔄 API authentication with API keys
- 🔄 API documentation with Swagger/OpenAPI

### 4. Data Synchronization APIs
- 🔄 Bulk data import/export APIs
- 🔄 Scheduled sync jobs
- 🔄 Real-time data streaming
- 🔄 Data transformation pipelines
- 🔄 Conflict resolution strategies

## Current Status

### ✅ Completed (from previous branch)
- System settings API (`/api/settings/system/info`)
- Content upload API with full schema support
- WebSocket dashboard (`/ws/dashboard`)
- Firebird database integration foundation
- Database schema fixes (contents, playlists, playlist_content)

### 🚧 In Progress
- None (branch baru dibuat)

### 📋 Planned
1. **Hotel PMS API Endpoints**
   - GET `/api/integrations/pms/guests` - Get guest list
   - GET `/api/integrations/pms/guests/{room_number}` - Get guest by room
   - POST `/api/integrations/pms/sync` - Manual sync trigger
   - GET `/api/integrations/pms/status` - Integration status

2. **External Content API**
   - GET `/api/integrations/content/sources` - List content sources
   - POST `/api/integrations/content/import` - Import external content
   - GET `/api/integrations/content/preview/{source_id}` - Preview external content

3. **Webhook Management**
   - POST `/api/webhooks/register` - Register webhook endpoint
   - GET `/api/webhooks` - List registered webhooks
   - DELETE `/api/webhooks/{id}` - Delete webhook
   - POST `/api/webhooks/test/{id}` - Test webhook

4. **API Authentication**
   - POST `/api/auth/api-keys/generate` - Generate API key
   - GET `/api/auth/api-keys` - List API keys
   - DELETE `/api/auth/api-keys/{key_id}` - Revoke API key
   - GET `/api/auth/api-keys/{key_id}/usage` - API key usage stats

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Hotel PMS│  │ Payment  │  │ Weather  │  │ Analytics│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Integration Layer  │
                    │  (API Gateway)      │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│  Data Sync     │   │  Webhook        │   │  API Auth      │
│  Service       │   │  Handler        │   │  Service       │
└───────┬────────┘   └────────┬────────┘   └───────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Backend API      │
                    │   (FastAPI)        │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│  PostgreSQL    │   │   Redis Cache   │   │  Firebird DB   │
│  (Main DB)     │   │   (Temp Data)   │   │  (Hotel PMS)   │
└────────────────┘   └─────────────────┘   └────────────────┘
```

## Development Guidelines

### 1. API Design Principles
- Follow RESTful conventions
- Use proper HTTP status codes
- Implement pagination for list endpoints
- Include comprehensive error messages
- Version APIs with `/api/v1/`, `/api/v2/` prefixes
- Document all endpoints with OpenAPI/Swagger

### 2. Security Best Practices
- Validate all input data
- Sanitize output data
- Use API key authentication for machine-to-machine
- Implement rate limiting (100 requests/minute per IP)
- Log all API access attempts
- Encrypt sensitive data in transit and at rest

### 3. Testing Requirements
- Unit tests for all endpoints
- Integration tests for external API calls
- Load testing for high-traffic endpoints
- Mock external services in tests
- Minimum 80% code coverage

### 4. Documentation
- Update API documentation in `/docs/api/`
- Add inline code comments
- Create integration guides for each service
- Maintain changelog for API versions

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── integrations/          # New integration endpoints
│   │   │   ├── __init__.py
│   │   │   ├── pms.py             # Hotel PMS endpoints
│   │   │   ├── payment.py         # Payment gateway endpoints
│   │   │   ├── weather.py         # Weather API endpoints
│   │   │   └── webhooks.py        # Webhook management
│   │   └── ...
│   ├── services/
│   │   ├── integrations/          # Integration business logic
│   │   │   ├── __init__.py
│   │   │   ├── pms_service.py
│   │   │   ├── payment_service.py
│   │   │   └── webhook_service.py
│   │   └── ...
│   ├── schemas/
│   │   ├── integrations/          # Pydantic models for integrations
│   │   │   ├── __init__.py
│   │   │   ├── pms.py
│   │   │   └── webhook.py
│   │   └── ...
│   └── models/
│       ├── api_key.py             # API key model
│       ├── webhook.py             # Webhook registration model
│       └── integration_log.py     # Integration activity log
└── tests/
    └── integrations/              # Integration tests
        ├── test_pms.py
        ├── test_payment.py
        └── test_webhooks.py
```

## Next Steps

1. ✅ Create branch `feature/api-integration`
2. 🔄 Define integration database models
3. 🔄 Implement Hotel PMS API endpoints
4. 🔄 Add webhook system
5. 🔄 Implement API key authentication
6. 🔄 Add comprehensive API documentation
7. 🔄 Write integration tests
8. 🔄 Deploy to staging for testing

## Notes

- All external API credentials harus disimpan di `.env` file
- Gunakan `httpx` untuk async HTTP requests
- Implement retry logic dengan exponential backoff
- Cache external API responses di Redis (TTL: 5 minutes)
- Log semua integration errors ke database

## Related Branches

- `feature/firebird-integration` - Parent branch (Firebird DB integration)
- `main` - Production branch
- `feature/rename-content-table` - Content table restructuring

## Pull Request Checklist

Sebelum merge ke main, pastikan:
- [ ] All tests passing (100% for new code)
- [ ] API documentation updated
- [ ] Environment variables documented in `.env.example`
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Code review approved by 2+ reviewers
- [ ] Migration scripts tested on staging
- [ ] Rollback plan documented

---

**Last Updated**: 2025-10-27
**Contributors**: Claude AI Assistant
