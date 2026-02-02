# SPEC-06: Public Website Integration Architecture

> Arsitektur enterprise-grade untuk company profile website yang sinkron, terotomasi, dan aman

**Related Documents:**
- [SPEC-05: Internal Development Management System](./SPEC-05-internal-dev-management.md) - Source of truth untuk data teknis
- [STD-05: Versioning](./STD-05-notification-versioning-flags-sla.md#24-api-versioning-standard) - API versioning standard

---

## 1. Prinsip Inti

### 1.1 Core Principles

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PRINSIP ENTERPRISE WEBSITE                                               ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  1. Website = CONSUMER, bukan EDITOR                                      ║
║     • Website hanya consume data dari Internal Dev System                ║
║     • Tidak ada write-path dari website ke registry                      ║
║     • CMS hanya untuk konten marketing, bukan data teknis                ║
║                                                                           ║
║  2. SINGLE SOURCE OF TRUTH                                                ║
║     • Semua data teknis dari Internal Dev Management System              ║
║     • Module list, features, changelog, versions → dari registry         ║
║     • Marketing content → dari CMS                                       ║
║                                                                           ║
║  3. AUTOMATION FIRST                                                      ║
║     • CI/CD trigger website rebuild saat ada update                      ║
║     • Auto-generate sitemap, structured data, SEO tags                   ║
║     • Performance budget enforced di pipeline                            ║
║                                                                           ║
║  4. VERSION-AWARE                                                         ║
║     • Website bisa tampilkan data per version                            ║
║     • Deprecated features tetap visible untuk existing users             ║
║     • Documentation locked to specific versions                          ║
║                                                                           ║
║  5. PUBLIC vs INTERNAL BOUNDARY                                           ║
║     • Jelas mana data public vs internal                                 ║
║     • Feature flags control visibility                                   ║
║     • Staging website baca staging registry                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Filosofi:**
- Website bukan brosur statis
- Website = sistem terkontrol, terobservasi, version-aware
- Tanpa prinsip ini, hasilnya startup-grade dengan tampilan rapi

---

## 2. Architecture Overview

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEBSITE ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │               DATA SOURCES (Separated)                          │   │
│  │                                                                 │   │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐     │   │
│  │  │  Internal Dev System    │  │      CMS (Headless)     │     │   │
│  │  │  (SPEC-05)              │  │                         │     │   │
│  │  ├─────────────────────────┤  ├─────────────────────────┤     │   │
│  │  │ • Module Registry       │  │ • Company Profile       │     │   │
│  │  │ • Feature List          │  │ • Marketing Copy        │     │   │
│  │  │ • Changelog             │  │ • Landing Pages         │     │   │
│  │  │ • Versions              │  │ • Blog Posts            │     │   │
│  │  │ • Release Notes         │  │ • SEO Content           │     │   │
│  │  └────────┬────────────────┘  └────────┬────────────────┘     │   │
│  │           │                             │                     │   │
│  │           │ Public API                  │ GraphQL/REST        │   │
│  │           │ (Read-only)                 │ (Read-only)         │   │
│  └───────────┼─────────────────────────────┼─────────────────────┘   │
│              │                             │                         │
│              └──────────┬──────────────────┘                         │
│                         │                                             │
│              ┌──────────▼──────────┐                                 │
│              │   WEBSITE BACKEND   │                                 │
│              │   (Next.js/Astro)   │                                 │
│              ├─────────────────────┤                                 │
│              │ • Data aggregation  │                                 │
│              │ • Caching layer     │                                 │
│              │ • SSG/ISR           │                                 │
│              │ • SEO generation    │                                 │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│              ┌──────────▼──────────┐                                 │
│              │   STATIC SITE       │                                 │
│              │   (CDN)             │                                 │
│              ├─────────────────────┤                                 │
│              │ • Product pages     │                                 │
│              │ • Module catalog    │                                 │
│              │ • Changelog         │                                 │
│              │ • Documentation     │                                 │
│              │ • Marketing pages   │                                 │
│              └─────────────────────┘                                 │
│                         │                                             │
│                         ▼                                             │
│                    PUBLIC USERS                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DEVELOPER DEPLOYS MODULE                                               │
│           │                                                             │
│           │ 1. Push code & tag version                                 │
│           ▼                                                             │
│    ┌─────────────┐                                                     │
│    │   CI/CD     │                                                     │
│    └──────┬──────┘                                                     │
│           │                                                             │
│           │ 2. Update Internal Dev System                              │
│           ▼                                                             │
│    ┌──────────────────────────┐                                        │
│    │  Internal Dev System     │                                        │
│    │  (Module Registry)       │                                        │
│    └──────┬───────────────────┘                                        │
│           │                                                             │
│           │ 3. Webhook trigger                                         │
│           ▼                                                             │
│    ┌─────────────────────┐                                             │
│    │  Website Build      │                                             │
│    │  Trigger (CI/CD)    │                                             │
│    └──────┬──────────────┘                                             │
│           │                                                             │
│           │ 4. Fetch latest data                                       │
│           ├────────────────┬────────────────┐                          │
│           │                │                │                          │
│           ▼                ▼                ▼                          │
│    ┌──────────┐   ┌────────────┐   ┌──────────┐                      │
│    │ Registry │   │    CMS     │   │ Old Cache│                      │
│    │   API    │   │    API     │   │(fallback)│                      │
│    └────┬─────┘   └─────┬──────┘   └────┬─────┘                      │
│         │               │               │                              │
│         └───────────────┴───────────────┘                              │
│                         │                                               │
│                         │ 5. Build static site                         │
│                         ▼                                               │
│              ┌────────────────────┐                                    │
│              │  Static Site Gen   │                                    │
│              │  • Module pages    │                                    │
│              │  • Feature lists   │                                    │
│              │  • Changelog       │                                    │
│              │  • SEO tags        │                                    │
│              │  • Sitemap         │                                    │
│              └─────────┬──────────┘                                    │
│                        │                                                │
│                        │ 6. Deploy to CDN                              │
│                        ▼                                                │
│              ┌────────────────────┐                                    │
│              │    CDN (Vercel/    │                                    │
│              │    Cloudflare)     │                                    │
│              └─────────┬──────────┘                                    │
│                        │                                                │
│                        │ 7. Serve to users                             │
│                        ▼                                                │
│                   PUBLIC USERS                                          │
│                   • See latest modules                                  │
│                   • Read features                                       │
│                   • View changelog                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Content Strategy

### 3.1 Data Ownership

**Engineering-Owned (dari Internal Dev System):**
- ✅ Module list & descriptions
- ✅ Feature list per module
- ✅ Changelog & release notes
- ✅ Version numbers & release dates
- ✅ Status (beta, stable, deprecated)
- ✅ Public visibility flags
- ✅ Technical specifications

**Marketing-Owned (dari CMS):**
- ✅ Company profile
- ✅ Marketing copy & positioning
- ✅ Landing page content
- ✅ Blog posts & articles
- ✅ SEO content & meta tags
- ✅ Images & media assets

**Rule:**
> CMS **read-only** untuk data teknis (hanya display).
> Registry **read-only** untuk marketing (no marketing content in registry).

### 3.2 Content Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTENT TYPES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PUBLIC PAGES                                                           │
│                                                                         │
│  1. Homepage                                                            │
│     Source: CMS (hero, value props) + Registry (module count, latest)  │
│                                                                         │
│  2. Products/Modules Page                                               │
│     Source: Registry (module list) + CMS (descriptions, positioning)   │
│     URL: /products                                                      │
│     • List semua public modules                                        │
│     • Filter by category, status                                       │
│     • Auto-updated saat module baru di-publish                         │
│                                                                         │
│  3. Module Detail Page                                                  │
│     Source: Registry (features, versions) + CMS (marketing content)    │
│     URL: /products/{module_code}                                        │
│     • Module overview                                                   │
│     • Feature list (dari registry)                                     │
│     • Pricing (dari CMS)                                               │
│     • Screenshots (dari CMS)                                           │
│     • CTA (dari CMS)                                                   │
│                                                                         │
│  4. Changelog Page                                                      │
│     Source: Registry (releases)                                         │
│     URL: /changelog atau /products/{module}/changelog                   │
│     • Version-aware changelog                                          │
│     • Filter by module, version, date                                  │
│     • Breaking changes highlighted                                     │
│                                                                         │
│  5. Documentation                                                       │
│     Source: Registry (API specs) + Docs repo (guides)                  │
│     URL: /docs                                                          │
│     • Version-locked docs                                              │
│     • Auto-generated API reference                                     │
│     • Integration guides                                               │
│                                                                         │
│  6. Company/About Page                                                  │
│     Source: CMS                                                         │
│     URL: /about, /team, /careers                                        │
│                                                                         │
│  7. Blog                                                                │
│     Source: CMS                                                         │
│     URL: /blog                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation

### 4.1 Technology Stack

**Recommended Stack:**
- **Framework:** Next.js 14+ (App Router) atau Astro
- **CMS:** Sanity, Strapi, atau Contentful
- **Styling:** Tailwind CSS
- **Deployment:** Vercel atau Cloudflare Pages
- **Analytics:** Vercel Analytics atau Plausible

**Why Next.js/Astro:**
- Static Site Generation (SSG)
- Incremental Static Regeneration (ISR)
- Excellent SEO support
- API routes untuk server-side logic
- Image optimization

### 4.2 Data Fetching

**Build Time (SSG):**
```typescript
// app/products/page.tsx
import { getPublicModules } from '@/lib/registry-api';
import { getProductsContent } from '@/lib/cms';

export default async function ProductsPage() {
  // Fetch dari Internal Dev System (registry)
  const modules = await getPublicModules();

  // Fetch dari CMS (marketing content)
  const content = await getProductsContent();

  return (
    <div>
      <h1>{content.hero.title}</h1>
      <p>{content.hero.description}</p>

      <ModuleGrid modules={modules} />
    </div>
  );
}
```

**API Client untuk Registry:**
```typescript
// lib/registry-api.ts
const REGISTRY_API = process.env.REGISTRY_API_URL;
const API_KEY = process.env.REGISTRY_API_KEY;

export async function getPublicModules() {
  const response = await fetch(`${REGISTRY_API}/api/public/modules`, {
    headers: {
      'X-API-Key': API_KEY,
    },
    next: { revalidate: 3600 } // Cache 1 hour
  });

  if (!response.ok) {
    // Fallback to cached data
    return getCachedModules();
  }

  return response.json();
}

export async function getModuleDetails(code: string) {
  const response = await fetch(`${REGISTRY_API}/api/public/modules/${code}`, {
    headers: { 'X-API-Key': API_KEY },
    next: { revalidate: 3600 }
  });

  return response.json();
}

export async function getChangelog(module?: string) {
  const url = module
    ? `${REGISTRY_API}/api/public/releases?module=${module}`
    : `${REGISTRY_API}/api/public/releases`;

  const response = await fetch(url, {
    headers: { 'X-API-Key': API_KEY },
    next: { revalidate: 1800 } // Cache 30 min
  });

  return response.json();
}
```

### 4.3 Caching Strategy

**Multi-Layer Cache:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CACHING STRATEGY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Layer 1: CDN Cache (Cloudflare/Vercel)                                │
│  • TTL: 1 hour                                                          │
│  • Purge on deploy                                                      │
│                                                                         │
│  Layer 2: Next.js Data Cache                                            │
│  • Revalidate: 1 hour (ISR)                                             │
│  • Stale-while-revalidate                                               │
│                                                                         │
│  Layer 3: Application Cache (Redis)                                     │
│  • TTL: 5 minutes                                                       │
│  • Fallback if registry down                                            │
│                                                                         │
│  Layer 4: Last Known Good Data                                          │
│  • Stored in codebase (JSON files)                                     │
│  • Updated on each build                                                │
│  • Fallback if all else fails                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Implementation:**
```typescript
// lib/cache.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function getCachedOrFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 300 // 5 minutes
): Promise<T> {
  // Try Redis cache first
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  try {
    // Fetch fresh data
    const data = await fetcher();

    // Store in cache
    await redis.setex(key, ttl, JSON.stringify(data));

    // Also update last known good data
    await updateLastKnownGood(key, data);

    return data;
  } catch (error) {
    console.error('Fetch failed, using last known good:', error);
    return getLastKnownGood(key);
  }
}
```

### 4.4 Graceful Degradation

**Jika Internal Dev System Down:**
```typescript
// lib/fallback.ts
import lastKnownGood from '@/data/last-known-good.json';

export function getCachedModules() {
  return lastKnownGood.modules;
}

export async function getPublicModulesWithFallback() {
  try {
    // Try fresh data
    const data = await fetch(REGISTRY_API + '/api/public/modules', {
      signal: AbortSignal.timeout(5000) // 5s timeout
    });
    return await data.json();
  } catch (error) {
    // Log error for monitoring
    console.error('Registry API failed, using fallback:', error);

    // Use last known good data
    return getCachedModules();
  }
}
```

**Last Known Good Data:**
```json
// data/last-known-good.json
{
  "modules": [...],
  "features": [...],
  "last_updated": "2024-12-23T10:00:00Z"
}
```

---

## 5. CI/CD & Update Flow

### 5.1 Automated Update Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     WEBSITE AUTO-UPDATE FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Developer deploys new module version                                │
│     ↓                                                                   │
│  2. CI/CD updates Internal Dev System (SPEC-05)                         │
│     ↓                                                                   │
│  3. Internal Dev System sends webhook to Vercel                         │
│     POST https://api.vercel.com/v1/integrations/deploy/...             │
│     ↓                                                                   │
│  4. Vercel triggers website rebuild                                     │
│     • Fetch latest data from registry                                  │
│     • Fetch content from CMS                                           │
│     • Generate static pages                                            │
│     • Generate sitemap & SEO tags                                      │
│     ↓                                                                   │
│  5. Deploy to production CDN                                            │
│     • Purge CDN cache                                                  │
│     • Update last-known-good data                                      │
│     ↓                                                                   │
│  6. Website now shows latest modules/features                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 GitHub Actions Example

```yaml
# .github/workflows/deploy-website.yml
name: Deploy Website

on:
  # Manual trigger
  workflow_dispatch:

  # Webhook from Internal Dev System
  repository_dispatch:
    types: [registry-updated]

  # Scheduled rebuild (daily)
  schedule:
    - cron: '0 0 * * *'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Fetch latest data from registry
        env:
          REGISTRY_API_URL: ${{ secrets.REGISTRY_API_URL }}
          REGISTRY_API_KEY: ${{ secrets.REGISTRY_API_KEY }}
        run: npm run fetch-registry-data

      - name: Build website
        env:
          CMS_API_URL: ${{ secrets.CMS_API_URL }}
          CMS_API_KEY: ${{ secrets.CMS_API_KEY }}
        run: npm run build

      - name: Run SEO checks
        run: npm run check-seo

      - name: Run performance budget
        run: npm run check-performance

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'

      - name: Purge CDN cache
        run: npm run purge-cache
```

**Fetch Registry Data Script:**
```javascript
// scripts/fetch-registry-data.js
const fs = require('fs');

async function fetchRegistryData() {
  const modules = await fetch(`${process.env.REGISTRY_API_URL}/api/public/modules`, {
    headers: { 'X-API-Key': process.env.REGISTRY_API_KEY }
  }).then(r => r.json());

  const features = await fetch(`${process.env.REGISTRY_API_URL}/api/public/features`, {
    headers: { 'X-API-Key': process.env.REGISTRY_API_KEY }
  }).then(r => r.json());

  // Save as last-known-good data
  fs.writeFileSync('./data/last-known-good.json', JSON.stringify({
    modules,
    features,
    last_updated: new Date().toISOString()
  }, null, 2));
}

fetchRegistryData();
```

---

## 6. SEO & Performance

### 6.1 SEO Automation

**Auto-Generated Sitemap:**
```typescript
// app/sitemap.ts
import { getPublicModules } from '@/lib/registry-api';

export default async function sitemap() {
  const modules = await getPublicModules();

  const moduleUrls = modules.map(module => ({
    url: `https://example.com/products/${module.code}`,
    lastModified: module.updated_at,
    changeFrequency: 'weekly',
    priority: 0.8,
  }));

  return [
    {
      url: 'https://example.com',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: 'https://example.com/products',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
    ...moduleUrls,
  ];
}
```

**Structured Data:**
```typescript
// components/ModuleSchema.tsx
export function ModuleSchema({ module }) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: module.name,
    description: module.description,
    applicationCategory: 'BusinessApplication',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD'
    },
    operatingSystem: 'Web',
    softwareVersion: module.current_version,
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
```

### 6.2 Performance Budget

**Enforced in CI/CD:**
```json
// performance-budget.json
{
  "budgets": [
    {
      "path": "/*",
      "timings": [
        {
          "metric": "first-contentful-paint",
          "budget": 1500
        },
        {
          "metric": "largest-contentful-paint",
          "budget": 2500
        },
        {
          "metric": "cumulative-layout-shift",
          "budget": 0.1
        },
        {
          "metric": "total-blocking-time",
          "budget": 300
        }
      ],
      "resourceSizes": [
        {
          "resourceType": "script",
          "budget": 300
        },
        {
          "resourceType": "total",
          "budget": 500
        }
      ]
    }
  ]
}
```

**CI Check:**
```bash
# Check performance budget
npm run build
lighthouse --budget-path=performance-budget.json https://staging.example.com
```

---

## 7. Version-Aware Content

### 7.1 Version Selector

**Show features per version:**
```typescript
// components/VersionSelector.tsx
export function VersionSelector({ module }) {
  const [version, setVersion] = useState(module.current_version);
  const { data: features } = useSWR(
    `/api/features?module=${module.code}&version=${version}`
  );

  return (
    <div>
      <select value={version} onChange={(e) => setVersion(e.target.value)}>
        {module.versions.map(v => (
          <option key={v} value={v}>Version {v}</option>
        ))}
      </select>

      <FeatureList features={features} version={version} />
    </div>
  );
}
```

### 7.2 Deprecated Feature Handling

```typescript
// components/FeatureCard.tsx
export function FeatureCard({ feature }) {
  const isDeprecated = feature.status === 'deprecated';

  return (
    <div className={isDeprecated ? 'opacity-50' : ''}>
      <h3>{feature.name}</h3>
      {isDeprecated && (
        <Badge variant="warning">
          Deprecated in v{feature.version_deprecated}
        </Badge>
      )}
      <p>{feature.description}</p>
    </div>
  );
}
```

---

## 8. Governance & Approval

### 8.1 Content Approval Workflow

**CMS Workflow:**
```
Draft → Review → Scheduled → Published
```

**Registry Visibility Control:**
```sql
-- Only stable modules with public_visible=true appear on website
SELECT * FROM module_registry
WHERE status = 'stable' AND public_visible = true;
```

### 8.2 Rollback Capability

**Git-based Content Rollback:**
```bash
# Rollback to previous version
git revert HEAD
git push origin main

# Trigger redeploy
vercel --prod
```

---

## 9. Observability

### 9.1 Monitoring

**Error Tracking:**
- Sentry untuk JS errors
- API error monitoring
- Broken link detection

**Analytics:**
- Page views per module
- Conversion funnel (landing → product → contact)
- Search queries

**Alerts:**
- Registry API down (fallback activated)
- Performance budget exceeded
- SEO score dropped
- High error rate

### 9.2 Health Dashboard

**Metrics:**
- Website uptime
- Average response time
- Registry API availability
- CMS API availability
- CDN cache hit rate
- Build success rate

---

## 10. Security

### 10.1 Security Headers

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
        ],
      },
    ];
  },
};
```

### 10.2 Dependency Scanning

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0' # Weekly

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run npm audit
        run: npm audit --audit-level=moderate

      - name: Run Snyk scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

---

## 11. Environment Parity

### 11.1 Environments

**Staging:**
- URL: https://staging.example.com
- Registry: Staging registry API
- CMS: Staging CMS
- Purpose: Test before production

**Production:**
- URL: https://example.com
- Registry: Production registry API
- CMS: Production CMS
- Purpose: Live public site

**Preview (PR):**
- URL: https://pr-123.example.com
- Registry: Staging registry
- CMS: Staging CMS
- Purpose: Review changes per PR

### 11.2 Environment Config

```typescript
// lib/config.ts
const config = {
  development: {
    registryApi: 'http://localhost:8000',
    cmsApi: 'http://localhost:1337',
  },
  staging: {
    registryApi: 'https://staging-api.example.com',
    cmsApi: 'https://staging-cms.example.com',
  },
  production: {
    registryApi: 'https://api.example.com',
    cmsApi: 'https://cms.example.com',
  },
};

export default config[process.env.NODE_ENV];
```

---

## 12. Checklist (Enterprise-Grade)

**Core Requirements:**
- ✅ Metadata Registry sebagai single source of truth
- ✅ CMS hanya untuk narasi marketing
- ✅ CI/CD auto-update website saat deploy
- ✅ Governance & approval workflow
- ✅ Version-aware content display
- ✅ Public data contract (API)
- ✅ SEO & performance automated
- ✅ Observability (monitoring & alerts)
- ✅ Security headers & CSP
- ✅ Environment parity (staging/prod)
- ✅ Graceful degradation (fallback)
- ✅ Audit log untuk publish

**Advanced:**
- ✅ Multi-layer caching strategy
- ✅ Performance budget enforcement
- ✅ Structured data (Schema.org)
- ✅ Auto-generated sitemap
- ✅ A/B testing capability
- ✅ Analytics integration

---

## 13. Reference

**Related Documents:**
- [SPEC-05: Internal Development Management System](./SPEC-05-internal-dev-management.md)
- [STD-05: API Versioning](./STD-05-notification-versioning-flags-sla.md#24-api-versioning-standard)
- [GUIDE-01: Development Flow](./GUIDE-01-development-flow.md)

**External Resources:**
- Next.js Documentation: https://nextjs.org/docs
- Vercel Deployment: https://vercel.com/docs
- Schema.org: https://schema.org
- Web Vitals: https://web.dev/vitals

---

**Last Updated:** 2024-12-23
**Status:** DRAFT - Ready for Review
**Owner:** Engineering + Marketing Team
