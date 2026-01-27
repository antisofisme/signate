---
sidebar_position: 1
slug: /
---

# Welcome to ATLAS PUGUH

**ATLAS PUGUH** is a Constitutional Law System for AI-assisted decision making. It provides enterprise-grade governance, compliance, and auditability for automated decisions.

## What is PUGUH?

PUGUH (derived from Indonesian for "steadfast" or "firm") is a decision engine that enforces rules and policies on AI-assisted decisions. Think of it as a constitutional framework that ensures every automated decision follows predefined laws and can be audited.

## Core Capabilities

### 1. Decision Engine
Define rules that govern how decisions are made. Our rule engine supports complex conditions, priorities, and actions.

### 2. Identity & Access Management
Enterprise-grade IAM with role-based permissions, service accounts, and complete audit trails.

### 3. Workflow Orchestration
Multi-step approval workflows with escalation, delegation, and automated routing based on business rules.

### 4. Multi-Tenant Architecture
Complete tenant isolation with per-tenant rules, workflows, and data separation for SaaS deployments.

### 5. Audit & Control
Real-time audit logging, event tracking, and compliance reporting for regulatory requirements.

## Quick Links

- **[Quick Start](/docs/getting-started/quick-start)** - Get up and running in 5 minutes
- **[Create Your First Tenant](/docs/getting-started/first-tenant)** - Set up your organization
- **[Build Your First Rule](/docs/getting-started/first-rule)** - Create a decision rule
- **[API Reference](/docs/api-reference/authentication)** - Integrate with our API

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Application                      │
│                    (SDK / API Integration)                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      ATLAS PUGUH                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Decision │  │ Workflow │  │   IAM    │  │  Audit   │    │
│  │  Engine  │  │  Engine  │  │  Module  │  │  Trail   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Multi-Tenant Data Layer                   │
│              (Isolated per Tenant & Project)                 │
└─────────────────────────────────────────────────────────────┘
```

## Subscription Plans

| Plan | Projects | Decisions/mo | Team Members |
|------|----------|--------------|--------------|
| **Free** | 1 | 1,000 | 3 |
| **Starter** | 5 | 10,000 | 10 |
| **Pro** | Unlimited | 100,000 | Unlimited |
| **Enterprise** | Unlimited | Unlimited | Unlimited |

## Getting Help

- **Documentation**: You're here! Browse the sidebar for detailed guides.
- **API Status**: Check our [status page](https://status.atlashub.com)
- **Support**: Email [support@atlashub.com](mailto:support@atlashub.com)
- **Community**: Join our [Discord](https://discord.gg/atlashub)

---

Ready to get started? Head to the [Quick Start Guide](/docs/getting-started/quick-start).
