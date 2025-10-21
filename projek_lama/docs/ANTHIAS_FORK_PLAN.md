# Anthias Fork Plan for Signate

## 🎯 Core Files to Fork and Modify

### 1. Backend Core (Django)
```
anthias_app/           # Main Django application
├── models.py         # Database models (extend for multi-tenant)
├── views.py          # API views (enhance for Signate features)
├── urls.py           # URL routing
├── helpers.py        # Utility functions
└── management/       # Django management commands

anthias_django/        # Django configuration
├── settings.py       # Django settings (modify for Signate)
├── urls.py           # Main URL configuration
└── wsgi.py           # WSGI configuration

api/                   # REST API modules
├── models.py         # API models
├── serializers.py    # Data serialization
├── views.py          # API endpoints (extend for cloud features)
└── urls.py           # API routing
```

### 2. Frontend (React + TypeScript)
```
static/src/           # React source code
├── components/       # React components (rebrand for Signate)
│   ├── app.tsx      # Main app component
│   ├── navbar.tsx   # Navigation (add Signate branding)
│   ├── home/        # Dashboard components
│   ├── settings/    # Settings management
│   └── assets/      # Asset management
├── store/           # Redux store
├── types/           # TypeScript definitions
└── sass/            # Styling (rebrand colors/theme)

templates/            # Django templates
├── base.html        # Base template (Signate branding)
├── react.html       # React app container
└── login.html       # Authentication
```

### 3. Configuration & Build
```
docker/              # Docker configuration
├── Dockerfile.*     # Container definitions (customize for Signate)
└── nginx/           # nginx configuration

docker-compose.*.yml # Development setup (modify for Signate services)
webpack.*.js         # Build configuration
package.json         # Dependencies (add Signate-specific packages)
requirements/        # Python dependencies
```

### 4. Core Libraries
```
lib/                 # Python utilities
├── auth.py         # Authentication (extend for multi-user)
├── utils.py        # Utility functions
└── errors.py       # Error handling

settings.py         # Main configuration (customize for Signate)
```

## 📋 Modification Strategy

### Phase 1: Clean Fork
- [x] Clone official Anthias repository
- [ ] Remove Anthias branding
- [ ] Add Signate branding and configuration
- [ ] Update package names and metadata

### Phase 2: Multi-tenant Architecture
- [ ] Extend Django models for organizations/tenants
- [ ] Add user management and permissions
- [ ] Implement device grouping and management
- [ ] Create cloud API endpoints

### Phase 3: Enhanced Features
- [ ] Advanced scheduling system
- [ ] Analytics and reporting
- [ ] Content distribution network
- [ ] Mobile app API endpoints

### Phase 4: Cloud Platform
- [ ] Multi-device dashboard
- [ ] Real-time monitoring
- [ ] Centralized content management
- [ ] Enterprise features

## 🔧 Key Modifications Needed

### 1. Branding Changes
```bash
# Replace all occurrences of:
"Anthias" → "Signate"
"Screenly" → "Signate" 
"anthias" → "signate"
"screenly" → "signate"
```

### 2. Database Schema Extensions
```python
# Add to models.py
class Organization(models.Model):
    name = models.CharField(max_length=255)
    plan = models.CharField(max_length=50)  # free, pro, enterprise
    created_at = models.DateTimeField(auto_now_add=True)

class Device(models.Model):
    organization = models.ForeignKey(Organization)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    last_seen = models.DateTimeField()
    status = models.CharField(max_length=50)
```

### 3. API Extensions
```python
# Add to api/views.py
class OrganizationViewSet(viewsets.ModelViewSet):
    # Multi-tenant device management
    
class AnalyticsViewSet(viewsets.ModelViewSet):
    # Analytics and reporting endpoints
    
class CloudSyncViewSet(viewsets.ModelViewSet):
    # Cloud synchronization endpoints
```

### 4. Frontend Enhancements
```typescript
// Add to React components
interface SignateConfig {
  organization: string;
  plan: 'free' | 'pro' | 'enterprise';
  features: string[];
}

// New components for Signate
<DeviceCluster />
<AnalyticsDashboard />
<OrganizationSettings />
<CloudSync />
```

## 📁 Signate Project Structure

```
signate/
├── docs/                    # Documentation
├── viewers/                 # Viewer implementations ✅
├── signate-core/           # Forked Anthias core (NEXT)
│   ├── anthias_app/        # Renamed to signate_app
│   ├── anthias_django/     # Renamed to signate_django
│   ├── api/                # Extended API
│   ├── static/             # Rebranded frontend
│   ├── docker/             # Custom containers
│   └── requirements/       # Dependencies
├── signate-cloud/          # Cloud management platform
├── signate-mobile/         # Mobile applications
└── signate-analytics/      # Analytics module
```

## 🚀 Implementation Steps

1. **Copy Core Files**
   ```bash
   cp -r anthias-core signate-core
   cd signate-core
   ```

2. **Rename Modules**
   ```bash
   mv anthias_app signate_app
   mv anthias_django signate_django
   ```

3. **Update Imports and References**
   ```bash
   find . -type f -name "*.py" -exec sed -i 's/anthias_app/signate_app/g' {} \;
   find . -type f -name "*.py" -exec sed -i 's/anthias_django/signate_django/g' {} \;
   ```

4. **Update Branding**
   ```bash
   find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.tsx" -o -name "*.json" \) \
     -exec sed -i 's/Anthias/Signate/g' {} \;
   ```

5. **Customize Configuration**
   - Update package.json metadata
   - Modify Docker configurations
   - Update requirements with Signate-specific packages

## ⚖️ License Compliance

**Anthias License:** AGPL-3.0
- ✅ Can modify and redistribute
- ✅ Can use commercially
- ⚠️ Must keep source code open if distributed as SaaS
- ⚠️ Must include original license and copyright

**Signate Strategy:**
- Open-source core (AGPL compliance)
- Proprietary cloud services
- Commercial support and hosting
- Enterprise features as paid addons

## 🎯 Next Actions

1. Copy essential files to signate-core
2. Start rebranding process
3. Setup development environment
4. Test basic functionality
5. Begin feature extensions

---

*This plan ensures we leverage Anthias's solid foundation while building Signate's unique value proposition.*