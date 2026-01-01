# Enterprise Hospitality Platform - Development Decisions

> Keputusan yang sudah disetujui untuk pengembangan **Enterprise Hospitality Platform**.
>
> **Last Updated**: 2025-12-07 (v12 - Logging & i18n)
>
> **Total Decisions**: 245
>
> **See Also**: [PLATFORM_VISION.md](./PLATFORM_VISION.md) - Complete platform vision & architecture

---

## Platform Scope

Platform enterprise yang terintegrasi untuk industri hospitality, mencakup:

| # | Application | Target Users | Status |
|---|-------------|--------------|--------|
| 1 | **Digital Signage (CMS)** | Marketing | ✅ Done |
| 2 | **PMS (Hotel Operations)** | Front Office | 🔄 Planning |
| 3 | **Guest App** | Tamu, Member Loyalty | 📋 Planned |
| 4 | **POS (F&B)** | Outlets, Restaurant | 📋 Planned |
| 5 | **Online Menu** | Guests | 📋 Planned |
| 6 | **HRM & Payroll** | HR, Finance | 📋 Planned |
| 7 | **Procurement** | Purchasing | 📋 Planned |
| 8 | **Supplier Portal** | Vendors | 📋 Planned |
| 9 | **Inventory** | Warehouse | 📋 Planned |
| 10 | **Asset Management** | Engineering | 📋 Planned |
| 11 | **Accounting** | Finance | 📋 Planned |

**Key Concept:**
- **Single Backend** (FastAPI) serving all applications
- **Database-per-Tenant** - Each organization gets own database
- **Unified User Management** - Employee, Guest, Supplier all in one `users` table
- **Cross-Application Integration** - All modules share data seamlessly

---

## Enterprise Technology Stack Summary

> Final approved stack - designed for 500+ tenants, start small scale big.

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Database** | TimescaleDB | PostgreSQL + time-series extension |
| **Connection Pool** | PgBouncer | Handle 10,000+ connections |
| **Cache** | Redis Cluster | Sessions, cache, pub/sub, locks |
| **Message Queue** | RabbitMQ | Events, async tasks |
| **Background Jobs** | Celery + RabbitMQ | Workers + scheduled tasks |
| **File Storage** | Cloudflare R2 | S3-compatible, zero egress, CDN |
| **Real-time** | Centrifugo | WebSocket server, scalable |
| **Search** | Meilisearch | Full-text search |
| **Load Balancer** | Traefik | Reverse proxy, SSL, routing |
| **Metrics** | Prometheus | Metrics collection |
| **Dashboards** | Grafana | Visualization |
| **Logs** | Loki | Log aggregation |
| **Tracing** | Jaeger | Distributed tracing |
| **Errors** | Sentry | Error tracking |
| **Containers** | Docker Swarm | Container orchestration |

**Scaling Path:**
```
Stage 1: 1 VPS (4 vCPU, 8GB)    → 0-30 tenants    → $50-100/month
Stage 2: 1 VPS (8 vCPU, 16GB)   → 30-100 tenants  → $150-300/month
Stage 3: Separate servers        → 100-300 tenants → $500-800/month
Stage 4: Full cluster            → 300-500+ tenants→ $2,000-5,000/month
```

---

## Executive Summary (Database Analysis)

Berdasarkan analisis komprehensif dengan multi-agent terhadap database PMS lama (Firebird), ditemukan:

| Kategori | Masalah Ditemukan | Grade Lama |
|----------|-------------------|------------|
| Database Design | 15 kategori utama | D (35/100) |
| Security | 17 vulnerabilities (6 Critical) | F (20/100) |
| Performance | 15 critical issues | D (30/100) |
| Architecture | 18 weaknesses | D (37/100) |
| Missing Features | 35+ features | F (25/100) |

**Overall Grade: D- (Requires Complete Rewrite)**

---

## Approved Decisions

### A. Architecture (1-10)

1. **Web-based application** - Bukan desktop, agar bisa diakses dari device apapun (browser, tablet, mobile)

2. **Monolith-first, microservices-ready** - Mulai dengan monolith yang modular, bisa dipecah ke microservices nanti ketika scale

3. **Multi-application platform** - Backend besar yang bisa support banyak aplikasi (PMS, Accounting, Signage, dll)

4. **Business logic di application layer** - TIDAK di stored procedures/triggers, agar mudah test, debug, dan maintain

5. **Clean Architecture** - Separation of concerns: Routes → Use Cases → Repositories → Database

6. **REST API first** - Semua fitur bisa diakses via API untuk integrasi

7. **Event-driven architecture** - Publish events saat terjadi perubahan (booking created, checkout completed) untuk webhook dan real-time updates

8. **Horizontal scalability** - Design untuk bisa scale out (multiple instances), bukan hanya scale up

9. **Real-time support dengan WebSocket** - Untuk housekeeping status, room availability, notifications

10. **Background job processing** - Heavy tasks (reports, bulk operations, night audit) dijalankan async dengan Celery/RQ

---

### B. Tech Stack - Core (11-18)

11. **Backend: Python + FastAPI** - Async, modern, type-safe, auto-generate API docs

12. **Database: TimescaleDB (PostgreSQL + Extension)** - PostgreSQL dengan time-series extension untuk:
    - Auto time-partitioning (hypertables)
    - Data compression (90%+ space savings)
    - Continuous aggregates (real-time analytics)
    - Retention policies (auto-delete old data)
    - ACID compliant, enterprise-grade

13. **Frontend: React + Vite + TypeScript** - Modern, fast, type-safe

14. **State Management: TanStack Query + Zustand** - Server state & UI state terpisah

15. **UI: Tailwind + shadcn/ui** - Flexible, modern, accessible

16. **Redis Cluster untuk caching & session** - Cache, sessions, pub/sub, distributed locks, rate limiting

17. **Background jobs dengan Celery + RabbitMQ** - Report generation, heavy tasks, scheduled jobs, event-driven processing

18. **Docker + Kubernetes deployment** - Consistent environment, orchestration, auto-scaling

---

### C. Database Design - Core (19-35)

19. **Soft delete untuk semua entity** - Data tidak dihapus permanen, menggunakan pattern lengkap:
    - `is_deleted BOOLEAN DEFAULT FALSE NOT NULL` - Flag untuk query filtering
    - `deleted_at TIMESTAMP WITH TIME ZONE` - Timestamp kapan dihapus
    - `deleted_by_id INTEGER REFERENCES users(id)` - Siapa yang menghapus

20. **Audit trail lengkap** - Setiap tabel wajib punya:
    - `created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`
    - `created_by_id INTEGER REFERENCES users(id)`
    - `updated_at TIMESTAMP WITH TIME ZONE`
    - `updated_by_id INTEGER REFERENCES users(id)`
    - `is_deleted BOOLEAN DEFAULT FALSE NOT NULL`
    - `deleted_at TIMESTAMP WITH TIME ZONE`
    - `deleted_by_id INTEGER REFERENCES users(id)`

21. **Timezone-aware timestamps** - Semua timestamp pakai `WITH TIME ZONE`, simpan dalam UTC, convert di application layer

22. **UTF-8 encoding** - Support semua bahasa (Asia, Arab, emoji, dll) - BUKAN WIN1251

23. **External file storage** - File/gambar disimpan di S3/MinIO, database hanya simpan URL (tidak ada BLOB di database)

24. **Multi-tenancy dengan organization_id** - Satu database untuk banyak hotel, isolasi data per organization dengan Row-Level Security (RLS)

25. **DECIMAL/NUMERIC untuk uang** - Semua kolom harga/nominal pakai `DECIMAL(18,4)` agar tidak ada floating-point rounding error dan cukup untuk high-denomination currencies (IDR, VND)

26. **Optimistic locking dengan version column** - Setiap tabel yang bisa di-edit concurrent wajib punya kolom `version INTEGER` untuk mencegah lost updates

27. **UUID untuk external-facing IDs** - Primary key tetap integer untuk performance, tapi expose UUID ke API untuk security (tidak predictable)

28. **Consistent naming conventions**:
    - Tables: plural, snake_case (`users`, `room_types`, `reservations`)
    - Columns: snake_case (`created_at`, `is_active`)
    - Foreign keys: `{table}_id` (`user_id`, `organization_id`)
    - Booleans: prefix `is_`, `has_`, `can_` (`is_active`, `has_breakfast`)
    - Timestamps: suffix `_at` (`created_at`, `checked_in_at`)

29. **NOT NULL by default** - Semua kolom NOT NULL kecuali memang optional. Nullable harus explicit dan ada alasan

30. **CHECK constraints untuk validasi** - Validasi di database level:
    - `CHECK (total >= 0)` untuk nominal
    - `CHECK (check_out_at >= check_in_at)` untuk dates
    - `CHECK (email ~* '^[A-Za-z0-9._%+-]+@')` untuk format

31. **ENUM types untuk status** - Status pakai PostgreSQL ENUM, bukan CHAR(1) magic values:
    ```sql
    CREATE TYPE reservation_status AS ENUM ('confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show');
    ```

32. **Data partitioning untuk tabel besar** - Tabel dengan data bertahun-tahun (transactions, logs) di-partition by year/month

33. **Foreign key indexes wajib** - Setiap FK column harus ada index untuk performance JOIN

34. **Covering indexes untuk frequent queries** - Index dengan INCLUDE untuk query yang sering dipakai

35. **Full-text search dengan GIN index** - Untuk guest name search, company search, dll

---

### C. Database Design - Advanced (36-45)

36. **Lookup tables untuk reference data** - Status codes, room types, rate codes pakai lookup table dengan deskripsi jelas

37. **Support external integration** - Setiap entity yang bisa di-sync dengan sistem luar wajib punya:
    - `external_id VARCHAR(100)`
    - `channel_code VARCHAR(50)`
    - `last_synced_at TIMESTAMP WITH TIME ZONE`

38. **Database documentation wajib** - Setiap tabel dan kolom penting wajib punya `COMMENT ON`

39. **No computed columns di database** - Kalkulasi dilakukan di application layer, bukan `COMPUTED BY` di database

40. **ON DELETE RESTRICT by default** - Tidak CASCADE delete, explicit handling di application

41. **Materialized views untuk reports** - Pre-calculate heavy aggregations, refresh nightly

42. **Temporal tables untuk historical data** - Track perubahan rate, price, dengan `valid_from`, `valid_to`

43. **JSON/JSONB untuk flexible data** - Guest preferences, custom fields, metadata pakai JSONB

44. **Connection pooling dengan PgBouncer** - Manage database connections efficiently

45. **Read replicas untuk reporting** - Heavy reports query ke replica, tidak ganggu production

---

### D. Security - Critical (46-55)

46. **Password hashing dengan Argon2id/bcrypt** - Semua password di-hash dengan cost factor 12+, TIDAK PERNAH plaintext

47. **Tidak simpan credit card di database** - Pakai payment gateway (Midtrans, Xendit, Stripe), hanya simpan token/last4 digits (PCI-DSS compliance)

48. **Multi-Factor Authentication (MFA/2FA)** - TOTP untuk admin dan user dengan akses sensitif:
    ```sql
    CREATE TABLE mfa_tokens (
        user_id INTEGER REFERENCES users(id),
        secret_key VARCHAR(255) ENCRYPTED,
        backup_codes TEXT[],
        is_enabled BOOLEAN DEFAULT FALSE
    );
    ```

49. **Session management lengkap**:
    - Session table dengan device info, IP address, user agent
    - Session expiration (idle timeout 30 min, absolute timeout 24 hours)
    - Concurrent session limit (max 3 per user)
    - "Logout all devices" capability

50. **Rate limiting dengan tracking**:
    - 5 failed login → 15 min lockout
    - 10 failed from same IP → 1 hour IP block
    - 20 failed → permanent lock (manual unlock)
    - Track di database untuk audit

51. **Row-Level Security (RLS)** - User hanya bisa akses data organization mereka sendiri, enforced di database level

52. **Column-level encryption untuk sensitive data** - Passport numbers, personal IDs dienkripsi dengan pgcrypto

53. **Blacklist/DNR (Do Not Rent) system** - Block guest bermasalah dengan alasan, periode, severity level, auto-check saat booking

54. **Security audit logging** - Log semua security events:
    - Login success/failure
    - Permission changes
    - Sensitive data access
    - Admin actions

55. **Input validation di semua layer** - Validasi di frontend, backend, dan database (CHECK constraints)

---

### D. Security - Standard (56-62)

56. **JWT authentication** - Stateless, scalable, dengan refresh token rotation

57. **RBAC (Role-Based Access Control)** - Permission berbasis role dengan hierarchy:
    - SUPER_ADMIN → ADMIN → MANAGER → STAFF → VIEWER

58. **API rate limiting** - Prevent abuse dengan rate limits per endpoint

59. **HTTPS everywhere** - Semua traffic encrypted, no HTTP

60. **Secure headers** - CSP, X-Frame-Options, X-Content-Type-Options, dll

61. **Backup encryption** - Semua backup di-encrypt dengan AES-256

62. **Data retention policies** - Auto-purge data sesuai GDPR requirements:
    - Guest PII: 7 years (financial records)
    - Session logs: 90 days
    - Audit logs: 7 years

---

### E. Performance (63-75)

63. **Minimal triggers** - Trigger HANYA untuk:
    - `updated_at` timestamp update
    - Audit trail logging
    - Enforcing integrity yang tidak bisa via constraint

64. **No business logic in triggers** - Semua business logic di application layer

65. **Proper indexing strategy** - Target 2-3 indexes per table:
    - Primary key (automatic)
    - Foreign keys (all)
    - Frequent WHERE clauses
    - ORDER BY columns

66. **Avoid SELECT *** - Query hanya kolom yang dibutuhkan

67. **Pagination untuk semua list endpoints** - Limit default 50, max 100

68. **Set-based operations** - Tidak row-by-row processing (no cursors untuk bulk ops)

69. **Caching strategy dengan Redis**:
    - Room availability: 5 min TTL
    - Rate plans: 1 hour TTL
    - Static data: 24 hour TTL

70. **Real-time availability cache** - Availability di-cache dan update real-time via pub/sub

71. **Async processing untuk heavy tasks** - Night audit, bulk operations, report generation

72. **Database query optimization** - Explain analyze semua slow queries, target < 100ms

73. **Narrow tables** - Split wide tables (max 30-40 columns), hindari 186-column monster

74. **Bulk operations support** - Batch insert/update untuk performance

75. **CDN untuk static assets** - Images, documents via CDN, bukan direct dari server

---

### F. Features - Guest Experience (76-85)

76. **Online check-in/out** - Guest bisa check-in online sebelum arrival, skip antrian, langsung ambil kunci

77. **Digital registration card** - E-signature, scan ID, tanpa form kertas

78. **Guest self-service portal** - Guest bisa:
    - Lihat booking details
    - Download invoice/receipt
    - Request amenities
    - Submit preferences
    - View loyalty points

79. **Guest mobile app support** - API mobile-friendly untuk:
    - Mobile room key
    - In-room service ordering
    - Real-time notifications
    - Chat with front desk

80. **Guest preference profile (JSONB)** - Simpan preferensi lengkap:
    - Room preferences (floor, view, bed type, pillow)
    - Service preferences (DND, turndown, newspaper)
    - Dietary restrictions
    - Accessibility needs

81. **Loyalty program management**:
    - Points accumulation rules
    - Tier progression (Bronze, Silver, Gold, Platinum)
    - Redemption tracking
    - Partner integrations

82. **Guest feedback/NPS system** - Kirim survey post-checkout, track NPS score, respond to feedback, sentiment analysis

83. **Multi-language support** - UI dan communications dalam multiple languages

84. **Multi-currency handling** - Display dan payment dalam currency pilihan guest

85. **Personalized communications** - Email/SMS templates dengan merge fields dari guest profile

---

### F. Features - Operations (86-95)

86. **Real-time housekeeping mobile app** - HK staff bisa:
    - Receive task push notifications
    - Update room status real-time
    - Upload cleaning photos
    - Report maintenance issues

87. **Maintenance request/work order system**:
    - Priority levels (urgent, high, medium, low)
    - SLA tracking
    - Assignment to technicians
    - Completion photos
    - Cost tracking

88. **Task/ticket system** - Track semua operational tasks:
    - Guest requests
    - Internal tasks
    - Follow-up items
    - Lost & found

89. **Staff scheduling optimization** - Shift management, swap requests, labor forecasting

90. **Inventory management with alerts** - Track amenities, supplies dengan reorder alerts

91. **Approval workflow** - Perubahan penting perlu approval:
    - Rate changes > X%
    - Discounts > Y%
    - Void transactions
    - Workflow: Draft → Review → Approve

92. **Webhook support** - Notify external systems via HTTP callback saat events terjadi

93. **Flexible tagging system** - Guest, reservasi, company bisa di-tag dinamis (VIP, Corporate, Repeat)

94. **Favorites/Bookmark** - User bisa bookmark frequent guests, reports, rooms

95. **Search history & autocomplete** - Recent searches, suggestions untuk UX lebih baik

---

### F. Features - Revenue Management (96-105)

96. **Dynamic pricing engine** - AI-driven pricing berdasarkan:
    - Demand forecasting
    - Competitor rates
    - Historical patterns
    - Events/seasonality

97. **Yield management system**:
    - Overbooking optimization
    - Length-of-stay restrictions (min/max)
    - CTA/CTD controls
    - Advance booking limits

98. **Rate restrictions lengkap**:
    - Min stay, max stay
    - CTA (close to arrival)
    - CTD (close to departure)
    - Advance booking min/max
    - Non-refundable options

99. **A/B testing untuk rates** - Test different rates/packages, measure conversion

100. **Competitor rate tracking** - Monitor competitor prices, alerts for price changes

101. **Demand forecasting** - Predict occupancy 30-90 days out untuk planning

102. **Package builder** - Create dynamic packages (room + services + meals) dengan ROI tracking

103. **Scheduled report delivery** - GM/Owner subscribe daily/weekly reports via email

104. **Custom fields per hotel** - EAV pattern atau JSONB untuk hotel-specific fields

105. **Analytics dashboard** - Real-time KPIs:
     - RevPAR (Revenue Per Available Room)
     - ADR (Average Daily Rate)
     - Occupancy %
     - Market penetration
     - Conversion rates

---

### F. Features - Distribution (106-112)

106. **Channel manager integration** - Single interface untuk manage:
     - Booking.com
     - Expedia
     - Agoda
     - Airbnb
     - Hotels.com

107. **OTA connectivity (multiple)** - API integrations dengan major OTAs

108. **Website booking engine** - Direct booking dengan:
     - Rate comparison
     - Conversion tracking
     - Abandoned booking recovery

109. **Metasearch integration** - Connect ke:
     - Google Hotel Ads
     - Trivago
     - Kayak
     - TripAdvisor

110. **GDS connectivity** - Untuk corporate travel (Amadeus, Sabre, Galileo)

111. **Payment gateway integration** - Multiple gateways:
     - Midtrans
     - Xendit
     - Stripe
     - Local bank integrations

112. **Accounting system sync** - Real-time sync dengan ERP/accounting software

---

### F. Features - Integration (113-120)

113. **POS integration (unified)** - Sync dengan F&B, spa, minibar POS systems

114. **CRM integration** - Sync guest data dengan Salesforce, HubSpot, dll

115. **IoT device integration**:
     - Smart locks (mobile keys)
     - Thermostats
     - Room occupancy sensors
     - Energy management

116. **GDPR consent management** - Track consent untuk:
     - Marketing communications
     - Data retention
     - Third-party sharing
     - With opt-in/opt-out controls

117. **Data warehouse untuk analytics** - Separate analytical database untuk complex queries

118. **API documentation (OpenAPI/Swagger)** - Auto-generated, always up-to-date

119. **Predictive analytics** - ML models untuk:
     - No-show prediction
     - Churn risk
     - Upsell opportunities
     - Length of stay prediction

120. **Scheduled jobs management** - Night audit, report generation, data cleanup, rate updates

---

### G. Guest App & Loyalty (121-130)

121. **Unified users table** - Semua tipe user (employee, guest, supplier) dalam satu tabel `users` dengan `user_type` discriminator

122. **Guest profile dengan preferences (JSONB)** - Flexible storage untuk preferensi guest (room type, pillow, dietary, etc.)

123. **Loyalty tier system** - Bronze → Silver → Gold → Platinum → Diamond dengan benefits berbeda tiap tier

124. **Points earning rules** - Configurable points per USD spent (room, F&B, spa, etc.)

125. **Points redemption** - Redeem untuk room nights, upgrades, F&B credits, amenities

126. **Tier qualification tracking** - Track points/stays untuk tier progression

127. **Member benefits engine** - Auto-apply benefits berdasarkan tier saat booking/check-in

128. **Digital membership card** - QR code untuk scan di outlet

129. **Partner integration support** - External loyalty program connection (airline miles, etc.)

130. **Guest app notifications** - Push notifications untuk offers, booking confirmations, points earned

---

### H. HRM & Payroll (131-140)

131. **Employee master data** - Extended employee profile (KTP, NPWP, BPJS, bank account)

132. **Organization structure** - Department → Position → Grade hierarchy

133. **Employee grading system** - Grade 1-9 dengan salary range dan benefits per grade

134. **Attendance management** - Clock in/out via mobile/web dengan GPS location

135. **Shift scheduling** - Flexible shift assignment dengan swap request

136. **Leave management** - Annual leave, sick leave, cuti besar dengan approval workflow

137. **Payroll calculation** - Auto-calculate gaji pokok + tunjangan - potongan (BPJS, PPh 21)

138. **Payslip generation** - Digital payslip dengan breakdown detail

139. **Bank integration** - Bulk transfer to employee bank accounts

140. **Performance management** - KPI tracking, performance review, 360 feedback

---

### I. Procurement & Supplier (141-150)

141. **Supplier database** - Vendor master dengan rating, payment terms, credit limit

142. **Supplier portal access** - Supplier bisa login, manage catalog, receive PO, submit invoice

143. **Supplier's own employees** - Supplier bisa add staff mereka (sales rep, finance, logistics)

144. **Purchase requisition (PR)** - Department request dengan budget check dan approval

145. **Purchase order (PO)** - Generate PO dari approved PR, send ke supplier

146. **Goods receiving (GRN)** - Terima barang, quality check, variance report

147. **Three-way matching** - Match PO vs GRN vs Invoice untuk payment approval

148. **Vendor performance rating** - Auto-rate vendor berdasarkan delivery, quality, price

149. **Contract management** - Manage supplier contracts dengan expiry alerts

150. **Price comparison** - Compare vendor prices untuk same item

---

### J. Inventory & Assets (151-158)

151. **Multi-warehouse support** - Central warehouse + department stores

152. **Stock movements** - Receipt, transfer, issue, return, adjustment dengan audit trail

153. **Batch/lot tracking** - Track batch untuk expiry management (F&B ingredients)

154. **Recipe costing (F&B)** - Define recipe ingredients, auto-calculate food cost

155. **Reorder point alerts** - Auto-alert ketika stock di bawah minimum level

156. **Stock opname** - Physical count dengan variance report

157. **Asset register** - Fixed asset master dengan location, custodian, QR label

158. **Depreciation calculation** - Auto-calculate monthly depreciation (straight-line, declining)

---

### K. POS & Online Menu (159-165)

159. **Multi-outlet POS** - Restaurant, bar, spa, retail dengan outlet-specific menu

160. **QR code menu** - Scan QR → view menu → order → pay

161. **Self-ordering** - Guest order sendiri tanpa waiter

162. **Kitchen Display System (KDS)** - Orders appear di kitchen screen

163. **Post to room folio** - F&B charges langsung ke room bill

164. **Split bill** - Split by item, by person, atau by percentage

165. **Loyalty points integration** - Earn/redeem points di POS

---

### L. Multi-Tenancy Architecture (166-175)

166. **Database-per-Tenant + Schema-per-App model** - Setiap organization mendapat database sendiri dengan schema per aplikasi:
    ```
    Hotel A (Database: hotel_a_db)
    ├── Schema: pms          → Reservations, Rooms, Rates
    ├── Schema: accounting   → GL, AP, AR, Journal
    ├── Schema: hrm          → Employees, Payroll
    ├── Schema: inventory    → Stock, Purchase
    └── Schema: shared       → Users, Audit, Settings
    ```
    - Data isolation lebih kuat (database level)
    - Schema isolation per module (schema level)
    - Backup/restore per tenant mudah
    - Migration per module independent
    - Performance tidak saling mempengaruhi
    - Compliance lebih mudah (data locality)

167. **Central Database untuk platform data** - Database pusat untuk:
    - User authentication (login sekali, akses semua)
    - Cross-organization relationships
    - Platform-wide analytics
    - Billing & subscription
    - Marketplace data (supplier catalog)

168. **Invitation-based relationships** - Semua hubungan antar organization via invitation:
    - Hotel invite Supplier → Supplier accept/reject
    - Guest register → Hotel invite as member
    - Employee registration → HR approve
    - Model seperti LinkedIn connections

169. **Multi-branch support** - Satu organization bisa punya banyak branch/property:
    - Hotel chain: 1 org, 10 properties (10 databases)
    - Supplier: 1 org, 5 branches (5 databases)
    - Consolidated reporting untuk owner/shareholders

170. **Cross-tenant transactions di Central DB** - Purchase Order, Invoice, Payment antar tenant:
    - PO created di Hotel DB
    - Reference sync ke Central DB
    - Supplier see di Supplier Portal
    - Payment tracked di Central DB

171. **User multi-organization access** - Satu user bisa akses multiple organizations:
    - Owner punya 3 hotels → 1 login, switch context
    - Supplier sales rep → akses semua branch
    - Accountant → akses hotel + accounting firm

172. **Tenant provisioning automation** - Auto-create database saat organization register:
    - Create database dari template
    - Apply migrations
    - Seed default data
    - Configure connection string

173. **Data sync strategy** - Sync antara Tenant DB ↔ Central DB:
    - Real-time untuk critical data (availability, booking)
    - Batch sync untuk analytics (daily revenue)
    - Event-driven via RabbitMQ

174. **Tenant database routing** - PgBouncer untuk route connections:
    - Connection pooling per tenant
    - Dynamic database selection
    - Failover handling

175. **Consistent approach untuk semua tenant** - Tidak ada tiered model (small/medium/large):
    - Semua tenant dapat database sendiri
    - Scaling based on usage, bukan tier
    - Pricing based on actual consumption

---

### M. Infrastructure Stack (176-190)

176. **TimescaleDB** - Primary database dengan time-series capabilities:
    - PostgreSQL 15+ compatible
    - Hypertables untuk time-series data
    - Compression untuk historical data
    - Continuous aggregates untuk real-time analytics

177. **PgBouncer** - Connection pooling untuk handle 10,000+ connections:
    - Pool size configurable per tenant
    - Transaction/Session pooling modes
    - Automatic failover
    - Connection multiplexing

178. **Redis Cluster** - Distributed caching & real-time features:
    ```
    Use Cases:
    ├── Session storage (JWT, user sessions)
    ├── API rate limiting per tenant
    ├── Real-time room availability
    ├── Pub/Sub for notifications
    ├── Distributed locks (prevent double booking)
    └── Query result caching
    ```

179. **RabbitMQ Cluster** - Message queue untuk event-driven architecture:
    ```
    Exchanges:
    ├── events.booking (new, cancel, modify)
    ├── events.payment (received, failed)
    ├── events.inventory (update, low stock)
    ├── events.notification (email, sms, push)
    └── events.sync (tenant ↔ central)
    ```

180. **Dramatiq Workers** - Background job processing (reuse RabbitMQ broker):
    ```python
    import dramatiq
    from dramatiq.brokers.rabbitmq import RabbitmqBroker

    broker = RabbitmqBroker(url="amqp://guest:guest@rabbitmq:5672")
    dramatiq.set_broker(broker)

    @dramatiq.actor
    def run_night_audit(hotel_id: int):
        process_daily_charges(hotel_id)
        calculate_revenue(hotel_id)
    ```
    Tasks:
    ├── Email/SMS notifications
    ├── Report generation
    ├── Data sync (tenant ↔ central)
    ├── Invoice processing
    ├── Image resizing/optimization
    └── Scheduled tasks (night audit)

181. **APScheduler** - Scheduled task runner (with Dramatiq):
    - Daily revenue sync (02:00)
    - Monthly report generation (1st of month)
    - Session cleanup (hourly)
    - Low inventory alerts (every 6 hours)
    - Reservation reminders (daily 08:00)

182. **Cloudflare R2** - S3-compatible object storage (zero egress fee, built-in CDN):
    ```
    Buckets:
    ├── hotel-{id}/
    │   ├── guests/       (ID scans, passports)
    │   ├── invoices/     (PDF invoices)
    │   ├── reports/      (generated reports)
    │   └── documents/    (contracts)
    └── shared/
        └── templates/    (report templates)
    ```
    Benefits:
    - Zero egress fee (download gratis)
    - Built-in CDN
    - S3-compatible API
    - ~$7.50/bulan untuk 500GB

183. **Meilisearch** - Full-text search engine:
    - Guest search (name, phone, email)
    - Supplier product search
    - Menu item search
    - Inventory item search
    - Typo-tolerant, instant results

184. **Traefik** - Load balancer & reverse proxy:
    - Auto-discovery (Docker labels)
    - Let's Encrypt SSL auto-renewal
    - Path-based routing
    - Health checks
    - Rate limiting

185. **Prometheus** - Metrics collection:
    - API latency & error rates
    - Database connection pool stats
    - Queue depth & processing time
    - Resource utilization (CPU, memory, disk)

186. **Grafana** - Dashboards & visualization:
    - System Overview dashboard
    - API Performance dashboard
    - Database Health dashboard
    - Business Metrics dashboard
    - Tenant Usage dashboard

187. **Loki** - Log aggregation:
    - Centralized logging
    - Log correlation with traces
    - Structured logging (JSON)
    - Retention policies

188. **Jaeger** - Distributed tracing:
    - Request tracing across services
    - Latency analysis
    - Dependency mapping
    - Error tracking

189. **Sentry** - Error tracking:
    - Exception monitoring
    - Performance monitoring
    - Release tracking
    - User impact analysis

189b. **Centrifugo** - Real-time WebSocket server:
    ```
    Channels:
    ├── hotel:{id}:rooms        → Room status updates
    ├── hotel:{id}:reservations → New bookings, modifications
    ├── hotel:{id}:notifications→ Staff notifications
    └── user:{id}               → Personal notifications
    ```
    - Dedicated WebSocket server (tidak membebani API)
    - Scales well untuk banyak connections
    - Redis Pub/Sub integration
    - JWT authentication support

190. **Docker Swarm** - Container orchestration (simpler than K8s, sufficient for 500 tenants):
    - Auto-scaling based on load
    - Rolling deployments
    - Self-healing (restart failed containers)
    - Resource limits per service
    - Native Docker integration (no additional tooling)

---

### N. Scaling Strategy (191-200)

191. **Start Small, Scale Big** - Arsitektur yang sama dari awal hingga 500+ tenants:
    ```
    Stage 1 (0-30 tenants):    1 VPS, 4 vCPU, 8GB RAM   ($50-100/month)
    Stage 2 (30-100 tenants):  1 VPS, 8 vCPU, 16GB RAM  ($150-300/month)
    Stage 3 (100-300 tenants): Separate servers         ($500-800/month)
    Stage 4 (300-500+ tenants): Full cluster            ($2,000-5,000/month)
    ```

192. **Vertical scaling first** - Upgrade server specs sebelum horizontal scaling:
    - Lebih simple untuk manage
    - Tidak perlu ubah architecture
    - Cost effective untuk early stage

193. **Horizontal scaling when needed** - Add more nodes saat vertical limit tercapai:
    - Database read replicas
    - Multiple API servers
    - Celery worker scaling
    - Redis/RabbitMQ clustering

194. **Database per tenant scaling** - Setiap tenant database independen:
    - Bisa move ke server berbeda jika overload
    - Tidak perlu sharding kompleks
    - Easy to identify & fix hot tenants

195. **Connection pooling critical** - PgBouncer untuk manage connections:
    - 500 tenants × 10 connections = 5000 connections
    - PgBouncer reduce ke ~500 actual DB connections
    - Prevent "too many connections" error

196. **Caching strategy** - Multi-level caching:
    - L1: Application memory (request-level)
    - L2: Redis (shared across instances)
    - L3: Database (materialized views)

197. **Queue-based load leveling** - RabbitMQ absorb traffic spikes:
    - Heavy tasks go to queue
    - Workers process at sustainable rate
    - Prevent overload during peak

198. **Auto-scaling rules** - Kubernetes HPA (Horizontal Pod Autoscaler):
    - Scale up: CPU > 70% for 2 minutes
    - Scale down: CPU < 30% for 5 minutes
    - Min replicas: 2, Max replicas: 20

199. **Resource limits per service** - Prevent one service from consuming all resources:
    ```yaml
    API:         512MB - 2GB RAM, 0.5 - 2 CPU
    Worker:      256MB - 1GB RAM, 0.25 - 1 CPU
    Redis:       512MB - 16GB RAM
    RabbitMQ:    512MB - 8GB RAM
    TimescaleDB: 2GB - 128GB RAM
    ```

200. **Monitoring-driven scaling** - Scale based on metrics, not guesswork:
    - Alert when approaching limits
    - Capacity planning from historical data
    - Cost optimization (scale down during off-peak)

---

### O. Accounting & Business Rules (201-220) ⚠️ TENTATIVE APPROVAL

> **Status**: Disetujui sementara, akan di-review detail saat implementasi accounting module.

#### O1. Rule Layer Architecture (201-203)

201. **3-Layer Rule System** - Pemisahan rules berdasarkan flexibility:
    ```
    Layer 1: HARD RULES    → Di code, tidak bisa diubah siapapun
    Layer 2: SOFT RULES    → Configurable dengan guardrails (MIN/MAX)
    Layer 3: BUSINESS PARAMS → Fully flexible sesuai kebutuhan
    ```

202. **Hard Rules di Application Layer** - Rules fundamental yang di-enforce di code:
    - Double-entry accounting WAJIB
    - Audit trail WAJIB untuk semua transaksi
    - Soft delete only (tidak ada hard delete)
    - Past date posting DIBLOKIR
    - Closed period IMMUTABLE
    - Negative balance DIBLOKIR

203. **Soft Rules dengan Guardrails** - Configurable tapi dalam batas:
    - Discount max: 0-50% (tidak bisa 100%)
    - Void time limit: 1-24 jam (tidak bisa unlimited)
    - Overbooking max: 0-15% (tidak bisa 50%)
    - Cash float: Rp 500k - 5jt (ada range)
    - Credit limit: per company dengan ceiling

#### O2. Anti-Cheating Controls (204-210)

204. **Segregation of Duties** - Pembuat ≠ Approver:
    ```
    Cashier:    ✅ Posting, ❌ Void sendiri, ❌ Discount >X%
    Supervisor: ✅ Approve void, ❌ Posting, ❌ Terima uang
    Manager:    ✅ Approve discount, ✅ Rate change, ❌ Close period
    System:     ✅ Night audit, ✅ Period close (bukan manusia)
    ```

205. **Approval Workflow Mandatory** - Aksi sensitif perlu approval:
    - Void transaction → Supervisor approval + reason
    - Discount > threshold → Manager approval
    - Refund > amount → Finance Manager approval
    - Rate change setelah booking → Revenue Manager

206. **Immutable Audit Log** - Log yang tidak bisa dihapus/diubah:
    - WHO: user_id, user_name, user_role
    - WHEN: timestamp dengan timezone
    - WHAT: entity_type, entity_id, old_values, new_values
    - WHY: reason (mandatory untuk void, discount, refund)
    - WHERE: ip_address, session_id, user_agent

207. **Double-Entry Accounting Enforced** - Setiap transaksi:
    - Minimal 2 journal entries
    - SUM(debit) HARUS = SUM(credit)
    - Reference ke source document
    - Database constraint untuk validasi balance

208. **Period Close Control** - Tutup buku yang ketat:
    - Daily close oleh Night Audit (system)
    - Monthly close dengan checklist
    - Setelah close: NO posting, NO modification
    - Reopen hanya dengan special authorization + full audit

209. **Cash Handling Controls**:
    - Cash float limit per shift
    - Cash drop threshold (wajib setor ke safe)
    - Cash count wajib saat shift change
    - Over/short harus dijelaskan

210. **Transaction Integrity**:
    - Folio terkunci setelah checkout
    - Rate terkunci setelah check-in (kecuali approval)
    - Payment allocation tidak bisa diubah setelah apply
    - Refund harus reference transaksi asli

#### O3. Accounting Standards (211-215)

211. **Chart of Accounts Standard** - Struktur COA yang konsisten:
    ```
    1xxx - Assets (Cash, AR, Inventory, Fixed Assets)
    2xxx - Liabilities (AP, Accruals, Deposits)
    3xxx - Equity (Capital, Retained Earnings)
    4xxx - Revenue (Room, F&B, Other)
    5xxx - COGS (F&B Cost, Amenities)
    6xxx - Expenses (Payroll, Utilities, Marketing)
    7xxx - Other Income/Expense
    ```

212. **Revenue Recognition Rules**:
    - Room revenue: Recognized per night stayed
    - Advance deposit: Liability until stay
    - No-show: Revenue on no-show date
    - Cancellation fee: Revenue on cancellation date
    - Package: Allocated across components

213. **AR/AP Aging Standard**:
    - Current: 0-30 days
    - 30 days: 31-60 days
    - 60 days: 61-90 days
    - 90+ days: Over 90 days
    - Auto-flag untuk collection follow-up

214. **Tax Handling**:
    - Tax calculated at transaction level
    - Tax summary per period
    - Tax payable tracking
    - Support multiple tax types (VAT, Service, City Tax)

215. **Multi-Currency Support**:
    - Base currency per property
    - Daily exchange rate table
    - Realized/unrealized gain/loss tracking
    - Currency rounding rules

#### O4. Reporting Controls (216-220)

216. **Standard Financial Reports** - Laporan wajib:
    - Daily Revenue Report
    - Trial Balance
    - Income Statement (P&L)
    - Balance Sheet
    - Cash Flow Statement
    - AR/AP Aging Report

217. **Operational Reports** - Laporan operasional:
    - Daily Production Report
    - Occupancy Report
    - ADR/RevPAR Report
    - Market Segment Analysis
    - Source of Business Report

218. **Audit Reports** - Laporan untuk audit:
    - Void Transaction Report
    - Discount Report
    - Rate Variance Report
    - User Activity Log
    - Cash Over/Short Report

219. **Report Access Control**:
    - Financial reports: Finance role only
    - Operational reports: Manager+ role
    - Audit reports: Auditor/GM role
    - Export control (who can export data)

220. **Report Integrity**:
    - Report generated from same data source
    - No manual adjustment di report
    - Timestamp dan user yang generate
    - Report hash untuk verify tidak diubah

---

### P. Payment & Licensing (221-235)

#### P1. Licensing Model (221-225)

221. **Flexible Licensing Architecture** - Support multiple pricing models (business decision later):
    - Per-App Purchase: Bayar per aplikasi
    - Tier/Bundle Package: Bronze/Silver/Gold
    - Base + Add-on: Core + optional modules
    - Usage-based: Pay per room/transaction

222. **Central Licensing Tables** - Di central database:
    ```
    Tables:
    ├── plans (template paket)
    ├── features (definisi fitur/app)
    ├── plan_features (mapping plan → features)
    ├── subscriptions (langganan aktif)
    ├── subscription_addons (tambahan)
    ├── usage_records (tracking usage)
    └── invoices (billing records)
    ```

223. **LicenseService** - Check akses fitur di API layer:
    - `has_feature(org_id, feature_code)` - Check akses
    - `get_feature_limit(org_id, metric)` - Get limit
    - `check_within_limit(org_id, metric)` - Check usage

224. **Feature Limits** - Support berbagai limit:
    - Room count (max_rooms)
    - User count (max_users)
    - Transaction count (max_transactions)
    - API calls (rate limiting)

225. **Trial & Grace Period** - Support trial dan grace:
    - Trial period configurable (7/14/30 days)
    - Grace period untuk past_due (3-7 days)
    - Auto-downgrade atau suspend

#### P2. Platform Payment (226-229)

226. **Platform Subscription Payment** - Tenant bayar ke Platform Owner:
    - Gateway: Xendit / Midtrans
    - Methods: VA, Credit Card, E-Wallet, QRIS
    - Features: Recurring billing, auto-invoice

227. **Subscription Billing Flow**:
    ```
    1. Tenant pilih plan
    2. Generate invoice
    3. Tenant bayar via VA/CC/E-wallet
    4. Webhook → update subscription status
    5. Auto-renew sebelum expired
    ```

228. **Invoice Management**:
    - Auto-generate invoice setiap billing cycle
    - Email reminder sebelum due date
    - Past due notification
    - Receipt setelah payment

229. **Proration** - Hitung pro-rata untuk:
    - Upgrade mid-cycle
    - Downgrade mid-cycle
    - Add-on mid-cycle

#### P3. Organization Payment (230-235)

230. **Integration-based Payment** - Platform sediakan integrasi, bukan collect:
    - Hotel daftar merchant sendiri ke gateway
    - Hotel input API keys di platform settings
    - Uang langsung ke rekening hotel (NOT through platform)
    - Tidak perlu izin Payment Facilitator

231. **Supported Payment Gateways**:
    | Gateway  | VA | CC | E-Wallet | QRIS | Use Case |
    |----------|----|----|----------|------|----------|
    | Midtrans | ✅ | ✅ | ✅       | ✅   | Indonesia full |
    | Xendit   | ✅ | ✅ | ✅       | ✅   | Indonesia dev-friendly |
    | Stripe   | ❌ | ✅ | ❌       | ❌   | International CC |

232. **Payment Gateway Settings** - Per organization:
    - Multiple gateways (Midtrans + Stripe)
    - Set default gateway
    - Sandbox/Production environment
    - Encrypted credentials (server_key)

233. **Payment Flow for Guest**:
    ```
    1. Guest checkout → Staff klik "Pay Online"
    2. Platform generate payment (pakai API key hotel)
    3. Guest bayar via VA/CC/E-wallet/QRIS
    4. Webhook dari gateway → Platform
    5. Platform auto-posting payment ke folio
    6. Uang masuk ke rekening hotel
    ```

234. **Payment Gateway Factory** - Abstract interface untuk semua gateway:
    - `create_payment(request)` - Buat payment
    - `check_status(transaction_id)` - Cek status
    - `cancel_payment(transaction_id)` - Cancel
    - `verify_webhook(payload, signature)` - Verify webhook

235. **Webhook Logging** - Track semua webhook untuk debugging:
    - Store full payload
    - Track processed/error status
    - Retry mechanism untuk failed processing

---

### Q. Operational Standards (236-243)

> Keputusan dari hasil audit multi-agent (2025-12-07)

236. **TimescaleDB Hypertable Implementation**:
    - Hypertables untuk time-series tables (audit_logs, folio_transactions, journal_entries)
    - Compression policy: > 3 bulan (default), > 6 bulan (financial)
    - Retention policy: 3-10 tahun tergantung tipe data
    - Mitigasi FK: UUID surrogate + application-level validation
    - Mitigasi composite PK: UUID untuk external reference
    - Continuous aggregates untuk dashboard KPI

237. **Firebird Database as Reference Only**:
    - Database Firebird (powerfo.gdb, powerbo.gdb) adalah referensi eksternal
    - TIDAK ada migrasi data yang diperlukan
    - Digunakan sebagai acuan untuk analisis tabel PMS hotel
    - Platform dibangun 100% baru dari nol

238. **Backup/Disaster Recovery - Tiered Approach**:
    - Development (0-10 tenants): Basic pg_dump + S3, RPO 24 jam
    - Production (10-100 tenants): pgBackRest + WAL, RPO 5-15 menit
    - Scale (100-500 tenants): Replication + Multi-Region, RPO < 1 menit
    - Alternative: Cloud-Managed RDS/Cloud SQL
    - Retention: Daily 7 hari, Weekly 4 minggu, Monthly 12 bulan, Yearly 7 tahun

239. **Event-Driven Architecture - Celery + RabbitMQ**:
    - Message Broker: RabbitMQ (bukan Redis)
    - Task Library: Celery (quality-focused, production-proven)
    - Result Backend: Redis DB 1
    - Cache: Redis DB 0
    - Session: Redis DB 2
    - Rate Limiting: Redis DB 3
    - Quality settings: task_acks_late, task_reject_on_worker_lost
    - Priority queues: high, default, low

240. **Payment - Recording Only, No PCI-DSS Required**:
    - Platform hanya MENCATAT pembayaran (bukan memproses)
    - Pembayaran aktual dilakukan di luar sistem (cash, EDC, transfer)
    - Tidak ada data kartu kredit yang disimpan/diproses
    - PCI-DSS compliance: NOT APPLICABLE
    - Future: Jika butuh payment gateway, gunakan redirect (SAQ A)

241. **CI/CD - Full GitHub Actions Pipeline**:
    - Platform: GitHub Actions
    - Registry: GitHub Container Registry (ghcr.io)
    - Security: Trivy (container scan), Snyk (dependencies)
    - Coverage: Codecov
    - Branch strategy: main → production (manual), develop → staging (auto)
    - CI: Lint, Type check, Tests, Security scan, Build
    - CD: Auto deploy staging, manual approve production

242. **Code Generation - Full Kubb Setup**:
    - Tool: Kubb (@kubb/core)
    - Source: OpenAPI spec dari FastAPI
    - Output: TypeScript types, Zod schemas, React Query hooks, Axios client
    - Location: /src/api/generated/ (auto-generated, jangan edit manual)
    - Workflow: Backend update DTO → api:generate → Frontend updated
    - CI: Auto-generate dan commit jika ada perubahan

243. **Testing - Full Suite, 70% Coverage Target**:
    - Unit tests: 70% (Pytest backend, Vitest frontend)
    - Integration tests: 20% (TestClient, MSW)
    - E2E tests: 10% (Playwright)
    - Tools: pytest-cov, @vitest/coverage-v8, MSW, Playwright
    - CI: Tests on every PR, block merge if coverage < 70%
    - E2E: Run before production deploy

244. **Logging - Full Observability**:
    - Format: JSON structured logs (bukan plain text)
    - Required fields: timestamp, level, service, tenant_id, correlation_id, message
    - Correlation ID: X-Correlation-ID header di setiap request
    - Stack: Prometheus + Grafana (metrics), Loki (logs), Jaeger (tracing), Sentry (errors)
    - Dashboards: Platform Overview, Service Health, Per-Tenant dashboards
    - Alerting: PagerDuty (critical), Slack (warning)
    - Retention: App logs 1 tahun, Audit logs 7 tahun, Debug logs 7 hari

245. **Internationalization - Delayed i18n**:
    - Strategy: Struktur i18n disiapkan dari awal, translations ditambahkan nanti
    - Primary language: Satu bahasa dulu (Indonesian atau English)
    - Frontend: Lingui (compile-time, smaller bundle, better TypeScript)
    - Backend: Babel/gettext (Python standard)
    - Storage: File-based (PO format)
    - Phases: (1) Structure ready → (2) Primary language → (3) Additional languages

---

## Pending Decisions

> Keputusan yang belum final, perlu diskusi lebih lanjut.

- [ ] GraphQL selain REST API?
- [ ] Native mobile app atau PWA saja untuk guest app?
- [ ] Channel manager: Build vs Buy (integrate existing)?
- [ ] AI/ML hosting: Cloud (AWS SageMaker) vs Self-hosted?
- [ ] Payroll: Support multi-country tax calculation?
- [ ] Supplier Portal: Build vs Use existing e-procurement platform?

---

## Priority Matrix

### Phase 1 - Foundation (Month 1-3)
**Must have untuk go-live:**
1. Core architecture (#1-10)
2. Basic security (#46-55)
3. Database design (#19-35)
4. Basic features (reservations, check-in/out, billing)

### Phase 2 - Operations (Month 4-6)
**Essential untuk daily operations:**
1. Housekeeping mobile (#86)
2. Maintenance system (#87)
3. Reporting & analytics (#103-105)
4. Rate management (#96-98)

### Phase 3 - Distribution (Month 7-9)
**Revenue optimization:**
1. Channel manager (#106)
2. OTA connectivity (#107)
3. Booking engine (#108)
4. Payment gateways (#111)

### Phase 4 - Advanced (Month 10-12)
**Competitive advantage:**
1. Guest mobile app (#79)
2. Loyalty program (#81)
3. Dynamic pricing (#96)
4. IoT integration (#115)

### Phase 5 - AI & Analytics (Month 12+)
**Future-proofing:**
1. Predictive analytics (#119)
2. Demand forecasting (#101)
3. AI pricing (#96)
4. Advanced personalization

---

## Reference Documents

### Platform Documentation
- [PLATFORM_VISION.md](./PLATFORM_VISION.md) - **Complete platform vision & architecture**

### PMS Reference (Legacy Analysis)
- [PMS_DATABASE_ANALYSIS.md](./PMS_DATABASE_ANALYSIS.md) - Analisis database lama
- [PMS_DATABASE_SCHEMA.md](./PMS_DATABASE_SCHEMA.md) - Schema lengkap
- [PMS_WEAKNESSES_ANALYSIS.md](./PMS_WEAKNESSES_ANALYSIS.md) - Kekurangan sistem lama
- [PMS_REFERENCE_INDEX.md](./PMS_REFERENCE_INDEX.md) - Quick reference index

---

## Analysis Reports (Generated by Multi-Agent Analysis)

Detailed reports dari comprehensive analysis:

1. **Database Design Analysis** - 15 major weakness categories found
2. **Security Audit** - 17 vulnerabilities (6 Critical, 5 High, 4 Medium, 2 Low)
3. **Performance Analysis** - 15 critical performance issues
4. **Architecture Review** - 18 architecture anti-patterns
5. **Feature Gap Analysis** - 35+ missing modern features

---

*Dokumen ini di-update setiap ada keputusan baru yang disetujui.*
*v12 - Logging & i18n - 2025-12-07*
*Total Decisions: 245*

**Changes in v12:**
- Added: Decision 244 - Full Observability Logging (JSON structured, Correlation ID, per-tenant dashboards)
- Added: Decision 245 - Delayed i18n (structure ready, 1 language first)
- Updated: DEVELOPMENT_STANDARDS_V2.md with Standard #15-16

**Changes in v11:**
- Added: Section Q - Operational Standards (236-243)
- Added: TimescaleDB Hypertable implementation with mitigations
- Added: Firebird as reference only (no migration)
- Added: Tiered Backup/Disaster Recovery strategy
- Changed: Background Jobs Celery + RabbitMQ (not Dramatiq)
- Added: Payment recording only (PCI-DSS not applicable)
- Added: Full CI/CD with GitHub Actions
- Added: Kubb code generation setup
- Added: Full testing strategy (70% coverage)

**Changes in v10:**
- Added: Section P - Payment & Licensing (221-235)
- Added: Flexible licensing architecture
- Added: Platform subscription payment (Xendit/Midtrans)
- Added: Organization payment integration (Midtrans + Xendit + Stripe)
- Removed from Pending: Payment gateway priority (now decided)

**Changes in v9:**
- Background Jobs: Celery → Dramatiq + RabbitMQ
- File Storage: MinIO → Cloudflare R2
- Orchestration: Docker + K8s → Docker Swarm
- Added: Centrifugo for real-time WebSocket
- Clarified: Database-per-tenant + Schema-per-app
