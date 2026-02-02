# Cloudflare Setup Guide for ARSAKA Projects

## Overview

Panduan implementasi Cloudflare untuk ARSAKA infrastructure yang berjalan di VPS.

**VPS:** 72.61.209.224
**Services:**
- ARSAKA_MANTRA (Backend :8002, Frontend :3001)
- ARSAKA_PUGUH (Backend :8000, Frontend :3000)
- ARSAKA_TUTUR (Backend :8003)
- Admin UIs: Nomad :4646, Consul :8500, RabbitMQ :15672, Traefik :8080

---

## Implementation Phases

### Phase 1: Essential (Priority: HIGH)

| Feature | Effort | Impact |
|---------|--------|--------|
| DNS + Proxy | 30 min | Hide IP, basic protection |
| SSL/TLS (Full Strict) | 15 min | HTTPS everywhere |
| Cloudflare Tunnel | 1 hour | Eliminate exposed ports |
| Access untuk Admin UIs | 1 hour | Secure Nomad/Consul/RabbitMQ |

### Phase 2: Security Hardening

| Feature | Effort | Impact |
|---------|--------|--------|
| WAF Rules | 30 min | Block attacks |
| Rate Limiting | 30 min | API protection |
| Bot Management | 15 min | Block bad bots |

### Phase 3: Performance

| Feature | Effort | Impact |
|---------|--------|--------|
| Caching Rules | 30 min | Faster frontend |
| Pages (frontends) | 2 hours | Offload VPS |

### Phase 4: Future Scale

| Feature | When | Why |
|---------|------|-----|
| Load Balancing | Multiple VPS | Failover |
| R2 Storage | File uploads needed | Cost effective |
| Workers | Complex API logic | Edge computing |

---

## Feature Details

### 1. DNS + Proxy (FREE)

**Benefit:**
- IP VPS tersembunyi dari publik
- Automatic failover jika punya backup server
- Anycast DNS (fast resolution globally)

**Setup:**
1. Add domain ke Cloudflare
2. Update nameservers di registrar
3. Enable proxy (orange cloud) untuk A records

### 2. SSL/TLS Certificates (FREE)

**Modes:**
- Flexible: CF→User HTTPS, CF→VPS HTTP
- Full: CF→User HTTPS, CF→VPS HTTPS (self-signed OK)
- Full (Strict): End-to-end dengan valid cert ✓ RECOMMENDED

**Setup:**
1. SSL/TLS → Overview → Full (Strict)
2. Edge Certificates → Always Use HTTPS: ON
3. Edge Certificates → Automatic HTTPS Rewrites: ON

### 3. DDoS Protection (FREE)

Otomatis aktif ketika proxy enabled. Proteksi Layer 3/4/7.

### 4. WAF - Web Application Firewall (FREE tier available)

**Recommended Rules:**
```
Block:
├── SQL Injection attempts
├── XSS attacks
├── Path traversal
├── Known bad bots
└── Suspicious user agents

Custom Rules:
├── Block requests dengan payload > 1MB ke API
├── Block non-JSON content-type ke POST /api/*
└── Challenge requests dari high-risk countries
```

**Setup:**
1. Security → WAF → Managed Rules → Enable
2. Security → WAF → Custom Rules → Add rules

### 5. Cloudflare Tunnel (FREE) ⭐ RECOMMENDED

**Benefit:**
- No open ports di VPS
- IP completely hidden
- Outbound connection only (more secure)
- Replace/complement Traefik

**Installation:**
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create atlas

# Note the tunnel ID from output
```

**Configuration:**
```yaml
# /etc/cloudflared/config.yml
tunnel: atlas
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  # MANTRA
  - hostname: mantra.yourdomain.com
    service: http://localhost:3001
  - hostname: api.mantra.yourdomain.com
    service: http://localhost:8002

  # PUGUH
  - hostname: puguh.yourdomain.com
    service: http://localhost:3000
  - hostname: api.puguh.yourdomain.com
    service: http://localhost:8000

  # TUTUR
  - hostname: tutur.yourdomain.com
    service: http://localhost:8003

  # Admin UIs (protect dengan Access)
  - hostname: nomad.yourdomain.com
    service: http://localhost:4646
  - hostname: consul.yourdomain.com
    service: http://localhost:8500
  - hostname: rabbitmq.yourdomain.com
    service: http://localhost:15672
  - hostname: traefik.yourdomain.com
    service: http://localhost:8080

  # Catch-all
  - service: http_status:404
```

**Route DNS:**
```bash
cloudflared tunnel route dns atlas mantra.yourdomain.com
cloudflared tunnel route dns atlas api.mantra.yourdomain.com
cloudflared tunnel route dns atlas puguh.yourdomain.com
cloudflared tunnel route dns atlas api.puguh.yourdomain.com
cloudflared tunnel route dns atlas tutur.yourdomain.com
cloudflared tunnel route dns atlas nomad.yourdomain.com
cloudflared tunnel route dns atlas consul.yourdomain.com
cloudflared tunnel route dns atlas rabbitmq.yourdomain.com
```

**Run as Service:**
```bash
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared
systemctl status cloudflared
```

### 6. Cloudflare Access / Zero Trust (FREE for 50 users)

**Benefit:**
- Protect admin UIs tanpa VPN
- SSO dengan Google/GitHub/Email OTP
- Audit log

**Protected Services:**
- Nomad UI
- Consul UI
- RabbitMQ Management
- Traefik Dashboard
- Meilisearch Dashboard

**Setup:**
1. Zero Trust Dashboard → Access → Applications
2. Add Application → Self-hosted
3. Configure:
   - Application name: Nomad Dashboard
   - Session Duration: 24 hours
   - Application domain: nomad.yourdomain.com
4. Add Policy:
   - Policy name: Allow Team
   - Action: Allow
   - Include: Emails ending in @yourcompany.com
   - OR Include: GitHub organization

### 7. Rate Limiting (FREE tier: 1 rule)

**Recommended Rules:**
```
/api/v1/ai/chat     → 30 req/min per IP
/api/v1/ai/hints    → 60 req/min per IP
/api/v1/search/*    → 100 req/min per IP
/api/v1/validation/* → 20 req/min per IP
Global              → 1000 req/min per IP
```

**Setup:**
1. Security → WAF → Rate limiting rules
2. Add rule dengan expression dan threshold

### 8. Caching (FREE)

**Static Assets:**
```
Cache Level: Aggressive
Edge TTL: 1 month
Browser TTL: 1 week

Applies to:
- *.js, *.css
- *.woff2, *.ttf
- *.png, *.jpg, *.svg, *.ico
```

**API Responses:**
```
Cacheable (public data):
- GET /api/v1/decisions → 5 min
- GET /api/v1/matrix → 5 min

Never Cache:
- POST /*
- Authenticated endpoints
- /api/v1/ai/*
```

**Page Rules:**
```
Rule 1: mantra.yourdomain.com/assets/*
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week

Rule 2: api.*.yourdomain.com/*
  - Cache Level: Bypass
  - Security Level: High
```

### 9. Cloudflare Pages (FREE)

**Benefit:**
- Host frontends di edge (global CDN)
- VPS fokus untuk backends only
- Automatic deploys dari GitHub
- Preview per branch

**Migration Steps:**
1. Connect GitHub repo ke Pages
2. Configure build:
   - Build command: `npm run build`
   - Output directory: `dist`
3. Environment variables:
   ```
   VITE_API_URL=https://api.mantra.yourdomain.com
   ```
4. Deploy dan update DNS

### 10. R2 Object Storage (FREE tier: 10GB)

**Use Cases:**
- Document uploads
- Chat attachments
- Backup files
- Large static assets

**Benefit:**
- S3-compatible API
- Zero egress fees
- Integrate dengan Workers

---

## Target Architecture

```
                    ┌─────────────────────────────────────┐
                    │         CLOUDFLARE EDGE             │
                    │                                     │
                    │  ┌─────────┐  ┌─────────────────┐  │
Internet ──────────►│  │   WAF   │  │  Rate Limiting  │  │
                    │  └────┬────┘  └────────┬────────┘  │
                    │       │                │           │
                    │  ┌────▼────────────────▼────┐      │
                    │  │      Cloudflare Tunnel    │      │
                    │  └────────────┬─────────────┘      │
                    │               │                    │
                    │  ┌────────────▼─────────────┐      │
                    │  │    Cloudflare Access     │      │
                    │  │    (Admin UIs only)      │      │
                    │  └────────────┬─────────────┘      │
                    └───────────────┼─────────────────────┘
                                    │
                    ┌───────────────▼─────────────────────┐
                    │         VPS (NO OPEN PORTS)         │
                    │                                     │
                    │  cloudflared ◄── outbound only      │
                    │       │                             │
                    │  ┌────▼────┐                        │
                    │  │ Traefik │ (internal routing)     │
                    │  └────┬────┘                        │
                    │       │                             │
                    │  ┌────▼─────────────────────────┐   │
                    │  │  MANTRA  │  PUGUH  │  TUTUR  │   │
                    │  └──────────────────────────────┘   │
                    │                                     │
                    │  ┌──────────────────────────────┐   │
                    │  │  Nomad │ Consul │ RabbitMQ   │   │
                    │  │  (Access-protected)          │   │
                    │  └──────────────────────────────┘   │
                    └─────────────────────────────────────┘
```

---

## Checklist

### Phase 1: Essential
- [ ] Domain added to Cloudflare
- [ ] Nameservers updated
- [ ] SSL/TLS set to Full (Strict)
- [ ] cloudflared installed on VPS
- [ ] Tunnel created and configured
- [ ] DNS routes added for all services
- [ ] cloudflared running as service
- [ ] Access policies for admin UIs
- [ ] Test all endpoints

### Phase 2: Security
- [ ] WAF managed rules enabled
- [ ] Custom WAF rules added
- [ ] Rate limiting rules configured
- [ ] Bot fight mode enabled
- [ ] Security level set to High for APIs

### Phase 3: Performance
- [ ] Page rules for caching
- [ ] Browser TTL configured
- [ ] (Optional) Frontends migrated to Pages

### Post-Setup
- [ ] Firewall: Close ports 80, 443, 8080, 4646, 8500, 15672
- [ ] Keep only SSH (22) open or use Tunnel for SSH too
- [ ] Monitor Cloudflare Analytics
- [ ] Set up alerts

---

## Useful Commands

```bash
# Tunnel status
cloudflared tunnel info atlas

# List tunnels
cloudflared tunnel list

# Run tunnel manually (debug)
cloudflared tunnel run atlas

# View logs
journalctl -u cloudflared -f

# Test connectivity
curl -I https://mantra.yourdomain.com
```

---

## Cost Summary

| Feature | Free Tier | Paid |
|---------|-----------|------|
| DNS + Proxy | Unlimited | - |
| SSL/TLS | Unlimited | - |
| DDoS Protection | Unlimited | - |
| Tunnel | Unlimited | - |
| Access | 50 users | $3/user/month |
| WAF Managed | 5 rules | Pro $20/month |
| Rate Limiting | 1 rule | Pro: 10 rules |
| Pages | Unlimited | - |
| R2 | 10GB storage | $0.015/GB |
| Workers | 100k req/day | $5/month |

**Recommended:** Start dengan FREE tier, upgrade ke Pro ($20/month) jika butuh lebih banyak WAF dan Rate Limiting rules.

---

## References

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Cloudflare Access Docs](https://developers.cloudflare.com/cloudflare-one/policies/access/)
- [WAF Managed Rules](https://developers.cloudflare.com/waf/managed-rules/)
- [Pages Documentation](https://developers.cloudflare.com/pages/)
- [R2 Documentation](https://developers.cloudflare.com/r2/)
