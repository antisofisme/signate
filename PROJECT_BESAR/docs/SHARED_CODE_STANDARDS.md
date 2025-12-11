# Shared Code Standards

> **Date**: 2025-12-07
> **Decisions**: #100 - #105
> **Status**: Approved

---

## Overview

Dokumen ini mendefinisikan standar untuk **shared/centralized code** yang digunakan bersama oleh semua services dan modules. Tujuan:

1. **Consistency** - Pola yang sama di semua tempat
2. **Reusability** - Code yang bisa dipakai ulang
3. **Maintainability** - Mudah di-maintain dan di-update
4. **Microservice-ready** - Siap split ke microservices

### Perbedaan Shared vs Core Services

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PENTING: Shared ≠ Core Services                                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  SHARED (Utilities) - Dokumen ini                                         ║
║  ────────────────────────────────                                         ║
║  • Pure functions tanpa side effects                                      ║
║  • TIDAK punya database tables                                            ║
║  • TIDAK punya API endpoints                                              ║
║  • TIDAK punya state                                                      ║
║  • Contoh: formatDate(), Button component, validators                     ║
║                                                                            ║
║  CORE SERVICES - Lihat PUZZLE_ARCHITECTURE.md Section 2.1                 ║
║  ────────────────────────────────────────────────────────                 ║
║  • Business services dengan database dan API                              ║
║  • PUNYA database tables                                                  ║
║  • PUNYA API endpoints                                                    ║
║  • PUNYA state                                                            ║
║  • Contoh: Auth, RBAC, Notification, Audit, Search, Files                 ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

| Aspek | Shared (Utilities) | Core Services |
|-------|-------------------|---------------|
| Database | ❌ Tidak | ✅ Ya |
| API Endpoints | ❌ Tidak | ✅ Ya |
| State | ❌ Tidak | ✅ Ya |
| Side Effects | ❌ Tidak | ✅ Ya |
| Lokasi | `shared/` | `core/services/` |
| Dokumentasi | Dokumen ini | PUZZLE_ARCHITECTURE.md |

---

## 1. Backend Shared Structure (Decision #100)

```
shared/
├── __init__.py              # Re-export utama
│
├── config.py                # App configuration
├── database.py              # DB connection & session
├── exceptions.py            # Exception hierarchy
│
├── contracts/               # Service interfaces (untuk cross-service)
│   ├── __init__.py
│   ├── accounting_contract.py
│   ├── pms_contract.py
│   ├── inventory_contract.py
│   └── hrm_contract.py
│
├── entities/                # Shared domain entities (Shared Kernel)
│   ├── __init__.py
│   ├── user.py
│   ├── organization.py
│   ├── journal.py
│   └── coa_account.py
│
├── repositories/            # Shared/base repositories
│   ├── __init__.py
│   └── base_repository.py   # Base class only, NOT concrete repos
│
├── validators/              # Reusable validators (pure functions)
│   ├── __init__.py
│   ├── money_validator.py
│   ├── date_validator.py
│   └── period_validator.py
│
├── utils/                   # Utility functions (pure functions)
│   ├── __init__.py
│   ├── formatters.py        # format_currency(), format_date()
│   ├── calculators.py       # calculate_tax(), round_money()
│   └── generators.py        # generate_uuid(), generate_code()
│
├── types/                   # Shared types/enums (no logic)
│   ├── __init__.py
│   ├── enums.py
│   └── aliases.py
│
└── dependencies.py          # FastAPI Depends factories
```

> **PERHATIAN**: `shared/services/` DIHAPUS dari struktur ini!
>
> Business services seperti `audit_service`, `cache_service`, `notification_service`
> sekarang berada di `core/services/` - lihat PUZZLE_ARCHITECTURE.md Section 2.1.

**Yang BOLEH ada di shared/:**
- ✅ Base classes (BaseRepository, BaseUseCase)
- ✅ Pure utility functions (formatters, calculators)
- ✅ Type definitions (enums, aliases)
- ✅ Validators (pure functions)
- ✅ Contracts/Interfaces
- ✅ Configuration loaders

**Yang TIDAK BOLEH ada di shared/:**
- ❌ Services dengan database (pindah ke core/services/)
- ❌ Services dengan API endpoints (pindah ke core/services/)
- ❌ Services dengan state (pindah ke core/services/)
- ❌ Middleware dengan business logic (pindah ke core/middleware/)

---

## 2. Frontend Shared Structure (Decision #101)

```
src/shared/
├── components/              # Reusable UI components
│   ├── ui/                  # shadcn base (Button, Input, etc.)
│   ├── forms/               # Form components (FormField, etc.)
│   ├── data/                # DataTable, Pagination
│   ├── layout/              # PageHeader, Sidebar, etc.
│   └── feedback/            # Toast, Alert, Modal, Loading
│
├── hooks/                   # Shared hooks
│   ├── index.ts
│   ├── useAuth.ts
│   ├── usePermission.ts
│   ├── usePagination.ts
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
│
├── utils/                   # Utility functions
│   ├── index.ts
│   ├── formatters.ts
│   ├── validators.ts
│   └── helpers.ts
│
├── types/                   # Shared TypeScript types
│   ├── index.ts
│   ├── api.types.ts
│   ├── common.types.ts
│   └── enums.ts
│
├── constants/               # Shared constants
│   ├── index.ts
│   ├── routes.ts
│   ├── queryKeys.ts
│   └── config.ts
│
├── api/                     # API utilities
│   ├── index.ts
│   ├── client.ts
│   ├── interceptors.ts
│   └── generated/           # Kubb generated
│
└── lib/                     # Third-party wrappers
    ├── index.ts
    ├── dayjs.ts
    └── i18n.ts
```

---

## 3. Base Class Pattern (Decision #102)

### 2-Level Inheritance

```
Level 1: BaseRepository (Generic CRUD)
    │
    ▼
Level 2: DomainBaseRepository (Domain-specific)
    │
    ▼
Level 3: ConcreteRepository (Entity-specific)
```

### Implementation

```python
# shared/repositories/base_repository.py
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Level 1: Generic CRUD operations"""

    def __init__(self, session: AsyncSession, model_class: type):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: int) -> Optional[T]:
        return await self.session.get(self.model_class, id)

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        await self.session.merge(entity)
        return entity

    async def delete(self, id: int) -> bool:
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            return True
        return False

    async def list(
        self,
        filters: dict = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[T]:
        query = select(self.model_class)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model_class, key) == value)
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
```

```python
# shared/repositories/accounting_base_repository.py
class AccountingBaseRepository(BaseRepository[T]):
    """Level 2: Accounting domain-specific operations"""

    async def get_by_period(
        self,
        period_id: int,
        organization_id: int
    ) -> List[T]:
        query = select(self.model_class).where(
            self.model_class.period_id == period_id,
            self.model_class.organization_id == organization_id,
            self.model_class.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_fiscal_year(
        self,
        fiscal_year_id: int,
        organization_id: int
    ) -> List[T]:
        query = select(self.model_class).where(
            self.model_class.fiscal_year_id == fiscal_year_id,
            self.model_class.organization_id == organization_id
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def soft_delete(self, id: int, deleted_by_id: int) -> bool:
        entity = await self.get_by_id(id)
        if entity:
            entity.is_deleted = True
            entity.deleted_at = datetime.now(timezone.utc)
            entity.deleted_by_id = deleted_by_id
            return True
        return False
```

```python
# services/accounting/repositories/journal_repository.py
class JournalRepository(AccountingBaseRepository[JournalEntity]):
    """Level 3: Journal-specific operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, JournalModel)

    async def get_unposted(self, organization_id: int) -> List[JournalEntity]:
        query = select(JournalModel).where(
            JournalModel.organization_id == organization_id,
            JournalModel.status == 'draft',
            JournalModel.is_deleted == False
        )
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_source(
        self,
        source_type: str,
        source_id: int
    ) -> Optional[JournalEntity]:
        query = select(JournalModel).where(
            JournalModel.source_type == source_type,
            JournalModel.source_id == source_id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
```

---

## 4. Interface/Contract Pattern (Decision #103)

### Self-Contained Contract (Interface + DTO in 1 file)

```python
# shared/contracts/accounting_contract.py
"""
Accounting Service Contract
===========================
Interface untuk komunikasi dengan Accounting module.
Semua service lain HARUS menggunakan interface ini.

File ini berisi:
1. DTOs - Data transfer objects untuk cross-service
2. Interface - Method yang tersedia
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import List, Optional

# ============================================================
# DTOs - Data yang boleh cross service boundary
# ============================================================

@dataclass(frozen=True)
class JournalLineRequest:
    """Request untuk create journal line"""
    account_id: int
    debit: Decimal
    credit: Decimal
    description: Optional[str] = None


@dataclass(frozen=True)
class CreateJournalRequest:
    """Request untuk create journal dari service lain"""
    source_type: str          # 'pms', 'pos', 'inventory'
    source_id: int            # ID dari source transaction
    transaction_date: date
    description: str
    lines: List[JournalLineRequest]


@dataclass(frozen=True)
class JournalInfo:
    """Response info journal (read-only)"""
    id: int
    journal_no: str
    transaction_date: date
    total_debit: Decimal
    total_credit: Decimal
    status: str


@dataclass(frozen=True)
class AccountBalanceInfo:
    """Response info saldo akun"""
    account_id: int
    account_code: str
    account_name: str
    balance: Decimal
    as_of_date: date


# ============================================================
# Interface - Method yang tersedia
# ============================================================

class IAccountingService(ABC):
    """
    Interface untuk Accounting Service.

    Usage:
        from shared.contracts.accounting_contract import (
            IAccountingService,
            CreateJournalRequest,
            JournalInfo
        )

        class MyUseCase:
            def __init__(self, accounting: IAccountingService):
                self.accounting = accounting
    """

    @abstractmethod
    async def create_journal(
        self,
        request: CreateJournalRequest
    ) -> JournalInfo:
        """Create journal entry dari source transaction"""
        pass

    @abstractmethod
    async def get_journal(
        self,
        journal_id: int
    ) -> Optional[JournalInfo]:
        """Get journal info by ID"""
        pass

    @abstractmethod
    async def get_journal_by_source(
        self,
        source_type: str,
        source_id: int
    ) -> Optional[JournalInfo]:
        """Get journal by source transaction"""
        pass

    @abstractmethod
    async def post_journal(
        self,
        journal_id: int
    ) -> JournalInfo:
        """Post draft journal to ledger"""
        pass

    @abstractmethod
    async def reverse_journal(
        self,
        journal_id: int,
        reason: str
    ) -> JournalInfo:
        """Create reversing entry"""
        pass

    @abstractmethod
    async def get_account_balance(
        self,
        account_id: int,
        as_of_date: Optional[date] = None
    ) -> AccountBalanceInfo:
        """Get account balance as of date"""
        pass
```

### Usage

```python
# services/pms/use_cases/post_room_charge.py

from shared.contracts.accounting_contract import (
    IAccountingService,
    CreateJournalRequest,
    JournalLineRequest
)

class PostRoomChargeUseCase:
    def __init__(
        self,
        folio_repo: IFolioRepository,
        accounting: IAccountingService,  # Interface, not concrete
    ):
        self.folio_repo = folio_repo
        self.accounting = accounting

    async def execute(self, charge_id: int) -> ChargeInfo:
        charge = await self.folio_repo.get_charge(charge_id)

        # Create journal via interface
        journal = await self.accounting.create_journal(
            CreateJournalRequest(
                source_type='pms',
                source_id=charge_id,
                transaction_date=charge.date,
                description=f"Room charge - {charge.room_number}",
                lines=[
                    JournalLineRequest(
                        account_id=AR_ACCOUNT,
                        debit=charge.total,
                        credit=Decimal(0)
                    ),
                    # ... more lines
                ]
            )
        )

        charge.journal_id = journal.id
        await self.folio_repo.save_charge(charge)

        return ChargeInfo.from_entity(charge)
```

---

## 5. Naming Convention (Decision #104)

| Type | Convention | Example |
|------|------------|---------|
| **Interface** | `I` prefix | `IAccountingService`, `IJournalRepository` |
| **Contract DTO (Request)** | `Request` suffix | `CreateJournalRequest`, `PostChargeRequest` |
| **Contract DTO (Response)** | `Info` suffix | `JournalInfo`, `AccountBalanceInfo` |
| **Base Class** | `Base` prefix | `BaseRepository`, `BaseUseCase` |
| **Domain Base** | `{Domain}Base` prefix | `AccountingBaseRepository`, `PMSBaseUseCase` |
| **Mixin** | `Mixin` suffix | `AuditMixin`, `PeriodFilterMixin` |
| **Utility Function** | `snake_case` verb | `format_currency()`, `validate_period()` |
| **Constants** | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE`, `MAX_RETRY_COUNT` |
| **Enums** | `PascalCase` | `JournalStatus`, `PeriodStatus` |
| **Type Alias** | `PascalCase` descriptive | `OrganizationId`, `MoneyAmount` |

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| **Contract** | `{service}_contract.py` | `accounting_contract.py` |
| **Repository** | `{entity}_repository.py` | `journal_repository.py` |
| **Use Case** | `{action}_{entity}.py` | `create_journal.py`, `post_charge.py` |
| **Service** | `{domain}_service.py` | `cache_service.py`, `audit_service.py` |
| **Validator** | `{domain}_validator.py` | `money_validator.py` |
| **Formatter** | `formatters.py` | Single file with all formatters |

---

## 6. Dependency Injection Pattern (Decision #105)

### Hybrid: Constructor DI + FastAPI Depends

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Routes (FastAPI Depends)                              │
│  - Wiring dependencies only                                     │
│  - Only place using Depends()                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Use Cases (Constructor Injection)                     │
│  - Pure Python class                                            │
│  - Framework agnostic                                           │
│  - Easy to test with mocks                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Repositories & Services (Constructor Injection)       │
│  - Pure Python class                                            │
│  - Interface-based                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Centralized Dependency Providers

```python
# shared/dependencies.py
"""
Centralized Dependency Providers
================================
Semua dependency factory untuk FastAPI Depends.
"""

from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db_session
from shared.contracts.accounting_contract import IAccountingService
from shared.contracts.pms_contract import IPMSService

# ============================================================
# Database Session
# ============================================================

async def get_db() -> AsyncSession:
    async with get_db_session() as session:
        yield session


# ============================================================
# Unit of Work
# ============================================================

def get_unit_of_work(
    session: AsyncSession = Depends(get_db)
) -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(session)


# ============================================================
# Repositories
# ============================================================

def get_journal_repository(
    session: AsyncSession = Depends(get_db)
) -> IJournalRepository:
    return JournalRepository(session)


def get_folio_repository(
    session: AsyncSession = Depends(get_db)
) -> IFolioRepository:
    return FolioRepository(session)


# ============================================================
# Services (Interface implementations)
# ============================================================

def get_accounting_service(
    journal_repo: IJournalRepository = Depends(get_journal_repository),
    balance_repo: IBalanceRepository = Depends(get_balance_repository),
    uow: IUnitOfWork = Depends(get_unit_of_work),
) -> IAccountingService:
    return AccountingServiceImpl(journal_repo, balance_repo, uow)


# ============================================================
# Use Cases
# ============================================================

def get_create_journal_uc(
    journal_repo: IJournalRepository = Depends(get_journal_repository),
    validator: JournalValidator = Depends(get_journal_validator),
    uow: IUnitOfWork = Depends(get_unit_of_work),
) -> CreateJournalUseCase:
    return CreateJournalUseCase(journal_repo, validator, uow)


def get_post_room_charge_uc(
    folio_repo: IFolioRepository = Depends(get_folio_repository),
    accounting: IAccountingService = Depends(get_accounting_service),
    uow: IUnitOfWork = Depends(get_unit_of_work),
) -> PostRoomChargeUseCase:
    return PostRoomChargeUseCase(folio_repo, accounting, uow)
```

### Route Usage

```python
# services/pms/routes.py

from fastapi import APIRouter, Depends
from shared.dependencies import get_post_room_charge_uc

router = APIRouter(prefix="/pms", tags=["PMS"])

@router.post("/charges/{charge_id}/post")
async def post_room_charge(
    charge_id: int,
    use_case: PostRoomChargeUseCase = Depends(get_post_room_charge_uc),
):
    result = await use_case.execute(charge_id)
    return {"journal_id": result.journal_id}
```

### Celery Task (Manual Wiring)

```python
# tasks/pms_tasks.py

from celery import shared_task
from shared.database import get_sync_session

@shared_task
def post_room_charge_task(charge_id: int):
    """Background task - no FastAPI Depends"""

    # Manual wiring
    session = get_sync_session()
    folio_repo = FolioRepository(session)
    journal_repo = JournalRepository(session)
    balance_repo = BalanceRepository(session)
    uow = SQLAlchemyUnitOfWork(session)
    accounting = AccountingServiceImpl(journal_repo, balance_repo, uow)

    use_case = PostRoomChargeUseCase(folio_repo, accounting, uow)

    # Execute synchronously
    import asyncio
    result = asyncio.run(use_case.execute(charge_id))

    session.close()
    return {"journal_id": result.journal_id}
```

### Unit Test (Easy Mock)

```python
# tests/unit/pms/test_post_room_charge.py

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

class TestPostRoomChargeUseCase:

    @pytest.fixture
    def mock_dependencies(self):
        return {
            'folio_repo': AsyncMock(spec=IFolioRepository),
            'accounting': AsyncMock(spec=IAccountingService),
            'uow': AsyncMock(spec=IUnitOfWork),
        }

    async def test_creates_journal_and_updates_charge(self, mock_dependencies):
        # Arrange
        mock_dependencies['folio_repo'].get_charge.return_value = FakeCharge(
            id=1,
            total=Decimal('100000'),
            room_number='101'
        )
        mock_dependencies['accounting'].create_journal.return_value = JournalInfo(
            id=99,
            journal_no='JV-2025-0001',
            status='posted'
        )

        # Act
        use_case = PostRoomChargeUseCase(**mock_dependencies)
        result = await use_case.execute(charge_id=1)

        # Assert
        mock_dependencies['accounting'].create_journal.assert_called_once()
        mock_dependencies['folio_repo'].save_charge.assert_called_once()
        assert result.journal_id == 99
```

---

## 7. Import Order Convention

```python
# ============================================================
# 1. Standard library
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

# ============================================================
# 2. Third-party packages
# ============================================================
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

# ============================================================
# 3. Shared (project-wide)
# ============================================================
from shared.database import get_db
from shared.exceptions import NotFoundError, ValidationError
from shared.contracts.accounting_contract import IAccountingService

# ============================================================
# 4. Same service (local)
# ============================================================
from .repositories.journal_repository import JournalRepository
from .dtos import CreateJournalDTO
from .entities import JournalEntity


# ============================================================
# FORBIDDEN - Direct import from other services
# ============================================================
# from services.pms.repositories.folio_repo import FolioRepository  # NO!
# from services.hrm.use_cases.create_employee import ...  # NO!
```

---

## 8. Kubb Integration (Frontend)

Shared code standards **tidak berkontradiksi** dengan Kubb:

```
Backend (FastAPI + Depends)
    │
    ▼ generates
OpenAPI Spec (automatic)
    │
    ▼ consumed by
Kubb (build-time)
    │
    ▼ produces
src/shared/api/generated/
├── types/          # TypeScript interfaces
├── zod/            # Zod schemas
└── hooks/          # React Query hooks
```

### Usage

```typescript
// Feature component using generated code
import { usePostRoomCharge } from '@/shared/api/generated/hooks';
import type { PostChargeResponse } from '@/shared/api/generated/types';

function ChargeActions({ chargeId }: { chargeId: number }) {
  const postCharge = usePostRoomCharge();

  const handlePost = () => {
    postCharge.mutate(chargeId, {
      onSuccess: (data: PostChargeResponse) => {
        toast.success(`Posted! Journal: ${data.journal_id}`);
      }
    });
  };

  return (
    <Button onClick={handlePost} loading={postCharge.isPending}>
      Post to Accounting
    </Button>
  );
}
```

---

## 9. Flexible Configuration Pattern (Decision #106)

### Overview

Pattern untuk **konfigurasi yang bisa diubah tanpa edit code**. Prinsip:

1. **Admin-Editable**: Hotel admin bisa ubah settings tanpa developer
2. **Context-Aware UI**: Tampilkan data terkait saat edit config
3. **Visual Formula**: Formula builder yang user-friendly
4. **Preview**: Real-time preview hasil kalkulasi
5. **Audit Trail**: History semua perubahan config

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     FLEXIBLE CONFIGURATION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────┐         ┌─────────────────┐         ┌─────────────┐          │
│   │   Admin     │         │   Config API    │         │  Database   │          │
│   │  Dashboard  │◄───────►│   /settings/*   │◄───────►│tenant_config│          │
│   └─────────────┘         └────────┬────────┘         └─────────────┘          │
│         │                          │                                            │
│         │ UI Config                │ ConfigService                              │
│         ▼                          ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        BUSINESS LOGIC                                    │  │
│   │                                                                          │  │
│   │   # TIDAK hardcode ❌                                                    │  │
│   │   total = room_rate * nights * 1.21                                      │  │
│   │                                                                          │  │
│   │   # PAKAI config ✅                                                      │  │
│   │   total = await config.calculate(org_id, "room_total_formula", {...})    │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### 9.1 Database Schema

```sql
-- Definisi config yang tersedia (master, dikelola developer)
CREATE TABLE config_definitions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Identity
    config_key VARCHAR(100) NOT NULL UNIQUE,   -- 'pms.pricing.room_total_formula'
    config_name VARCHAR(255) NOT NULL,          -- 'Formula Total Kamar'
    description TEXT,

    -- Type & Validation
    config_type VARCHAR(50) NOT NULL,           -- 'formula', 'number', 'boolean', 'select', 'json'
    default_value JSONB NOT NULL,
    validation_rules JSONB,                     -- {"min": 0, "max": 100, "required": true}

    -- Grouping
    module VARCHAR(50) NOT NULL,                -- 'pms', 'pos', 'accounting'
    category VARCHAR(50) NOT NULL,              -- 'pricing', 'workflow', 'notification'

    -- UI Configuration (Developer-defined)
    ui_config JSONB NOT NULL DEFAULT '{}',

    -- Meta
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Value config per tenant (dikelola admin hotel)
CREATE TABLE tenant_configs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL REFERENCES config_definitions(config_key),
    config_value JSONB NOT NULL,

    -- Audit
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(organization_id, config_key)
);

-- History perubahan config (audit trail)
CREATE TABLE tenant_config_history (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT
);

-- Indexes
CREATE INDEX idx_config_definitions_module ON config_definitions(module);
CREATE INDEX idx_config_definitions_category ON config_definitions(module, category);
CREATE INDEX idx_tenant_configs_org ON tenant_configs(organization_id);
CREATE INDEX idx_tenant_config_history_org ON tenant_config_history(organization_id, changed_at DESC);
```

---

### 9.2 UI Config Structure

Developer mendefinisikan `ui_config` untuk setiap config:

```json
{
    "input_type": "formula",

    "related_tables": [
        {
            "table": "room_types",
            "display_name": "Room Types",
            "columns": ["name", "base_rate"],
            "enabled": true
        },
        {
            "table": "tax_codes",
            "display_name": "Tax Codes",
            "columns": ["name", "percentage"],
            "enabled": true
        }
    ],

    "formula_variables": [
        {
            "key": "room_rate",
            "label": "Room Rate",
            "icon": "🏷️",
            "type": "currency",
            "sample_value": 500000
        },
        {
            "key": "nights",
            "label": "Jumlah Malam",
            "icon": "🌙",
            "type": "number",
            "sample_value": 2
        },
        {
            "key": "tax_percent",
            "label": "Tax %",
            "icon": "📊",
            "type": "percent",
            "sample_value": 11
        }
    ],

    "help_text": "Gunakan variabel yang tersedia untuk membuat formula",
    "preview_enabled": true
}
```

**Input Types:**

| Type | UI Component | Use Case |
|------|--------------|----------|
| `boolean` | Toggle switch | Enable/disable fitur |
| `number` | Number input + unit | Persentase, jumlah |
| `string` | Text input | Teks bebas |
| `select` | Dropdown | Pilihan terbatas |
| `json` | JSON editor | Complex settings |
| `formula` | Formula Builder | Kalkulasi dinamis |

---

### 9.3 Config Key Naming Convention

Pattern: `{module}.{category}.{name}`

```python
# PMS Module - Pricing
"pms.pricing.service_charge"           # Service charge %
"pms.pricing.tax_rate"                 # Tax %
"pms.pricing.room_total_formula"       # Formula kalkulasi
"pms.pricing.rounding_method"          # round_up, round_down, round_nearest

# PMS Module - Check-in/out
"pms.checkin.default_time"             # "14:00"
"pms.checkin.early_checkin_charge"     # Biaya early check-in
"pms.checkin.require_deposit"          # true/false
"pms.checkout.default_time"            # "12:00"
"pms.checkout.late_checkout_charge"    # Biaya late checkout

# PMS Module - Reservation
"pms.reservation.min_stay"             # Minimum nights
"pms.reservation.max_stay"             # Maximum nights
"pms.reservation.allow_same_day"       # Allow same day booking
"pms.reservation.overbooking_allowed"  # Allow overbooking
"pms.reservation.overbooking_percent"  # Max overbooking %

# POS Module
"pos.pricing.service_charge"
"pos.pricing.tax_rate"
"pos.receipt.show_tax_breakdown"
"pos.order.auto_print_kitchen"

# Notification
"notification.email.booking_confirmation"
"notification.whatsapp.checkin_reminder"
"notification.sms.payment_reminder"
```

---

### 9.4 Backend Implementation

#### ConfigService

```python
# core/services/config_service.py

from typing import Any, Optional, List
from decimal import Decimal
import simpleeval
from shared.exceptions import ConfigNotFoundError, ConfigValidationError

class ConfigService:
    """Service untuk manage tenant configurations"""

    def __init__(self, db: Database, cache: Redis):
        self.db = db
        self.cache = cache
        self._cache_ttl = 300  # 5 minutes

    async def get(
        self,
        org_id: int,
        config_key: str,
        default: Any = None
    ) -> Any:
        """Get config value untuk tenant, dengan fallback ke default"""

        # 1. Check cache
        cache_key = f"config:{org_id}:{config_key}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # 2. Query database
        result = await self.db.fetch_one("""
            SELECT
                COALESCE(tc.config_value, cd.default_value) as value
            FROM config_definitions cd
            LEFT JOIN tenant_configs tc
                ON tc.config_key = cd.config_key
                AND tc.organization_id = $1
            WHERE cd.config_key = $2 AND cd.is_active = true
        """, org_id, config_key)

        if not result:
            return default

        value = result['value']

        # 3. Cache & return
        await self.cache.set(cache_key, value, ex=self._cache_ttl)
        return value

    async def get_bool(self, org_id: int, key: str, default: bool = False) -> bool:
        """Get boolean config"""
        value = await self.get(org_id, key, default)
        return bool(value)

    async def get_number(self, org_id: int, key: str, default: Decimal = Decimal("0")) -> Decimal:
        """Get numeric config as Decimal"""
        value = await self.get(org_id, key, default)
        return Decimal(str(value))

    async def get_string(self, org_id: int, key: str, default: str = "") -> str:
        """Get string config"""
        value = await self.get(org_id, key, default)
        return str(value) if value else default

    async def calculate(
        self,
        org_id: int,
        formula_key: str,
        variables: dict[str, Any]
    ) -> Decimal:
        """Execute formula dengan variables (safe evaluation)"""

        formula = await self.get(org_id, formula_key)
        if not formula:
            raise ConfigNotFoundError(f"Formula '{formula_key}' not found")

        # Safe evaluation - tidak bisa execute arbitrary code
        try:
            result = simpleeval.simple_eval(
                formula,
                names=variables,
                functions={
                    "min": min, "max": max, "abs": abs, "round": round
                }
            )
            return Decimal(str(result))
        except Exception as e:
            raise ConfigValidationError(f"Formula error: {e}")

    async def set(
        self,
        org_id: int,
        config_key: str,
        value: Any,
        user_id: int,
        reason: Optional[str] = None
    ) -> None:
        """Set config value untuk tenant dengan audit trail"""

        # 1. Validate definition exists
        definition = await self._get_definition(config_key)
        if not definition:
            raise ConfigNotFoundError(f"Config '{config_key}' not defined")

        # 2. Validate value
        await self._validate_value(definition, value)

        # 3. Get old value for history
        old_value = await self.get(org_id, config_key)

        # 4. Upsert config
        await self.db.execute("""
            INSERT INTO tenant_configs (organization_id, config_key, config_value, updated_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (organization_id, config_key)
            DO UPDATE SET
                config_value = EXCLUDED.config_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
        """, org_id, config_key, value, user_id)

        # 5. Save history
        await self.db.execute("""
            INSERT INTO tenant_config_history
            (organization_id, config_key, old_value, new_value, changed_by, change_reason)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, org_id, config_key, old_value, value, user_id, reason)

        # 6. Invalidate cache
        await self.cache.delete(f"config:{org_id}:{config_key}")

    async def get_with_ui(
        self,
        org_id: int,
        config_key: str
    ) -> dict:
        """Get config dengan UI metadata dan related data untuk frontend"""

        # Get definition + current value
        result = await self.db.fetch_one("""
            SELECT
                cd.config_key,
                cd.config_name,
                cd.description,
                cd.config_type,
                cd.default_value,
                cd.validation_rules,
                cd.ui_config,
                COALESCE(tc.config_value, cd.default_value) as current_value
            FROM config_definitions cd
            LEFT JOIN tenant_configs tc
                ON tc.config_key = cd.config_key
                AND tc.organization_id = $1
            WHERE cd.config_key = $2 AND cd.is_active = true
        """, org_id, config_key)

        if not result:
            raise ConfigNotFoundError(f"Config '{config_key}' not found")

        ui_config = result['ui_config'] or {}

        # Fetch related tables data
        related_data = []
        for table_config in ui_config.get('related_tables', []):
            if table_config.get('enabled', True):
                data = await self._fetch_related_table(
                    org_id,
                    table_config['table'],
                    table_config.get('columns', [])
                )
                related_data.append({
                    **table_config,
                    'data': data
                })

        # Calculate preview if formula
        preview = None
        if result['config_type'] == 'formula' and ui_config.get('preview_enabled'):
            preview = await self._calculate_preview(
                result['current_value'],
                ui_config.get('formula_variables', [])
            )

        return {
            'config': {
                'key': result['config_key'],
                'name': result['config_name'],
                'description': result['description'],
                'type': result['config_type'],
                'value': result['current_value'],
                'default_value': result['default_value'],
                'validation': result['validation_rules']
            },
            'ui': {
                'input_type': ui_config.get('input_type', result['config_type']),
                'help_text': ui_config.get('help_text'),
                'preview_enabled': ui_config.get('preview_enabled', False),
                'formula_variables': ui_config.get('formula_variables', []),
                'related_tables': related_data,
                'input_props': ui_config.get('input_props', {})
            },
            'preview': preview
        }

    async def list_by_module(
        self,
        org_id: int,
        module: str,
        category: Optional[str] = None
    ) -> List[dict]:
        """List semua config untuk module tertentu"""

        query = """
            SELECT
                cd.config_key,
                cd.config_name,
                cd.description,
                cd.config_type,
                cd.category,
                COALESCE(tc.config_value, cd.default_value) as current_value,
                cd.default_value
            FROM config_definitions cd
            LEFT JOIN tenant_configs tc
                ON tc.config_key = cd.config_key
                AND tc.organization_id = $1
            WHERE cd.module = $2 AND cd.is_active = true
        """
        params = [org_id, module]

        if category:
            query += " AND cd.category = $3"
            params.append(category)

        query += " ORDER BY cd.category, cd.sort_order"

        return await self.db.fetch_all(query, *params)
```

#### Usage in Business Logic

```python
# SEBELUM (Hardcoded) ❌
class ReservationService:
    async def calculate_total(self, room_rate: Decimal, nights: int) -> Decimal:
        service_charge = Decimal("0.10")  # Hardcoded!
        tax = Decimal("0.11")              # Hardcoded!
        subtotal = room_rate * nights
        return subtotal * (1 + service_charge + tax)


# SESUDAH (Flexible Config) ✅
class ReservationService:
    def __init__(self, config: ConfigService):
        self.config = config

    async def calculate_total(
        self,
        org_id: int,
        room_rate: Decimal,
        nights: int
    ) -> Decimal:
        # Option 1: Individual configs
        service = await self.config.get_number(org_id, "pms.pricing.service_charge")
        tax = await self.config.get_number(org_id, "pms.pricing.tax_rate")

        subtotal = room_rate * nights
        return subtotal * (1 + service/100 + tax/100)

        # Option 2: Formula (more flexible)
        # return await self.config.calculate(
        #     org_id,
        #     "pms.pricing.room_total_formula",
        #     {"room_rate": room_rate, "nights": nights}
        # )
```

---

### 9.5 API Endpoints

```python
# routes/settings.py

from fastapi import APIRouter, Depends
from core.services.config_service import ConfigService

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("")
async def list_settings(
    module: str,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    config: ConfigService = Depends(get_config_service)
):
    """List semua config untuk module"""
    return await config.list_by_module(
        org_id=current_user.organization_id,
        module=module,
        category=category
    )

@router.get("/{config_key:path}")
async def get_setting(
    config_key: str,
    current_user: User = Depends(get_current_user),
    config: ConfigService = Depends(get_config_service)
):
    """Get single config dengan UI metadata"""
    return await config.get_with_ui(
        org_id=current_user.organization_id,
        config_key=config_key
    )

@router.put("/{config_key:path}")
async def update_setting(
    config_key: str,
    body: UpdateConfigRequest,
    current_user: User = Depends(require_permission("settings.edit")),
    config: ConfigService = Depends(get_config_service)
):
    """Update config value"""
    await config.set(
        org_id=current_user.organization_id,
        config_key=config_key,
        value=body.value,
        user_id=current_user.id,
        reason=body.reason
    )
    return {"status": "updated"}

@router.get("/{config_key:path}/history")
async def get_setting_history(
    config_key: str,
    current_user: User = Depends(require_permission("settings.view")),
    config: ConfigService = Depends(get_config_service)
):
    """Get config change history"""
    return await config.get_history(
        org_id=current_user.organization_id,
        config_key=config_key
    )
```

---

### 9.6 Frontend Components

#### Component Structure

```
src/components/config/
├── ConfigEditor.tsx              # Main container
├── ConfigForm.tsx                # Form wrapper
├── RelatedDataPanel.tsx          # Panel tabel terkait
│
├── inputs/                       # Input types
│   ├── TextInput.tsx
│   ├── NumberInput.tsx
│   ├── SelectInput.tsx
│   ├── BooleanInput.tsx
│   ├── JsonInput.tsx
│   └── FormulaBuilder/           # Formula builder
│       ├── FormulaBuilder.tsx
│       ├── FormulaCanvas.tsx     # Drop zone for tokens
│       ├── VariableChip.tsx      # Draggable variable
│       ├── OperatorButton.tsx    # +, -, ×, ÷
│       └── PreviewPanel.tsx      # Live preview
│
└── hooks/
    ├── useConfig.ts              # Get/update config
    └── useFormulaEvaluator.ts    # Evaluate formula client-side
```

#### Formula Builder UI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Formula Builder: Total Kamar                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Formula Canvas (drop zone):                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │   │
│  │  │ 🏷️ Room Rate │  ×  │ 🌙 Nights    │  ×  │     1.21     │        │   │
│  │  └──────────────┘     └──────────────┘     └──────────────┘        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │ Available Variables │  │ Operators       │  │ Live Preview            │ │
│  │                     │  │                 │  │                         │ │
│  │ 🏷️ Room Rate [drag] │  │  + │ - │ × │ ÷  │  │ Room Rate: Rp 500.000   │ │
│  │ 🌙 Nights    [drag] │  │  ( │ ) │       │  │ Nights: 2               │ │
│  │ 📊 Tax %     [drag] │  │                 │  │ ───────────────────     │ │
│  │ 📊 Service % [drag] │  │                 │  │ Result: Rp 1.210.000    │ │
│  │ 🏛️ City Tax  [drag] │  │                 │  │                         │ │
│  └─────────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### VariableChip Styling

```tsx
// Variable chip dengan warna berdasarkan type
const chipStyles = {
  currency: {
    background: '#e8f5e9',
    border: '1px solid #4caf50',
    color: '#2e7d32'
  },
  percent: {
    background: '#e3f2fd',
    border: '1px solid #2196f3',
    color: '#1565c0'
  },
  number: {
    background: '#fff3e0',
    border: '1px solid #ff9800',
    color: '#e65100'
  }
};

const VariableChip = ({ variable, draggable, onRemove }) => (
  <div
    className="variable-chip"
    style={chipStyles[variable.type]}
    draggable={draggable}
  >
    <span className="icon">{variable.icon}</span>
    <span className="label">{variable.label}</span>
    {onRemove && <button onClick={onRemove}>×</button>}
  </div>
);
```

---

### 9.7 Config Editor with Related Data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings > PMS > Pricing                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────┐  ┌───────────────────────────────┐│
│  │  Service Charge                     │  │  📋 Related Data              ││
│  │                                     │  │                               ││
│  │  ┌─────────────────────────────┐   │  │  Room Types:                  ││
│  │  │  [    10    ] %             │   │  │  ┌──────────┬───────────┐    ││
│  │  └─────────────────────────────┘   │  │  │ Deluxe   │ Rp 500.000│    ││
│  │                                     │  │  │ Suite    │ Rp 900.000│    ││
│  │  ℹ️ Persentase biaya layanan yang   │  │  │ Standard │ Rp 350.000│    ││
│  │    ditambahkan ke total bill       │  │  └──────────┴───────────┘    ││
│  │                                     │  │                               ││
│  ├─────────────────────────────────────┤  │  Tax Codes:                   ││
│  │  Tax Rate                           │  │  ┌──────────┬───────────┐    ││
│  │                                     │  │  │ PPN      │ 11%       │    ││
│  │  ┌─────────────────────────────┐   │  │  │ Service  │ 10%       │    ││
│  │  │  [    11    ] %             │   │  │  └──────────┴───────────┘    ││
│  │  └─────────────────────────────┘   │  │                               ││
│  │                                     │  │  Rate Plans:                  ││
│  │  ℹ️ Pajak yang dikenakan            │  │  • Best Available Rate (BAR) ││
│  │                                     │  │  • Corporate Rate            ││
│  │                                     │  │  • Promo Rate                ││
│  └─────────────────────────────────────┘  └───────────────────────────────┘│
│                                                                             │
│  [💾 Save Changes]                              Last updated: 2 hours ago  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 9.8 Permission

| Permission | Who | Actions |
|------------|-----|---------|
| `settings.view` | All staff | Lihat config values |
| `settings.edit` | Hotel Admin | Edit config values |
| `settings.define` | Developer | Create/modify config_definitions |

---

### 9.9 Summary

| Aspect | Implementation |
|--------|----------------|
| **Storage** | `config_definitions` + `tenant_configs` tables |
| **Caching** | Redis, TTL 5 menit |
| **Access** | Via `ConfigService` (dependency injection) |
| **Naming** | `{module}.{category}.{name}` |
| **Types** | boolean, number, string, select, json, formula |
| **UI Metadata** | `ui_config` JSONB column |
| **Related Data** | Developer-defined, fetched on demand |
| **Formula** | Visual builder dengan drag-drop |
| **Preview** | Real-time calculation |
| **Audit** | History table + user tracking |
| **Permission** | Hotel Admin = edit, Developer = define |

---

## Summary

| Decision | Topic | Pattern |
|----------|-------|---------|
| #100 | Backend Structure | 9 kategori shared folders |
| #101 | Frontend Structure | 7 kategori shared folders |
| #102 | Base Class | 2-level inheritance |
| #103 | Interface/Contract | Self-contained (Interface + DTO) |
| #104 | Naming | I-prefix, Request/Info suffix, etc. |
| #105 | Dependency Injection | Hybrid (Constructor + FastAPI Depends) |
| #106 | Flexible Configuration | Config tables + Visual UI + Formula Builder |

---

*Last Updated: 2025-12-10*
