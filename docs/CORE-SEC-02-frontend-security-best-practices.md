# CORE-SEC-02: Frontend Security Best Practices for React SaaS Applications

**Version**: 1.0.0
**Last Updated**: 2026-01-28
**Applies To**: All ATLAS Projects with React/Vite frontend

---

## Table of Contents

1. [Token Storage Best Practices](#1-token-storage-best-practices)
2. [XSS Prevention](#2-xss-prevention)
3. [CSRF Protection](#3-csrf-protection)
4. [Secure Headers for SPA](#4-secure-headers-for-spa)
5. [Dependency Security](#5-dependency-security)
6. [Build Security](#6-build-security)
7. [Client-side Input Validation](#7-client-side-input-validation)
8. [Quick Reference Checklist](#8-quick-reference-checklist)

---

## 1. Token Storage Best Practices

### 1.1 Storage Options Comparison

| Storage Method | XSS Vulnerable | CSRF Vulnerable | Recommended |
|----------------|----------------|-----------------|-------------|
| localStorage | YES (High Risk) | No | NO |
| sessionStorage | YES (High Risk) | No | NO |
| Memory (React State) | No | No | YES (Access Token) |
| httpOnly Cookie | No | Yes (mitigatable) | YES (Refresh Token) |

### 1.2 Recommended: Hybrid Approach

The most secure method is to store the **short-lived access token in memory** (React state/context) and the **long-lived refresh token in a secure httpOnly cookie**.

```typescript
// contexts/AuthContext.tsx
import { createContext, useContext, useState, useCallback, useRef } from 'react';

interface AuthContextType {
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Access token stored ONLY in memory - never in localStorage
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const refreshPromise = useRef<Promise<string | null> | null>(null);

  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      // Refresh token is sent automatically via httpOnly cookie
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include', // Important: includes cookies
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const { accessToken: newToken } = await response.json();
      setAccessToken(newToken);
      return newToken;
    } catch (error) {
      setAccessToken(null);
      return null;
    }
  }, []);

  // Singleton pattern for refresh to prevent race conditions
  const getAccessToken = useCallback(async (): Promise<string | null> => {
    if (accessToken) return accessToken;

    if (!refreshPromise.current) {
      refreshPromise.current = refreshAccessToken().finally(() => {
        refreshPromise.current = null;
      });
    }

    return refreshPromise.current;
  }, [accessToken, refreshAccessToken]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const { accessToken: token } = await response.json();
    setAccessToken(token);
  }, []);

  const logout = useCallback(async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    setAccessToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        isAuthenticated: !!accessToken,
        login,
        logout,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
```

### 1.3 Backend Cookie Configuration (FastAPI)

```python
# app/api/auth/routes.py
from fastapi import Response
from datetime import timedelta

def set_refresh_token_cookie(response: Response, refresh_token: str):
    """Set secure httpOnly cookie for refresh token."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,          # Cannot be accessed via JavaScript
        secure=True,            # Only sent over HTTPS
        samesite="strict",      # CSRF protection
        max_age=int(timedelta(days=7).total_seconds()),
        path="/api/auth",       # Limit cookie scope
    )

def clear_refresh_token_cookie(response: Response):
    """Clear refresh token cookie on logout."""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/auth",
    )
```

### 1.4 BFF (Backend for Frontend) Pattern

For maximum security, consider the BFF pattern where tokens never reach the frontend.

```
[Browser] <--session cookie--> [BFF/Gateway] <--JWT--> [API Services]
```

**Benefits:**
- No tokens exposed to JavaScript
- Session ID in httpOnly cookie only
- Tokens stored server-side (Redis)
- Silent token refresh without user interaction

```typescript
// With BFF pattern, API calls are simple
const fetchData = async () => {
  const response = await fetch('/api/data', {
    credentials: 'include', // Session cookie sent automatically
  });
  return response.json();
};
```

---

## 2. XSS Prevention

### 2.1 React's Built-in Protection

React automatically escapes values in JSX, preventing most XSS attacks:

```tsx
// SAFE - React escapes this automatically
const userInput = '<script>alert("xss")</script>';
return <div>{userInput}</div>;
// Renders: &lt;script&gt;alert("xss")&lt;/script&gt;
```

### 2.2 Dangerous Patterns to Avoid

```tsx
// DANGEROUS - Never use without sanitization
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// DANGEROUS - javascript: URLs
<a href={userProvidedUrl}>Click here</a>

// DANGEROUS - Dynamic script/style injection
<script src={userProvidedSrc} />
```

### 2.3 DOMPurify for HTML Content

When you must render HTML (e.g., from a CMS), always sanitize with DOMPurify:

```bash
npm install dompurify
npm install --save-dev @types/dompurify
```

```tsx
// components/SafeHTML.tsx
import DOMPurify from 'dompurify';

interface SafeHTMLProps {
  html: string;
  className?: string;
}

// Configure DOMPurify once
const purifyConfig = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'],
  ALLOWED_ATTR: ['href', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
};

export function SafeHTML({ html, className }: SafeHTMLProps) {
  const sanitizedHTML = DOMPurify.sanitize(html, purifyConfig);

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
}

// Usage
<SafeHTML html={cmsContent} className="article-content" />
```

### 2.4 URL Validation

```tsx
// utils/urlValidator.ts
const ALLOWED_PROTOCOLS = ['http:', 'https:', 'mailto:'];

export function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (ALLOWED_PROTOCOLS.includes(parsed.protocol)) {
      return url;
    }
  } catch {
    // Invalid URL
  }
  return '#'; // Safe fallback
}

// Usage in component
<a href={sanitizeUrl(userProvidedUrl)}>Link</a>
```

### 2.5 Avoid eval() and Similar

```tsx
// NEVER DO THIS
eval(userInput);
new Function(userInput)();
setTimeout(userInput, 0);
setInterval(userInput, 0);

// Instead, use safe alternatives
const safeAction = () => { /* predefined logic */ };
setTimeout(safeAction, 0);
```

---

## 3. CSRF Protection

### 3.1 When CSRF Protection is Needed

| Authentication Method | CSRF Protection Needed |
|----------------------|------------------------|
| JWT in Authorization header | NO |
| JWT in httpOnly cookie | YES |
| Session cookie | YES |

### 3.2 SameSite Cookie Attribute

Modern browsers support SameSite cookies which provide CSRF protection:

```python
# Backend cookie configuration
response.set_cookie(
    key="session",
    value=session_id,
    httponly=True,
    secure=True,
    samesite="strict",  # or "lax" for more flexibility
)
```

**SameSite Values:**
- `strict`: Cookie never sent on cross-site requests (most secure)
- `lax`: Cookie sent on top-level GET navigations (default in Chrome)
- `none`: Cookie sent on all cross-site requests (requires `secure=True`)

### 3.3 Double Submit Cookie Pattern

When cookies are used for authentication, implement the double-submit pattern:

**Backend (FastAPI):**

```python
# app/middleware/csrf.py
import secrets
import hmac
import hashlib
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next):
        if request.method in self.safe_methods:
            return await call_next(request)

        # Get CSRF token from cookie and header
        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token:
            raise HTTPException(status_code=403, detail="CSRF token missing")

        # Verify tokens match (using HMAC for signed tokens)
        expected = self._sign_token(cookie_token)
        if not hmac.compare_digest(expected, header_token):
            raise HTTPException(status_code=403, detail="CSRF token invalid")

        return await call_next(request)

    def _sign_token(self, token: str) -> str:
        return hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()

def generate_csrf_token(response, secret_key: str) -> str:
    """Generate and set CSRF token cookie."""
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # Must be readable by JavaScript
        secure=True,
        samesite="strict",
    )
    return token
```

**Frontend (React):**

```typescript
// utils/csrf.ts
function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

// lib/api.ts
import { signToken } from './crypto'; // Implement HMAC signing

async function fetchWithCsrf(url: string, options: RequestInit = {}) {
  const csrfToken = getCsrfToken();

  if (!csrfToken) {
    throw new Error('CSRF token not found');
  }

  // Sign the token (or send as-is for simple double-submit)
  const signedToken = await signToken(csrfToken);

  return fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      ...options.headers,
      'X-CSRF-Token': signedToken,
    },
  });
}
```

### 3.4 Custom Header Pattern (SPA-Friendly)

For SPAs using JWT in headers, add a custom header requirement:

```typescript
// All mutations require a custom header that browsers won't add cross-origin
const apiClient = {
  post: (url: string, data: unknown) =>
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // Custom header
      },
      body: JSON.stringify(data),
    }),
};
```

---

## 4. Secure Headers for SPA

### 4.1 Essential Security Headers

Configure these headers on your server (Nginx, Express, Vercel, etc.):

```nginx
# nginx.conf
server {
    # Prevent clickjacking
    add_header X-Frame-Options "DENY" always;

    # Prevent MIME-type sniffing
    add_header X-Content-Type-Options "nosniff" always;

    # Control referrer information
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Enable XSS filter (legacy browsers)
    add_header X-XSS-Protection "1; mode=block" always;

    # Enforce HTTPS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Permissions Policy (formerly Feature-Policy)
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
}
```

### 4.2 Content Security Policy (CSP)

CSP is critical for preventing XSS attacks. Configure based on your needs:

```nginx
# Strict CSP for isolated SPAs
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    font-src 'self';
    connect-src 'self' https://api.yourdomain.com;
    frame-ancestors 'none';
    form-action 'self';
    base-uri 'self';
    upgrade-insecure-requests;
" always;
```

**For React with third-party dependencies:**

```nginx
# CSP with nonce for inline scripts (requires server-side nonce generation)
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self' 'nonce-${NONCE}' 'strict-dynamic';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self' https://api.yourdomain.com wss://ws.yourdomain.com;
" always;
```

### 4.3 Express.js with Helmet

```typescript
// server.ts
import express from 'express';
import helmet from 'helmet';

const app = express();

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.yourdomain.com"],
      frameSrc: ["'none'"],
      frameAncestors: ["'none'"],
    },
  },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  hsts: { maxAge: 31536000, includeSubDomains: true },
}));
```

### 4.4 Subresource Integrity (SRI)

When loading third-party scripts from CDNs, use SRI:

```html
<script
  src="https://cdn.example.com/library.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/ux..."
  crossorigin="anonymous"
></script>
```

**Generate SRI hash:**

```bash
# Generate hash for local file
openssl dgst -sha384 -binary script.js | openssl base64 -A

# Or use online tool: https://www.srihash.org/
```

**Vite configuration for SRI:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { sriPlugin } from 'vite-plugin-sri'; // Third-party plugin

export default defineConfig({
  plugins: [
    sriPlugin({
      algorithm: 'sha384',
    }),
  ],
});
```

---

## 5. Dependency Security

### 5.1 npm audit

Built-in tool for scanning vulnerabilities:

```bash
# Run audit
npm audit

# Get JSON report
npm audit --json

# Fix automatically where possible
npm audit fix

# Force fix (may break things)
npm audit fix --force

# Only check production dependencies
npm audit --omit=dev
```

### 5.2 Integrating with CI/CD

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run npm audit
        run: npm audit --audit-level=high

      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### 5.3 Snyk Integration

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test for vulnerabilities
snyk test

# Monitor project (continuous)
snyk monitor

# Test only production dependencies
snyk test --production
```

### 5.4 Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
    reviewers:
      - "security-team"
    groups:
      development:
        patterns:
          - "@types/*"
          - "eslint*"
          - "typescript"
        update-types:
          - "minor"
          - "patch"
```

### 5.5 Lock File Importance

**Always commit lock files:**
- `package-lock.json` (npm)
- `yarn.lock` (Yarn)
- `pnpm-lock.yaml` (pnpm)
- `bun.lockb` (Bun)

```bash
# Ensure exact versions are installed
npm ci  # NOT npm install

# Verify lock file integrity
npm ci --ignore-scripts  # Also prevents post-install scripts
```

### 5.6 Banned/Risky Packages

Maintain a deny list for known malicious packages:

```json
// package.json
{
  "overrides": {
    "event-stream": "npm:empty-npm-package@*",
    "flatmap-stream": "npm:empty-npm-package@*",
    "colors": "1.4.0"
  }
}
```

---

## 6. Build Security

### 6.1 Environment Variables

**Critical Rule: Never expose secrets in frontend builds**

```bash
# .env.local (NEVER commit)
VITE_API_URL=https://api.example.com
VITE_PUBLIC_KEY=pk_live_xxx  # OK - public key

# .env.production.local (NEVER commit)
# These should NEVER have VITE_ prefix
DATABASE_URL=postgresql://...  # Backend only
API_SECRET_KEY=sk_live_xxx     # Backend only
```

**Vite configuration:**

```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  // Validate that no secrets are exposed
  const forbiddenPatterns = ['SECRET', 'PASSWORD', 'PRIVATE', 'DATABASE'];
  Object.keys(env).forEach(key => {
    if (key.startsWith('VITE_')) {
      forbiddenPatterns.forEach(pattern => {
        if (key.toUpperCase().includes(pattern)) {
          throw new Error(`SECURITY: ${key} may contain secrets and should not be exposed to frontend`);
        }
      });
    }
  });

  return {
    // ... config
  };
});
```

### 6.2 Source Maps in Production

**Disable source maps in production:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    // Disable source maps in production
    sourcemap: false,

    // Or use hidden source maps (for error tracking services)
    // sourcemap: 'hidden',
  },
});
```

**For error tracking (Sentry, etc.), use hidden source maps:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default defineConfig({
  build: {
    sourcemap: true, // Generate but...
  },
  plugins: [
    sentryVitePlugin({
      org: 'your-org',
      project: 'your-project',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        // Upload and then delete from build output
        filesToDeleteAfterUpload: '**/*.map',
      },
    }),
  ],
});
```

### 6.3 Code Minification and Obfuscation

Vite uses esbuild for minification by default:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    minify: 'esbuild', // Default, fast
    // Or use terser for more options
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log
        drop_debugger: true, // Remove debugger statements
      },
      mangle: {
        safari10: true,
      },
    },
  },
});
```

**For additional obfuscation (not security, just obscurity):**

```bash
npm install javascript-obfuscator --save-dev
```

---

## 7. Client-side Input Validation

### 7.1 Zod Schema Validation

```bash
npm install zod
```

```typescript
// schemas/user.ts
import { z } from 'zod';

// Define schema with security-conscious validations
export const userRegistrationSchema = z.object({
  email: z
    .string()
    .email('Invalid email format')
    .max(254, 'Email too long')
    .toLowerCase()
    .trim(),

  password: z
    .string()
    .min(12, 'Password must be at least 12 characters')
    .max(128, 'Password too long')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$/,
      'Password must include uppercase, lowercase, number, and special character'
    ),

  username: z
    .string()
    .min(3, 'Username too short')
    .max(30, 'Username too long')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and hyphens'),

  // Prevent XSS in free-text fields
  bio: z
    .string()
    .max(500, 'Bio too long')
    .optional()
    .transform(val => val ? DOMPurify.sanitize(val, { ALLOWED_TAGS: [] }) : val),
});

export type UserRegistration = z.infer<typeof userRegistrationSchema>;

// Validation function
export function validateUserRegistration(data: unknown): {
  success: boolean;
  data?: UserRegistration;
  errors?: z.ZodError
} {
  const result = userRegistrationSchema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  return { success: false, errors: result.error };
}
```

### 7.2 React Hook Form + Zod

```bash
npm install react-hook-form @hookform/resolvers zod
```

```tsx
// components/RegistrationForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { userRegistrationSchema, type UserRegistration } from '@/schemas/user';

export function RegistrationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserRegistration>({
    resolver: zodResolver(userRegistrationSchema),
    mode: 'onBlur', // Validate on blur for better UX
  });

  const onSubmit = async (data: UserRegistration) => {
    try {
      // Data is already validated and typed
      await registerUser(data);
    } catch (error) {
      // Handle API errors
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          {...register('email')}
        />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register('password')}
        />
        {errors.password && <span role="alert">{errors.password.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}
```

### 7.3 Sanitization with Zod Transform

```typescript
// schemas/content.ts
import { z } from 'zod';
import DOMPurify from 'dompurify';

// Sanitize HTML content while preserving safe tags
const sanitizedHtml = z.string().transform(val =>
  DOMPurify.sanitize(val, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href'],
  })
);

// Strip all HTML (plain text only)
const plainText = z.string().transform(val =>
  DOMPurify.sanitize(val, { ALLOWED_TAGS: [] })
);

// URL validation with sanitization
const safeUrl = z.string().url().refine(url => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}, 'URL must use http or https protocol');

export const articleSchema = z.object({
  title: plainText.pipe(z.string().min(1).max(200)),
  content: sanitizedHtml.pipe(z.string().min(1).max(50000)),
  sourceUrl: safeUrl.optional(),
});
```

### 7.4 Remember: Server-side Validation is Mandatory

Client-side validation is for UX, not security. **Always validate on the server:**

```python
# Backend validation must mirror frontend
from pydantic import BaseModel, EmailStr, constr, validator
import bleach

class UserRegistration(BaseModel):
    email: EmailStr
    password: constr(min_length=12, max_length=128)
    username: constr(min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_-]+$')
    bio: str | None = None

    @validator('bio')
    def sanitize_bio(cls, v):
        if v:
            return bleach.clean(v, tags=[], strip=True)
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Must contain uppercase')
        if not any(c.islower() for c in v):
            raise ValueError('Must contain lowercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Must contain digit')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Must contain special character')
        return v
```

---

## 8. Quick Reference Checklist

### Token Storage
- [ ] Access token stored in memory only (React state/context)
- [ ] Refresh token in httpOnly, secure, SameSite=strict cookie
- [ ] No tokens in localStorage or sessionStorage
- [ ] Token refresh mechanism implemented
- [ ] Consider BFF pattern for high-security applications

### XSS Prevention
- [ ] Never use `dangerouslySetInnerHTML` without DOMPurify
- [ ] Validate all URLs before rendering in href
- [ ] No `eval()`, `new Function()`, or dynamic script injection
- [ ] DOMPurify configured with minimal allowed tags
- [ ] Keep DOMPurify updated

### CSRF Protection
- [ ] SameSite cookie attribute set (strict or lax)
- [ ] Double submit cookie pattern if using cookie auth
- [ ] Custom header requirement for mutations
- [ ] CSRF tokens are cryptographically signed

### Security Headers
- [ ] Content-Security-Policy configured
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Strict-Transport-Security (HSTS) enabled
- [ ] SRI for third-party scripts

### Dependencies
- [ ] npm audit runs in CI/CD
- [ ] Snyk or similar tool integrated
- [ ] Dependabot enabled
- [ ] Lock files committed
- [ ] No known malicious packages

### Build Security
- [ ] No secrets in VITE_* environment variables
- [ ] Source maps disabled or hidden in production
- [ ] console.log/debugger removed in production
- [ ] .env files in .gitignore

### Input Validation
- [ ] Zod schemas for all form inputs
- [ ] HTML sanitization for rich text
- [ ] URL validation and sanitization
- [ ] Server-side validation mirrors client-side

---

## Sources and Further Reading

### Token Storage
- [JWT Storage in React: Local Storage vs Cookies Security Battle](https://cybersierra.co/blog/react-jwt-storage-guide/)
- [LocalStorage vs Cookies: Storing JWT Tokens Securely](https://dev.to/cotter/localstorage-vs-cookies-all-you-need-to-know-about-storing-jwt-tokens-securely-in-the-front-end-15id)
- [The Backend for Frontend Pattern (BFF) | Auth0](https://auth0.com/blog/the-backend-for-frontend-pattern-bff/)
- [Backend For Frontend (BFF) Security Framework | Duende Software](https://docs.duendesoftware.com/bff/)

### XSS Prevention
- [Preventing XSS in React: dangerouslySetInnerHTML](https://pragmaticwebsecurity.com/articles/spasecurity/react-xss-part2)
- [DOMPurify - GitHub](https://github.com/cure53/DOMPurify)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [React XSS Guide: Understanding and Prevention](https://www.stackhawk.com/blog/react-xss-guide-examples-and-prevention/)

### CSRF Protection
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN: Cross-site request forgery (CSRF)](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/CSRF)
- [SameSite Cookies | OWASP](https://owasp.org/www-community/SameSite)
- [React CSRF Protection: 10 Best Practices](https://codebrahma.com/react-csrf-protection-10-best-practices/)

### Security Headers
- [React Content Security Policy Guide | StackHawk](https://www.stackhawk.com/blog/react-content-security-policy-guide-what-it-is-and-how-to-enable-it/)
- [Deploying CSP in Single Page Applications | Auth0](https://auth0.com/blog/deploying-csp-in-spa/)
- [MDN: Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity)
- [5 Essential Security Headers for Modern Frontend Devs](https://dev.to/olabima_/5-essential-security-headers-for-modern-frontend-devs-nextjs-angular-vue-3icf)

### Dependency Security
- [npm Security: The Complete Guide](https://blog.cyberdesserts.com/npm-security-vulnerabilities/)
- [Snyk for JavaScript/Node.js Developers](https://docs.snyk.io/scan-using-snyk/supported-languages-and-frameworks/javascript/snyk-for-javascript-node.js-developers)
- [GitHub Dependabot Security Updates](https://docs.github.com/en/code-security/dependabot)

### Build Security
- [Vite Environment Variables and Modes](https://vite.dev/guide/env-and-mode)
- [Are You Leaking Secrets Through React Source Maps?](https://cybersierra.co/blog/secure-react-source-maps/)
- [Protect Your React.js Source Code In Production Build](https://izhan-yameen25.medium.com/protect-your-react-js-source-code-in-production-build-e6b408003817)

### Input Validation
- [Yup vs Zod: Choosing the Right Validation Library](https://betterstack.com/community/guides/scaling-nodejs/yup-vs-zod/)
- [How to Validate Forms with Zod and React-Hook-Form](https://www.freecodecamp.org/news/react-form-validation-zod-react-hook-form/)
- [React Security Best Practices 2025 | Corgea](https://corgea.com/Learn/react-security-best-practices-2025)

---

**Document Owner**: Security Team
**Review Cycle**: Quarterly
**Next Review**: 2026-04-28
