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
│   ├── base_repository.py
│   └── user_repository.py
│
├── services/                # Shared services
│   ├── __init__.py
│   ├── cache_service.py
│   ├── audit_service.py
│   ├── event_service.py
│   └── rounding_service.py
│
├── validators/              # Reusable validators
│   ├── __init__.py
│   ├── money_validator.py
│   ├── date_validator.py
│   └── period_validator.py
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── formatters.py
│   ├── calculators.py
│   └── generators.py
│
├── types/                   # Shared types/enums
│   ├── __init__.py
│   ├── enums.py
│   └── aliases.py
│
├── middleware/              # Shared middleware
│   ├── __init__.py
│   ├── auth_middleware.py
│   ├── audit_middleware.py
│   └── correlation_middleware.py
│
└── dependencies.py          # FastAPI Depends factories
```

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

## Summary

| Decision | Topic | Pattern |
|----------|-------|---------|
| #100 | Backend Structure | 9 kategori shared folders |
| #101 | Frontend Structure | 7 kategori shared folders |
| #102 | Base Class | 2-level inheritance |
| #103 | Interface/Contract | Self-contained (Interface + DTO) |
| #104 | Naming | I-prefix, Request/Info suffix, etc. |
| #105 | Dependency Injection | Hybrid (Constructor + FastAPI Depends) |

---

*Last Updated: 2025-12-07*
