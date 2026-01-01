# Development Standards V13

> Standards #44: Fraud Detection & Audit Intelligence (FDA)

---

## Table of Contents

- [44. Fraud Detection & Audit Intelligence](#44-fraud-detection--audit-intelligence)
  - [44.1 Overview](#441-overview)
  - [44.2 Module Classification](#442-module-classification)
  - [44.3 Detection Layers](#443-detection-layers)
  - [44.4 Fraud Scenarios by Module](#444-fraud-scenarios-by-module)
  - [44.5 Database Schema](#445-database-schema)
  - [44.6 Detection Rules Engine](#446-detection-rules-engine)
  - [44.7 Machine Learning Engine](#447-machine-learning-engine)
  - [44.8 LLM Analysis Engine](#448-llm-analysis-engine)
  - [44.9 Alert & Notification System](#449-alert--notification-system)
  - [44.10 Access Control](#4410-access-control)
  - [44.11 API Endpoints](#4411-api-endpoints)
  - [44.12 Dashboard & Reporting](#4412-dashboard--reporting)
  - [44.13 Data Collection & Privacy](#4413-data-collection--privacy)
  - [44.14 Cold Start Strategy](#4414-cold-start-strategy)
  - [44.15 Security Measures](#4415-security-measures)

---

## 44. Fraud Detection & Audit Intelligence

### 44.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           FRAUD DETECTION & AUDIT INTELLIGENCE (FDA)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose:                                                                   │
│  Sistem untuk mendeteksi, menganalisis, dan memberikan alert terhadap      │
│  aktivitas mencurigakan (fraud, cheating, anomaly) di seluruh module.      │
│                                                                             │
│  Key Features:                                                              │
│  • Multi-layer detection (Rule + ML + LLM)                                 │
│  • Cross-module analysis                                                    │
│  • Real-time & batch processing                                            │
│  • Explainable alerts (kenapa dicurigai)                                   │
│  • Hidden from regular users                                               │
│  • Restricted access (Auditor/Owner only)                                  │
│                                                                             │
│  Module Code: fda                                                           │
│  Type: Cross-Module Add-on                                                  │
│  Standalone: NO (requires at least 1 analyzable module)                    │
│                                                                             │
│  Analyzable Modules:                                                        │
│  PMS, POS, ACC, INV, HRM, PROC, SPA, GYM, LDR                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.2 Module Classification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FDA MODULE CLASSIFICATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Type: CROSS-MODULE ADD-ON                                                  │
│  ─────────────────────────                                                  │
│                                                                             │
│  Characteristics:                                                           │
│  • Tidak bisa standalone (butuh data dari module lain)                     │
│  • Tidak punya single parent (cross-cutting)                               │
│  • Valuable sebagai subscription tambahan                                  │
│  • Hidden module (tidak visible di menu biasa)                             │
│                                                                             │
│  Dependencies:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Minimum: 1 module dari list berikut                                 │   │
│  │                                                                      │   │
│  │ • PMS  - Property Management    (room, folio, guest transactions)  │   │
│  │ • POS  - Point of Sale          (sales, voids, discounts)          │   │
│  │ • ACC  - Accounting             (journals, payments, vendors)       │   │
│  │ • INV  - Inventory              (stock, receiving, waste)          │   │
│  │ • HRM  - Human Resources        (attendance, payroll)              │   │
│  │ • PROC - Procurement            (PO, vendors, pricing)             │   │
│  │ • SPA  - Spa & Wellness         (appointments, commissions)        │   │
│  │ • GYM  - Fitness Center         (memberships, sessions)            │   │
│  │ • LDR  - Laundry                (orders, collections)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Subscription Model:                                                        │
│  • FDA Basic: Rule-based detection only                                    │
│  • FDA Pro: Rule + ML detection                                            │
│  • FDA Enterprise: Rule + ML + LLM analysis                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.3 Detection Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THREE-LAYER DETECTION ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │  LAYER 3: LLM ENGINE                                         │  │   │
│  │   │  ─────────────────────                                       │  │   │
│  │   │  • Contextual analysis                                       │  │   │
│  │   │  • Natural language explanations                             │  │   │
│  │   │  • Cross-correlation insights                                │  │   │
│  │   │  • Recommendation generation                                 │  │   │
│  │   │  Processing: On-demand + Daily summary                       │  │   │
│  │   │  Subscription: FDA Enterprise                                │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                              ▲                                       │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │  LAYER 2: MACHINE LEARNING ENGINE                            │  │   │
│  │   │  ────────────────────────────────                            │  │   │
│  │   │  • Anomaly detection models                                  │  │   │
│  │   │  • Behavioral profiling                                      │  │   │
│  │   │  • Pattern recognition                                       │  │   │
│  │   │  • Risk scoring                                              │  │   │
│  │   │  Processing: Batch (hourly/daily)                            │  │   │
│  │   │  Subscription: FDA Pro                                       │  │   │
│  │   │  Data requirement: 3+ months history                         │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                              ▲                                       │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │  LAYER 1: RULE-BASED ENGINE                                  │  │   │
│  │   │  ──────────────────────────────                              │  │   │
│  │   │  • Threshold checks                                          │  │   │
│  │   │  • Statistical deviation                                     │  │   │
│  │   │  • Benford's Law                                             │  │   │
│  │   │  • Ratio analysis                                            │  │   │
│  │   │  • Sequence validation                                       │  │   │
│  │   │  Processing: Real-time + Batch                               │  │   │
│  │   │  Subscription: FDA Basic (included all tiers)                │  │   │
│  │   │  Data requirement: Day 1 ready                               │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.4 Fraud Scenarios by Module

#### 44.4.1 PMS (Property Management)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PMS FRAUD SCENARIOS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Cash Skimming       │ • Cash vs card ratio deviation                │  │
│  │                     │ • Revenue vs occupancy mismatch               │  │
│  │                     │ • Compare with similar properties             │  │
│  │                     │                                                │  │
│  │ Void Abuse          │ • Void rate > threshold (5%)                  │  │
│  │                     │ • Void timing pattern (supervisor away)       │  │
│  │                     │ • Void-to-total ratio per cashier             │  │
│  │                     │ • Cash-only void concentration                │  │
│  │                     │                                                │  │
│  │ Discount Abuse      │ • Discount rate > threshold                   │  │
│  │                     │ • Discounts without approval                  │  │
│  │                     │ • Same guest repeated discounts               │  │
│  │                     │ • Time pattern (end of shift)                 │  │
│  │                     │                                                │  │
│  │ Rate Manipulation   │ • Rate below rack rate without approval       │  │
│  │                     │ • Manual rate overrides frequency             │  │
│  │                     │ • Rate vs similar dates comparison            │  │
│  │                     │                                                │  │
│  │ City Ledger Abuse   │ • Aging > threshold without follow-up         │  │
│  │                     │ • Transfer to city ledger pattern             │  │
│  │                     │ • Write-off patterns                          │  │
│  │                     │                                                │  │
│  │ Phantom Guest       │ • Room status vs registration mismatch        │  │
│  │                     │ • Housekeeping report discrepancy             │  │
│  │                     │ • Minibar consumption without guest           │  │
│  │                     │                                                │  │
│  │ Late Checkout       │ • Late checkout not charged                   │  │
│  │                     │ • Extended stay not reflected                 │  │
│  │                     │                                                │  │
│  │ No-Show Manip.      │ • No-show rate deviation                      │  │
│  │                     │ • No-show converted to walk-in same day       │  │
│  │                     │                                                │  │
│  │ Complimentary       │ • Complimentary rate above threshold          │  │
│  │                     │ • Same staff repeated complimentary           │  │
│  │                     │ • Complimentary without proper auth           │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 44.4.2 POS (Point of Sale)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POS FRAUD SCENARIOS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Cash Skimming       │ • Cash vs card ratio per cashier              │  │
│  │                     │ • Sales vs traffic count mismatch             │  │
│  │                     │ • Drawer count discrepancy patterns           │  │
│  │                     │                                                │  │
│  │ Void Abuse          │ • Void rate > 5%                              │  │
│  │                     │ • Void after cash payment                     │  │
│  │                     │ • Void timing (supervisor away)               │  │
│  │                     │ • Post-payment void                           │  │
│  │                     │                                                │  │
│  │ Discount Abuse      │ • Unauthorized discounts                      │  │
│  │                     │ • Employee discount frequency                 │  │
│  │                     │ • Discount without valid promo                │  │
│  │                     │                                                │  │
│  │ Sweet-hearting      │ • Items deleted after preparation             │  │
│  │                     │ • Free items frequency                        │  │
│  │                     │ • Transaction modification after KOT          │  │
│  │                     │                                                │  │
│  │ Short-ringing       │ • Item substitution pattern                   │  │
│  │                     │ • Cheaper item rung vs actual                 │  │
│  │                     │ • Manual price entry frequency                │  │
│  │                     │                                                │  │
│  │ Waste Fraud         │ • Waste rate > threshold                      │  │
│  │                     │ • Waste vs sales ratio                        │  │
│  │                     │ • Same items repeatedly wasted                │  │
│  │                     │ • Waste timing pattern                        │  │
│  │                     │                                                │  │
│  │ Refund Fraud        │ • Refund rate > threshold                     │  │
│  │                     │ • Cash refund vs card purchase                │  │
│  │                     │ • Same customer repeated refunds              │  │
│  │                     │                                                │  │
│  │ Bill Splitting      │ • Split to avoid threshold                    │  │
│  │                     │ • Repeated small transactions                 │  │
│  │                     │                                                │  │
│  │ Receipt Gap         │ • Missing receipt numbers                     │  │
│  │                     │ • Sequence breaks                             │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 44.4.3 ACC (Accounting)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACC FRAUD SCENARIOS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Ghost Vendor        │ • New vendor → immediate large payment        │  │
│  │                     │ • Vendor address = employee address           │  │
│  │                     │ • Vendor bank = employee bank                 │  │
│  │                     │ • No purchase history before payment          │  │
│  │                     │                                                │  │
│  │ Duplicate Payment   │ • Same amount, same vendor, close dates       │  │
│  │                     │ • Same invoice number                         │  │
│  │                     │ • Slightly modified invoice number            │  │
│  │                     │                                                │  │
│  │ Journal Manip.      │ • Period-end unusual entries                  │  │
│  │                     │ • Round number entries                        │  │
│  │                     │ • Entries just below approval threshold       │  │
│  │                     │ • Reversals followed by similar entry         │  │
│  │                     │                                                │  │
│  │ Expense Fraud       │ • Same receipt multiple claims                │  │
│  │                     │ • Weekend/holiday expenses                    │  │
│  │                     │ • Round numbers                               │  │
│  │                     │ • Benford's Law violation                     │  │
│  │                     │                                                │  │
│  │ Kickback Indicator  │ • Single vendor dominance                     │  │
│  │                     │ • Price higher than market                    │  │
│  │                     │ • Urgent/rush payments                        │  │
│  │                     │                                                │  │
│  │ Asset Misuse        │ • Depreciation manipulation                   │  │
│  │                     │ • Disposal without proper process             │  │
│  │                     │ • Asset transfer patterns                     │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 44.4.4 INV (Inventory)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INV FRAUD SCENARIOS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Stock Shrinkage     │ • Variance > threshold per category           │  │
│  │                     │ • High-value item focus                       │  │
│  │                     │ • Pattern by location/shift                   │  │
│  │                     │                                                │  │
│  │ Receiving Fraud     │ • Quantity received < PO (collusion)          │  │
│  │                     │ • Quality substitution                        │  │
│  │                     │ • Same receiver + vendor pattern              │  │
│  │                     │ • Short delivery accepted repeatedly          │  │
│  │                     │                                                │  │
│  │ Stock Count Manip.  │ • Count always matches system                 │  │
│  │                     │ • Last-minute adjustments                     │  │
│  │                     │ • Same counter repeated patterns              │  │
│  │                     │                                                │  │
│  │ Transfer Abuse      │ • Frequent inter-outlet transfers             │  │
│  │                     │ • Transfer shrinkage                          │  │
│  │                     │ • One-way transfer patterns                   │  │
│  │                     │                                                │  │
│  │ Waste Manipulation  │ • Waste rate deviation                        │  │
│  │                     │ • Waste without witness                       │  │
│  │                     │ • Pattern items always wasted                 │  │
│  │                     │                                                │  │
│  │ Usage Ratio         │ • Purchase vs sales ratio deviation           │  │
│  │                     │ • Recipe cost deviation                       │  │
│  │                     │ • Yield variance                              │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 44.4.5 HRM (Human Resources)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HRM FRAUD SCENARIOS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Ghost Employee      │ • No attendance but paid                      │  │
│  │                     │ • Bank account = other employee               │  │
│  │                     │ • Address duplicate                           │  │
│  │                     │ • No activity in any module                   │  │
│  │                     │                                                │  │
│  │ Buddy Punching      │ • Location mismatch                           │  │
│  │                     │ • Time pattern anomaly                        │  │
│  │                     │ • Same device different employees             │  │
│  │                     │ • Biometric + manual punch pattern            │  │
│  │                     │                                                │  │
│  │ Overtime Abuse      │ • OT without corresponding output             │  │
│  │                     │ • Same employees always OT                    │  │
│  │                     │ • OT just below approval threshold            │  │
│  │                     │ • OT timing vs activity log                   │  │
│  │                     │                                                │  │
│  │ Commission Fraud    │ • Sales attributed incorrectly                │  │
│  │                     │ • Split transactions to multiple staff        │  │
│  │                     │ • Commission vs actual sales                  │  │
│  │                     │                                                │  │
│  │ Leave Abuse         │ • Pattern sick leave (Mon/Fri)                │  │
│  │                     │ • Medical cert from same doctor               │  │
│  │                     │ • Leave + outside activity (social media)     │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 44.4.6 PROC (Procurement)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROC FRAUD SCENARIOS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬────────────────────────────────────────────────┐  │
│  │ Scenario            │ Detection Method                               │  │
│  ├─────────────────────┼────────────────────────────────────────────────┤  │
│  │                     │                                                │  │
│  │ Bid Rigging         │ • Same bidders always                         │  │
│  │                     │ • Losing bids always close                    │  │
│  │                     │ • Rotation pattern                            │  │
│  │                     │ • Last minute bid changes                     │  │
│  │                     │                                                │  │
│  │ Vendor Favoritism   │ • Single source without justification         │  │
│  │                     │ • PO always to same vendor                    │  │
│  │                     │ • Bypass competitive bidding                  │  │
│  │                     │                                                │  │
│  │ Price Inflation     │ • Price above market rate                     │  │
│  │                     │ • Price increase frequency                    │  │
│  │                     │ • Different price for same item               │  │
│  │                     │                                                │  │
│  │ Split Purchase      │ • Multiple PO just below threshold            │  │
│  │                     │ • Same vendor, same day, split PO             │  │
│  │                     │ • Avoid approval chain                        │  │
│  │                     │                                                │  │
│  │ Rush PO Pattern     │ • Frequent emergency PO                       │  │
│  │                     │ • Rush = no competitive bidding               │  │
│  │                     │ • Rush always same vendor                     │  │
│  │                     │                                                │  │
│  └─────────────────────┴────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.5 Database Schema

```sql
-- =============================================================================
-- FDA DATABASE SCHEMA
-- Schema: fda
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 44.5.1 Detection Rules
-- -----------------------------------------------------------------------------

CREATE TABLE fda.detection_rules (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Rule identification
    rule_code VARCHAR(50) NOT NULL UNIQUE,
    rule_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Categorization
    module_code VARCHAR(20) NOT NULL,  -- 'pms', 'pos', 'acc', etc. or 'all'
    fraud_category VARCHAR(50) NOT NULL,  -- 'cash_skimming', 'void_abuse', etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'

    -- Rule configuration (ENCRYPTED - tidak bisa dibaca user biasa)
    rule_config BYTEA NOT NULL,  -- Encrypted JSON with thresholds

    -- Processing
    processing_type VARCHAR(20) NOT NULL,  -- 'realtime', 'hourly', 'daily'
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Subscription tier required
    tier_required VARCHAR(20) NOT NULL DEFAULT 'basic',  -- 'basic', 'pro', 'enterprise'

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    version INTEGER NOT NULL DEFAULT 1
);

-- Rule config is encrypted, example structure:
-- {
--   "type": "threshold",
--   "metric": "void_rate",
--   "operator": "gt",
--   "value": 0.05,
--   "time_window": "daily",
--   "group_by": ["user_id", "outlet_id"]
-- }

-- -----------------------------------------------------------------------------
-- 44.5.2 Alerts
-- -----------------------------------------------------------------------------

CREATE TABLE fda.alerts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,

    -- Alert identification
    alert_code VARCHAR(100) NOT NULL,  -- Unique per org + time
    rule_id INTEGER REFERENCES fda.detection_rules(id),

    -- Source
    module_code VARCHAR(20) NOT NULL,
    entity_type VARCHAR(50),  -- 'transaction', 'user', 'vendor', etc.
    entity_id BIGINT,

    -- Alert details
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'new',  -- 'new', 'reviewed', 'investigating', 'resolved', 'false_positive'

    -- Detection details (ENCRYPTED)
    detection_data BYTEA NOT NULL,  -- Encrypted JSON with details

    -- Risk scoring
    risk_score DECIMAL(5,2),  -- 0-100
    confidence_score DECIMAL(5,2),  -- 0-100

    -- Timestamps
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    -- Review
    reviewed_by INTEGER,
    resolution_notes TEXT,

    -- Indexes
    CONSTRAINT pk_alert_org_code UNIQUE (organization_id, alert_code)
);

CREATE INDEX idx_fda_alerts_org_status ON fda.alerts(organization_id, status);
CREATE INDEX idx_fda_alerts_org_severity ON fda.alerts(organization_id, severity);
CREATE INDEX idx_fda_alerts_org_module ON fda.alerts(organization_id, module_code);
CREATE INDEX idx_fda_alerts_detected_at ON fda.alerts(detected_at);

-- Partitioning by month for scalability
-- CREATE TABLE fda.alerts PARTITION BY RANGE (detected_at);

-- -----------------------------------------------------------------------------
-- 44.5.3 User Behavior Profiles (ML)
-- -----------------------------------------------------------------------------

CREATE TABLE fda.user_profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    -- Profile period
    profile_date DATE NOT NULL,  -- Daily profile

    -- Behavioral metrics (ENCRYPTED)
    metrics BYTEA NOT NULL,  -- Encrypted JSON

    -- Risk indicators
    risk_score DECIMAL(5,2),
    anomaly_score DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uk_user_profile UNIQUE (organization_id, user_id, profile_date)
);

-- Example metrics structure:
-- {
--   "transactions": {
--     "total_count": 150,
--     "void_count": 3,
--     "void_rate": 0.02,
--     "discount_count": 10,
--     "discount_rate": 0.067,
--     "cash_ratio": 0.45,
--     "avg_transaction": 125000
--   },
--   "timing": {
--     "avg_start_time": "08:15",
--     "avg_end_time": "17:30",
--     "break_patterns": [...]
--   },
--   "deviations": {
--     "void_rate_zscore": 0.5,
--     "discount_rate_zscore": -0.2
--   }
-- }

-- -----------------------------------------------------------------------------
-- 44.5.4 LLM Analysis Results
-- -----------------------------------------------------------------------------

CREATE TABLE fda.llm_analyses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,

    -- Reference
    alert_id BIGINT REFERENCES fda.alerts(id),
    analysis_type VARCHAR(50) NOT NULL,  -- 'alert_explanation', 'daily_summary', 'pattern_analysis'

    -- Analysis result
    analysis_text TEXT NOT NULL,  -- Natural language explanation
    recommendations JSONB,
    confidence_score DECIMAL(5,2),

    -- LLM metadata
    model_used VARCHAR(100),
    tokens_used INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 44.5.5 Investigation Cases
-- -----------------------------------------------------------------------------

CREATE TABLE fda.investigations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,

    -- Case details
    case_number VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- 'open', 'in_progress', 'closed', 'escalated'
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',

    -- Related alerts
    alert_ids BIGINT[] NOT NULL DEFAULT '{}',

    -- Assignment
    assigned_to INTEGER,

    -- Findings
    findings TEXT,
    financial_impact DECIMAL(15,2),

    -- Resolution
    resolution VARCHAR(50),  -- 'confirmed_fraud', 'false_positive', 'inconclusive', 'policy_violation'
    action_taken TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,

    CONSTRAINT uk_investigation_case UNIQUE (organization_id, case_number)
);

-- -----------------------------------------------------------------------------
-- 44.5.6 Audit Access Log
-- -----------------------------------------------------------------------------

CREATE TABLE fda.access_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    -- Access details
    action VARCHAR(50) NOT NULL,  -- 'view_dashboard', 'view_alert', 'export', etc.
    resource_type VARCHAR(50),
    resource_id BIGINT,

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_fda_access_logs_org_user ON fda.access_logs(organization_id, user_id);
CREATE INDEX idx_fda_access_logs_accessed_at ON fda.access_logs(accessed_at);
```

### 44.6 Detection Rules Engine

```python
# =============================================================================
# RULE-BASED DETECTION ENGINE
# =============================================================================

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal


class RuleType(str, Enum):
    THRESHOLD = "threshold"
    RATIO = "ratio"
    PATTERN = "pattern"
    BENFORD = "benford"
    SEQUENCE = "sequence"
    STATISTICAL = "statistical"
    CROSS_REFERENCE = "cross_reference"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionResult:
    rule_code: str
    triggered: bool
    severity: Severity
    risk_score: Decimal
    details: Dict[str, Any]
    evidence: List[Dict[str, Any]]


class RuleEngine:
    """
    Rule-based detection engine.
    Rules are encrypted in database, loaded securely at runtime.
    """

    def __init__(self, organization_id: int):
        self.organization_id = organization_id
        self._rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Load and decrypt rules from database"""
        # Rules are encrypted, decrypted only in memory
        pass

    async def evaluate_transaction(
        self,
        module: str,
        transaction: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[DetectionResult]:
        """
        Evaluate a transaction against all applicable rules.
        Called in real-time when transactions are created/modified.
        """
        results = []

        applicable_rules = self._get_applicable_rules(module, "realtime")

        for rule in applicable_rules:
            result = await self._evaluate_rule(rule, transaction, context)
            if result.triggered:
                results.append(result)

        return results

    async def evaluate_batch(
        self,
        module: str,
        time_window: str  # 'hourly', 'daily'
    ) -> List[DetectionResult]:
        """
        Batch evaluation for rules that need aggregated data.
        Called by scheduled jobs.
        """
        results = []

        applicable_rules = self._get_applicable_rules(module, time_window)

        for rule in applicable_rules:
            data = await self._fetch_aggregated_data(rule, time_window)
            result = await self._evaluate_rule(rule, data, {})
            if result.triggered:
                results.append(result)

        return results


# =============================================================================
# EXAMPLE RULE IMPLEMENTATIONS
# =============================================================================

class VoidRateRule:
    """
    Detect excessive void rates per cashier.
    """

    def __init__(self, config: Dict[str, Any]):
        self.threshold = config.get("threshold", 0.05)  # 5%
        self.min_transactions = config.get("min_transactions", 10)

    async def evaluate(
        self,
        user_id: int,
        period: str,
        data: Dict[str, Any]
    ) -> DetectionResult:
        total = data.get("total_transactions", 0)
        voids = data.get("void_count", 0)

        if total < self.min_transactions:
            return DetectionResult(
                rule_code="POS_VOID_RATE",
                triggered=False,
                severity=Severity.LOW,
                risk_score=Decimal("0"),
                details={},
                evidence=[]
            )

        void_rate = voids / total

        if void_rate > self.threshold:
            # Calculate risk score based on deviation
            deviation = (void_rate - self.threshold) / self.threshold
            risk_score = min(Decimal("100"), Decimal(str(50 + deviation * 50)))

            return DetectionResult(
                rule_code="POS_VOID_RATE",
                triggered=True,
                severity=self._calculate_severity(void_rate),
                risk_score=risk_score,
                details={
                    "void_rate": void_rate,
                    "threshold": self.threshold,
                    "total_transactions": total,
                    "void_count": voids,
                    "period": period
                },
                evidence=await self._fetch_void_evidence(user_id, period)
            )

        return DetectionResult(
            rule_code="POS_VOID_RATE",
            triggered=False,
            severity=Severity.LOW,
            risk_score=Decimal("0"),
            details={},
            evidence=[]
        )

    def _calculate_severity(self, void_rate: float) -> Severity:
        if void_rate > 0.20:  # >20%
            return Severity.CRITICAL
        elif void_rate > 0.15:  # >15%
            return Severity.HIGH
        elif void_rate > 0.10:  # >10%
            return Severity.MEDIUM
        else:
            return Severity.LOW


class BenfordLawRule:
    """
    Detect manipulation using Benford's Law.
    Natural numbers follow a specific first-digit distribution.
    """

    EXPECTED_DISTRIBUTION = {
        1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079,
        6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
    }

    def __init__(self, config: Dict[str, Any]):
        self.threshold = config.get("chi_square_threshold", 15.51)  # p=0.05
        self.min_samples = config.get("min_samples", 100)

    async def evaluate(
        self,
        amounts: List[Decimal]
    ) -> DetectionResult:
        if len(amounts) < self.min_samples:
            return DetectionResult(
                rule_code="ACC_BENFORD",
                triggered=False,
                severity=Severity.LOW,
                risk_score=Decimal("0"),
                details={},
                evidence=[]
            )

        # Calculate first digit distribution
        observed = self._calculate_distribution(amounts)

        # Chi-square test
        chi_square = self._chi_square_test(observed, len(amounts))

        if chi_square > self.threshold:
            return DetectionResult(
                rule_code="ACC_BENFORD",
                triggered=True,
                severity=self._calculate_severity(chi_square),
                risk_score=Decimal(str(min(100, chi_square * 3))),
                details={
                    "chi_square": chi_square,
                    "threshold": self.threshold,
                    "observed_distribution": observed,
                    "expected_distribution": self.EXPECTED_DISTRIBUTION
                },
                evidence=[]
            )

        return DetectionResult(
            rule_code="ACC_BENFORD",
            triggered=False,
            severity=Severity.LOW,
            risk_score=Decimal("0"),
            details={},
            evidence=[]
        )

    def _calculate_distribution(self, amounts: List[Decimal]) -> Dict[int, float]:
        counts = {i: 0 for i in range(1, 10)}

        for amount in amounts:
            first_digit = int(str(abs(amount)).lstrip('0')[0])
            if first_digit in counts:
                counts[first_digit] += 1

        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}

    def _chi_square_test(
        self,
        observed: Dict[int, float],
        n: int
    ) -> float:
        chi_square = 0.0

        for digit in range(1, 10):
            expected = self.EXPECTED_DISTRIBUTION[digit] * n
            actual = observed.get(digit, 0) * n
            chi_square += ((actual - expected) ** 2) / expected

        return chi_square
```

### 44.7 Machine Learning Engine

```python
# =============================================================================
# MACHINE LEARNING DETECTION ENGINE
# =============================================================================

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np


class MLEngine:
    """
    Machine Learning engine for anomaly detection.
    Requires FDA Pro tier.
    """

    def __init__(self, organization_id: int):
        self.organization_id = organization_id
        self.models = {}

    async def train_user_profile_model(
        self,
        module: str,
        historical_data: np.ndarray
    ):
        """
        Train anomaly detection model using historical data.
        Called periodically to update models.
        """
        if len(historical_data) < 1000:  # Minimum data requirement
            return None

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(historical_data)

        model = IsolationForest(
            contamination=0.05,  # Expected fraud rate
            random_state=42,
            n_estimators=100
        )
        model.fit(scaled_data)

        self.models[f"{module}_user_profile"] = {
            "model": model,
            "scaler": scaler,
            "trained_at": datetime.now()
        }

    async def detect_anomaly(
        self,
        module: str,
        features: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detect anomalies in new data point.
        """
        model_key = f"{module}_user_profile"

        if model_key not in self.models:
            return {"is_anomaly": False, "score": 0}

        model_data = self.models[model_key]
        scaled_features = model_data["scaler"].transform(features.reshape(1, -1))

        prediction = model_data["model"].predict(scaled_features)
        score = model_data["model"].decision_function(scaled_features)

        return {
            "is_anomaly": prediction[0] == -1,
            "anomaly_score": float(-score[0]),  # Higher = more anomalous
            "confidence": self._calculate_confidence(score[0])
        }

    def _calculate_confidence(self, score: float) -> float:
        """Convert anomaly score to confidence percentage"""
        # Normalize score to 0-100
        return min(100, max(0, (0.5 - score) * 100))
```

### 44.8 LLM Analysis Engine

```python
# =============================================================================
# LLM ANALYSIS ENGINE
# =============================================================================

from typing import List, Dict, Any


class LLMAnalysisEngine:
    """
    LLM-based contextual analysis engine.
    Requires FDA Enterprise tier.
    """

    def __init__(self, organization_id: int):
        self.organization_id = organization_id

    async def analyze_alert(
        self,
        alert: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate natural language explanation for an alert.
        """
        prompt = self._build_alert_analysis_prompt(alert, context)

        response = await self._call_llm(prompt)

        return {
            "explanation": response.get("explanation"),
            "key_findings": response.get("key_findings", []),
            "recommendations": response.get("recommendations", []),
            "confidence_score": response.get("confidence_score", 0.7),
            "additional_checks": response.get("additional_checks", [])
        }

    async def generate_daily_summary(
        self,
        alerts: List[Dict[str, Any]],
        date: str
    ) -> Dict[str, Any]:
        """
        Generate daily summary of all alerts for auditor.
        """
        prompt = self._build_daily_summary_prompt(alerts, date)

        response = await self._call_llm(prompt)

        return {
            "summary": response.get("summary"),
            "high_priority_items": response.get("high_priority", []),
            "patterns_identified": response.get("patterns", []),
            "recommended_focus_areas": response.get("focus_areas", [])
        }

    def _build_alert_analysis_prompt(
        self,
        alert: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Build prompt for alert analysis.
        Context includes historical patterns, user profile, etc.
        """
        return f"""
        Analyze the following fraud alert and provide a detailed explanation.

        ALERT DETAILS:
        - Type: {alert.get('fraud_category')}
        - Module: {alert.get('module_code')}
        - Severity: {alert.get('severity')}
        - Risk Score: {alert.get('risk_score')}

        DETECTION DATA:
        {alert.get('detection_data')}

        CONTEXT:
        - User History: {context.get('user_history')}
        - Typical Patterns: {context.get('typical_patterns')}
        - Recent Activity: {context.get('recent_activity')}

        Please provide:
        1. A clear explanation of why this is suspicious
        2. Key findings from the data
        3. Recommended actions for the auditor
        4. Additional checks that should be performed
        5. Your confidence level in this being actual fraud

        Format your response as JSON.
        """

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM API (implementation depends on provider)
        """
        # Implementation would call OpenAI, Anthropic, or local LLM
        pass
```

### 44.9 Alert & Notification System

```python
# =============================================================================
# ALERT & NOTIFICATION SYSTEM
# =============================================================================

class AlertService:
    """
    Manages alert creation, notification, and escalation.
    """

    async def create_alert(
        self,
        organization_id: int,
        rule_result: DetectionResult,
        entity_info: Dict[str, Any]
    ) -> int:
        """
        Create new alert from detection result.
        """
        alert = await self.repository.create({
            "organization_id": organization_id,
            "rule_id": rule_result.rule_id,
            "module_code": entity_info.get("module"),
            "entity_type": entity_info.get("type"),
            "entity_id": entity_info.get("id"),
            "severity": rule_result.severity.value,
            "risk_score": rule_result.risk_score,
            "detection_data": self._encrypt(rule_result.details),
            "status": "new"
        })

        # Notify based on severity
        await self._notify(alert)

        return alert.id

    async def _notify(self, alert: Alert):
        """
        Send notification based on severity.
        """
        if alert.severity == Severity.CRITICAL:
            # Immediate push notification + email to all auditors
            await self.notification_service.send_push(
                roles=["auditor", "owner"],
                title="CRITICAL Fraud Alert",
                message=f"Critical alert in {alert.module_code}",
                priority="high"
            )
            await self.notification_service.send_email(
                roles=["auditor", "owner"],
                template="critical_alert",
                data=alert
            )

        elif alert.severity == Severity.HIGH:
            # Push notification to auditors
            await self.notification_service.send_push(
                roles=["auditor"],
                title="High Priority Alert",
                message=f"High priority alert in {alert.module_code}",
                priority="normal"
            )

        else:
            # Include in daily digest only
            pass
```

### 44.10 Access Control

```python
# =============================================================================
# FDA ACCESS CONTROL
# =============================================================================

class FDAAccessControl:
    """
    Super-restricted access control for FDA module.
    """

    ALLOWED_ROLES = ["owner", "internal_auditor", "external_auditor", "gm", "cfo"]

    ROLE_PERMISSIONS = {
        "owner": {
            "view_all_alerts": True,
            "view_all_modules": True,
            "view_detection_rules": False,  # Never!
            "export_data": True,
            "manage_investigations": True
        },
        "internal_auditor": {
            "view_all_alerts": True,
            "view_all_modules": True,
            "view_detection_rules": False,
            "export_data": True,
            "manage_investigations": True
        },
        "external_auditor": {
            "view_all_alerts": True,
            "view_all_modules": True,
            "view_detection_rules": False,
            "export_data": False,  # Read-only
            "manage_investigations": False
        },
        "gm": {
            "view_all_alerts": False,  # Property-level only
            "view_all_modules": True,
            "view_detection_rules": False,
            "export_data": False,
            "manage_investigations": False
        },
        "cfo": {
            "view_all_alerts": False,  # Financial modules only
            "view_all_modules": False,  # ACC, PROC only
            "view_detection_rules": False,
            "export_data": False,
            "manage_investigations": False
        }
    }

    async def check_access(
        self,
        user: User,
        action: str,
        resource: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has access to FDA resource.
        """
        # Must have FDA role
        if not any(role in self.ALLOWED_ROLES for role in user.roles):
            return False

        # Get user's FDA role
        fda_role = self._get_fda_role(user)
        permissions = self.ROLE_PERMISSIONS.get(fda_role, {})

        # Check action permission
        if not permissions.get(action, False):
            return False

        # Additional resource-level checks
        if resource:
            return await self._check_resource_access(user, fda_role, resource)

        return True

    async def _check_resource_access(
        self,
        user: User,
        role: str,
        resource: Dict[str, Any]
    ) -> bool:
        """
        Check resource-level access.
        """
        if role == "gm":
            # GM can only see alerts from their property
            if resource.get("property_id") != user.property_id:
                return False

        if role == "cfo":
            # CFO can only see financial modules
            if resource.get("module_code") not in ["acc", "proc"]:
                return False

        return True
```

### 44.11 API Endpoints

```yaml
# =============================================================================
# FDA API ENDPOINTS
# =============================================================================

# Base URL: /api/v1/fda (hidden, requires special access)

# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------

GET /api/v1/fda/dashboard:
  description: Get FDA dashboard summary
  auth: FDA role required
  response:
    alerts_summary:
      total: 150
      critical: 5
      high: 23
      medium: 67
      low: 55
    risk_score_trend: [...]
    top_risk_areas: [...]
    recent_alerts: [...]

# -----------------------------------------------------------------------------
# Alerts
# -----------------------------------------------------------------------------

GET /api/v1/fda/alerts:
  description: List alerts with filtering
  auth: FDA role required
  query_params:
    - status: new|reviewed|investigating|resolved|false_positive
    - severity: low|medium|high|critical
    - module: pms|pos|acc|inv|hrm|proc|spa|gym|ldr
    - date_from: ISO date
    - date_to: ISO date
    - page: int
    - limit: int
  response:
    items: [Alert]
    total: int
    page: int

GET /api/v1/fda/alerts/{id}:
  description: Get alert detail with LLM analysis
  auth: FDA role required
  response:
    alert: Alert
    detection_details: object  # Decrypted for authorized users
    llm_analysis: object  # If enterprise tier
    related_alerts: [Alert]
    entity_history: object

PATCH /api/v1/fda/alerts/{id}:
  description: Update alert status
  auth: FDA role required
  body:
    status: reviewed|investigating|resolved|false_positive
    notes: string
  response:
    alert: Alert

# -----------------------------------------------------------------------------
# Investigations
# -----------------------------------------------------------------------------

POST /api/v1/fda/investigations:
  description: Create investigation from alerts
  auth: FDA role required
  body:
    title: string
    description: string
    alert_ids: [int]
    priority: low|medium|high|critical
    assigned_to: int (user_id)
  response:
    investigation: Investigation

GET /api/v1/fda/investigations:
  description: List investigations
  auth: FDA role required
  response:
    items: [Investigation]
    total: int

GET /api/v1/fda/investigations/{id}:
  description: Get investigation detail
  auth: FDA role required
  response:
    investigation: Investigation
    alerts: [Alert]
    timeline: [Event]

PATCH /api/v1/fda/investigations/{id}:
  description: Update investigation
  auth: FDA role required
  body:
    status: open|in_progress|closed|escalated
    findings: string
    financial_impact: decimal
    resolution: confirmed_fraud|false_positive|inconclusive|policy_violation
    action_taken: string
  response:
    investigation: Investigation

# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

GET /api/v1/fda/reports/daily-summary:
  description: Get daily summary report
  auth: FDA role required
  query_params:
    - date: ISO date
  response:
    summary: object
    llm_analysis: object  # If enterprise tier
    alerts_by_module: object
    alerts_by_severity: object
    top_risk_users: [object]

GET /api/v1/fda/reports/module-risk:
  description: Get risk report by module
  auth: FDA role required
  query_params:
    - module: string
    - period: daily|weekly|monthly
  response:
    risk_score: decimal
    trend: [object]
    top_scenarios: [object]
    recommendations: [string]

POST /api/v1/fda/reports/export:
  description: Export report (requires approval)
  auth: owner|internal_auditor only
  body:
    report_type: alerts|investigations|risk
    date_from: ISO date
    date_to: ISO date
    format: pdf|xlsx
  response:
    export_id: string
    status: pending_approval|processing|ready
```

### 44.12 Dashboard & Reporting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FDA DASHBOARD LAYOUT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HEADER                                                              │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐│   │
│  │  │ Overall Risk   │  │ Active Alerts  │  │ Open Investigations    ││   │
│  │  │     72/100     │  │      23        │  │         5              ││   │
│  │  │   ▲ +5 vs LW   │  │   ▲ +8 vs LW   │  │    ▼ -2 vs LW          ││   │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────┐  ┌───────────────────────────────────┐ │
│  │  ALERTS BY SEVERITY           │  │  ALERTS BY MODULE                 │ │
│  │                               │  │                                    │ │
│  │  🔴 Critical: 2               │  │  PMS: ████████░░ 35%              │ │
│  │  🟠 High: 8                   │  │  POS: ██████░░░░ 28%              │ │
│  │  🟡 Medium: 10                │  │  ACC: ████░░░░░░ 18%              │ │
│  │  🟢 Low: 3                    │  │  INV: ██░░░░░░░░ 12%              │ │
│  │                               │  │  HRM: █░░░░░░░░░  7%              │ │
│  └───────────────────────────────┘  └───────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RECENT ALERTS                                                       │   │
│  │                                                                      │   │
│  │  🔴 [CRITICAL] POS - Unusual void pattern detected                  │   │
│  │     Kasir: Budi | Outlet: Restaurant A | 15 voids in 1 hour         │   │
│  │     Risk Score: 92 | 10 minutes ago                                 │   │
│  │                                                                      │   │
│  │  🟠 [HIGH] ACC - Benford's Law violation in expenses                │   │
│  │     Department: Housekeeping | Chi-square: 24.5                     │   │
│  │     Risk Score: 78 | 2 hours ago                                    │   │
│  │                                                                      │   │
│  │  🟠 [HIGH] INV - Stock shrinkage above threshold                    │   │
│  │     Warehouse: Main Kitchen | Variance: 8.5%                        │   │
│  │     Risk Score: 75 | 3 hours ago                                    │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AI INSIGHTS (Enterprise Tier)                                       │   │
│  │                                                                      │   │
│  │  "Berdasarkan analisis 7 hari terakhir, teridentifikasi pola        │   │
│  │   mencurigakan di outlet Restaurant A:                              │   │
│  │   1. Void rate 3x lebih tinggi saat supervisor istirahat            │   │
│  │   2. Cash ratio menurun 15% dibanding bulan lalu                    │   │
│  │   3. 3 kasir menunjukkan pola serupa                                │   │
│  │                                                                      │   │
│  │   REKOMENDASI: Review CCTV dan cash drawer count detail."           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.13 Data Collection & Privacy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION & PRIVACY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA COLLECTED:                                                            │
│  ────────────────                                                           │
│  • All transactions (create, update, void, delete)                         │
│  • User actions with timestamps                                            │
│  • Session data (login, logout, duration)                                  │
│  • Approval workflows                                                       │
│  • System vs manual entry flags                                            │
│                                                                             │
│  DATA NOT COLLECTED:                                                        │
│  ──────────────────                                                         │
│  • Personal communications                                                  │
│  • Keystrokes or screen recordings                                         │
│  • Location tracking (beyond login IP)                                     │
│  • Data from non-subscribed modules                                        │
│                                                                             │
│  DATA RETENTION:                                                            │
│  ────────────────                                                           │
│  • Alerts: 7 years (regulatory compliance)                                 │
│  • User profiles: 2 years rolling                                          │
│  • Raw data: 1 year, then aggregated                                       │
│  • Investigation records: Permanent                                        │
│                                                                             │
│  PRIVACY SAFEGUARDS:                                                        │
│  ───────────────────                                                        │
│  • Detection data encrypted at rest                                        │
│  • Access logged and auditable                                             │
│  • No export without approval                                              │
│  • Regular access review                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.14 Cold Start Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COLD START STRATEGY                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIMELINE:                                                                  │
│  ──────────                                                                 │
│                                                                             │
│  Day 1 - Month 1:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Rule-based detection ACTIVE                                        │   │
│  │ • Threshold-based alerts (void rate, discount rate, etc.)           │   │
│  │ • Data collection for ML training                                   │   │
│  │ • No ML/behavioral detection                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Month 2 - Month 3:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Rule-based detection ACTIVE                                        │   │
│  │ • Statistical deviation alerts enabled                              │   │
│  │ • Benford's Law analysis enabled                                    │   │
│  │ • ML model training in progress                                     │   │
│  │ • Baseline profiles being built                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Month 4+:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • All detection layers ACTIVE                                        │   │
│  │ • ML anomaly detection enabled                                      │   │
│  │ • Behavioral profiling active                                       │   │
│  │ • Continuous model improvement                                      │   │
│  │ • LLM analysis available (Enterprise)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA REQUIREMENTS:                                                         │
│  ┌─────────────────┬──────────────────────────────────────────────────┐   │
│  │ Detection Type  │ Minimum Data Requirement                         │   │
│  ├─────────────────┼──────────────────────────────────────────────────┤   │
│  │ Rule-based      │ Day 1 ready                                      │   │
│  │ Statistical     │ 30 days of data                                  │   │
│  │ Benford's Law   │ 100+ transactions                                │   │
│  │ ML Anomaly      │ 90 days of data                                  │   │
│  │ Behavioral      │ 60 days per user                                 │   │
│  │ LLM Analysis    │ Day 1 ready (contextual)                         │   │
│  └─────────────────┴──────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 44.15 Security Measures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY MEASURES                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ACCESS SECURITY:                                                           │
│  ─────────────────                                                          │
│  • Separate login flow (not in main menu)                                  │
│  • URL tidak predictable (/fda/{random-token}/)                            │
│  • 2FA mandatory untuk semua FDA users                                     │
│  • Session timeout: 15 menit inactivity                                    │
│  • IP whitelisting option                                                  │
│  • Device fingerprinting                                                   │
│                                                                             │
│  DATA SECURITY:                                                             │
│  ──────────────                                                             │
│  • Detection rules ENCRYPTED (AES-256)                                     │
│  • Detection data ENCRYPTED                                                │
│  • User profiles ENCRYPTED                                                 │
│  • No plaintext thresholds in database                                     │
│  • Keys managed via HSM/KMS                                                │
│                                                                             │
│  HIDDEN FROM USERS:                                                         │
│  ──────────────────                                                         │
│  • Detection algorithms                                                    │
│  • Threshold values                                                        │
│  • ML model parameters                                                     │
│  • Which transactions are flagged                                          │
│  • Real-time monitoring status                                             │
│                                                                             │
│  AUDIT TRAIL:                                                               │
│  ─────────────                                                              │
│  • Every FDA access logged                                                 │
│  • Who viewed what, when                                                   │
│  • Export attempts logged                                                  │
│  • Configuration changes logged                                            │
│  • Audit logs immutable (append-only)                                      │
│                                                                             │
│  ANTI-GAMING:                                                               │
│  ─────────────                                                              │
│  • Rules not visible to ANY user                                           │
│  • Thresholds randomized within range                                      │
│  • Detection timing varies                                                 │
│  • No real-time alert to suspected user                                    │
│  • Delayed alerting for non-critical                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Section | Description |
|---------|-------------|
| **44.1 Overview** | FDA module introduction |
| **44.2 Module Classification** | Cross-module add-on type |
| **44.3 Detection Layers** | Rule + ML + LLM architecture |
| **44.4 Fraud Scenarios** | Per-module fraud types |
| **44.5 Database Schema** | Tables for FDA |
| **44.6 Rule Engine** | Rule-based detection code |
| **44.7 ML Engine** | Machine learning detection |
| **44.8 LLM Engine** | AI contextual analysis |
| **44.9 Alert System** | Notification & escalation |
| **44.10 Access Control** | Super-restricted access |
| **44.11 API Endpoints** | FDA REST APIs |
| **44.12 Dashboard** | UI layout |
| **44.13 Privacy** | Data collection rules |
| **44.14 Cold Start** | Gradual enablement |
| **44.15 Security** | Protection measures |

---

*Last Updated: 2025-12-10*
