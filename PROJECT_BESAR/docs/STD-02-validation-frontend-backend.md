# Development Standards V2

> Lanjutan dari DEVELOPMENT_STANDARDS.md (Standard #8-16)
>
> **Last Updated**: 2025-12-07
> **Status**: ✅ Standard #8-16 Approved

---

## Quick Reference

| # | Category | Status | File |
|---|----------|--------|------|
| 1 | Naming Conventions | ✅ Approved | V1 |
| 2 | Database Patterns | ✅ Approved | V1 |
| 3 | RBAC / Permission | ✅ Approved | V1 |
| 4 | Audit Log | ✅ Approved | V1 |
| 5 | Caching | ✅ Approved | V1 |
| 6 | API Patterns | ✅ Approved | V1 |
| 7 | Error Handling | ✅ Approved | V1 |
| 8 | Validation | ✅ Approved | V2 |
| 9 | Testing | ✅ Approved | V2 |
| 10 | Code Structure | ✅ Approved | V2 |
| 11 | Frontend Patterns | ✅ Approved | V2 |
| 12 | Infrastructure & DevOps | ✅ Approved | V2 |
| 13 | Payment & Licensing | ✅ Approved | V2 |
| 14 | TimescaleDB & Operational | ✅ Approved | V2 |
| 15 | Logging & Observability | ✅ Approved | V2 |
| 16 | Internationalization (i18n) | ✅ Approved | V2 |

---

## 8. Validation ✅

### 8.0 Prinsip Validation

```
╔═══════════════════════════════════════════════════════════════════════╗
║  VALIDATION PRINCIPLES                                                 ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. SINGLE SOURCE OF TRUTH  → Backend Pydantic = satu-satunya source ║
║  2. VALIDATE AT BOUNDARIES  → API layer (masuk) dan DB layer (save)  ║
║  3. FAIL FAST               → Validasi dulu sebelum proses apapun    ║
║  4. CODEGEN > MANUAL        → Generate schema, jangan tulis manual   ║
║  5. FRONTEND = UX ONLY      → Backend tetap WAJIB validasi ulang     ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 8.1 Tech Stack Validation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     VALIDATION TECH STACK                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  BACKEND (Source of Truth)                                              │
│  └── Pydantic DTOs                                                      │
│      ├── Type validation                                                │
│      ├── Format validation (email, phone, etc)                          │
│      ├── Constraints (min/max, regex, etc)                              │
│      └── Auto-generate OpenAPI spec                                     │
│                                                                          │
│  CODEGEN (Bridge)                                                       │
│  └── Kubb                                                               │
│      ├── Input: OpenAPI dari FastAPI                                    │
│      ├── Output: TypeScript types                                       │
│      ├── Output: Zod schemas (generated!)                               │
│      └── Output: React Query hooks                                      │
│                                                                          │
│  FRONTEND (Consume Generated)                                           │
│  └── React Hook Form + Generated Zod                                    │
│      ├── Form state management                                          │
│      ├── Validation: pakai generated Zod schemas                        │
│      └── API calls: pakai generated React Query hooks                   │
│                                                                          │
│  DATABASE (Last Defense)                                                │
│  └── Constraints                                                        │
│      ├── NOT NULL, UNIQUE, FK                                           │
│      └── CHECK constraints                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 8.2 Validation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Backend    │     │    Kubb      │     │   Frontend   │
│   Pydantic   │────▶│   Generate   │────▶│   Consume    │
│   DTOs       │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │                    │
      │                     ▼                    │
      │            Generated Files:              │
      │            ├── types.ts                  │
      │            ├── schemas.zod.ts            │
      │            ├── hooks.ts (React Query)    │
      │            └── mocks.ts (MSW)            │
      │                                          │
      └──────────────────────────────────────────┘
              Single Source of Truth
```

---

### 8.3 Backend - Pydantic DTOs (Source of Truth)

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from typing import Optional
import re

# === REUSABLE VALIDATORS ===

def validate_phone(phone: str) -> str:
    """Validate Indonesian phone number."""
    pattern = r'^(\+62|62|0)[0-9]{9,12}$'
    cleaned = phone.replace(' ', '').replace('-', '')
    if not re.match(pattern, cleaned):
        raise ValueError('Invalid phone number format')
    return cleaned

def validate_email(email: str) -> str:
    """Validate and normalize email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError('Invalid email format')
    return email.lower()


# === DTO EXAMPLES ===

class CreateReservationDTO(BaseModel):
    """DTO untuk create reservation - ini jadi source of truth."""

    # Required fields dengan constraints
    guest_id: int = Field(..., gt=0, description="Guest ID")
    room_id: int = Field(..., gt=0, description="Room ID")
    arrival_date: date = Field(..., description="Check-in date")
    departure_date: date = Field(..., description="Check-out date")

    # Optional fields dengan defaults
    adults: int = Field(default=1, ge=1, le=10, description="Number of adults")
    children: int = Field(default=0, ge=0, le=10, description="Number of children")
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Field-level validator
    @field_validator('arrival_date')
    @classmethod
    def arrival_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError('Arrival date cannot be in the past')
        return v

    # Cross-field validator
    @model_validator(mode='after')
    def validate_dates(self):
        if self.departure_date <= self.arrival_date:
            raise ValueError('Departure date must be after arrival date')
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "guest_id": 1,
                "room_id": 101,
                "arrival_date": "2025-01-15",
                "departure_date": "2025-01-18",
                "adults": 2,
                "children": 0
            }
        }
    }


class CreateGuestDTO(BaseModel):
    """DTO untuk create guest."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    id_type: str = Field(..., pattern='^(ktp|passport|sim|other)$')
    id_number: str = Field(..., min_length=5, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_email(v)
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_phone(v)
        return v
```

---

### 8.4 Kubb Configuration

```typescript
// kubb.config.ts
import { defineConfig } from '@kubb/core'
import { pluginOas } from '@kubb/plugin-oas'
import { pluginTs } from '@kubb/plugin-ts'
import { pluginZod } from '@kubb/plugin-zod'
import { pluginReactQuery } from '@kubb/plugin-react-query'

export default defineConfig({
  input: {
    path: 'http://localhost:8001/openapi.json'
  },
  output: {
    path: './src/api/generated',
    clean: true
  },
  plugins: [
    pluginOas(),

    // Generate TypeScript types
    pluginTs({
      output: { path: './types' }
    }),

    // Generate Zod schemas
    pluginZod({
      output: { path: './zod' },
      typed: true,
      coercion: true  // auto-coerce strings to numbers/dates
    }),

    // Generate React Query hooks
    pluginReactQuery({
      output: { path: './hooks' },
      client: { importPath: '@/lib/api-client' },
      mutation: { methods: ['post', 'put', 'patch', 'delete'] },
      query: { methods: ['get'] }
    })
  ]
})
```

```json
// package.json scripts
{
  "scripts": {
    "api:generate": "kubb generate",
    "api:watch": "kubb generate --watch",
    "dev": "npm run api:generate && vite",
    "build": "npm run api:generate && vite build"
  }
}
```

---

### 8.5 Generated Output Structure

```
src/api/generated/
├── types/
│   ├── CreateReservationDTO.ts      # TypeScript interface
│   ├── CreateGuestDTO.ts
│   └── index.ts
├── zod/
│   ├── createReservationDTOSchema.ts  # Zod schema (auto-generated!)
│   ├── createGuestDTOSchema.ts
│   └── index.ts
├── hooks/
│   ├── useCreateReservation.ts       # React Query mutation
│   ├── useGetReservations.ts         # React Query query
│   └── index.ts
└── index.ts
```

```typescript
// Generated: src/api/generated/zod/createReservationDTOSchema.ts
import { z } from 'zod';

export const createReservationDTOSchema = z.object({
  guest_id: z.number().int().positive(),
  room_id: z.number().int().positive(),
  arrival_date: z.coerce.date(),
  departure_date: z.coerce.date(),
  adults: z.number().int().min(1).max(10).default(1),
  children: z.number().int().min(0).max(10).default(0),
  notes: z.string().max(1000).optional().nullable()
});

export type CreateReservationDTO = z.infer<typeof createReservationDTOSchema>;
```

---

### 8.6 Frontend Usage (Consume Generated)

```typescript
// components/ReservationForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Import GENERATED schemas & hooks
import { createReservationDTOSchema, CreateReservationDTO } from '@/api/generated/zod';
import { useCreateReservation } from '@/api/generated/hooks';

function ReservationForm() {
  // Form dengan GENERATED Zod schema
  const form = useForm<CreateReservationDTO>({
    resolver: zodResolver(createReservationDTOSchema),
    defaultValues: {
      adults: 1,
      children: 0
    }
  });

  // GENERATED React Query mutation
  const mutation = useCreateReservation();

  const onSubmit = async (data: CreateReservationDTO) => {
    try {
      await mutation.mutateAsync(data);
      toast.success('Reservation created!');
    } catch (error) {
      // Backend errors di-map ke form fields
      handleApiError(error, form);
    }
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <Input
        {...form.register('arrival_date')}
        error={form.formState.errors.arrival_date?.message}
      />
      <Input
        {...form.register('departure_date')}
        error={form.formState.errors.departure_date?.message}
      />
      {/* ... */}
      <Button type="submit" disabled={mutation.isPending}>
        Create Reservation
      </Button>
    </form>
  );
}
```

---

### 8.7 Use Case Validation (Business Rules)

```python
class CreateReservationUseCase:
    """Business validation yang tidak bisa di-generate."""

    async def execute(self, dto: CreateReservationDTO) -> Reservation:
        # 1. DTO sudah validated oleh Pydantic (format, type, constraints)

        # 2. Async validation - FK exists
        guest = await self.guest_repo.get_by_id(dto.guest_id)
        if not guest:
            raise NotFoundError("Guest", dto.guest_id)

        room = await self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise NotFoundError("Room", dto.room_id)

        # 3. Business rule validation
        if not room.is_active:
            raise BusinessError(
                "BUSINESS_INVALID_STATE",
                "Room is not active",
                [{"field": "room_id"}]
            )

        # 4. Availability check
        is_available = await self.availability_service.check(
            dto.room_id, dto.arrival_date, dto.departure_date
        )
        if not is_available:
            raise RoomNotAvailableError(
                dto.room_id,
                dto.arrival_date.isoformat(),
                dto.departure_date.isoformat()
            )

        # 5. All validations passed
        return await self.repo.create(dto)
```

---

### 8.8 Validation Responsibility Matrix

| Validation Type | Backend Pydantic | Generated Zod | Use Case | Database |
|-----------------|------------------|---------------|----------|----------|
| Type (string, int, date) | ✅ | ✅ (generated) | - | - |
| Required fields | ✅ | ✅ (generated) | - | NOT NULL |
| Format (email, phone) | ✅ | ✅ (generated) | - | - |
| Range (min/max) | ✅ | ✅ (generated) | - | CHECK |
| Enum/Status | ✅ | ✅ (generated) | - | CHECK |
| Cross-field | ✅ | ✅ (generated) | - | CHECK |
| Unique | - | - | ✅ (async) | UNIQUE |
| FK exists | - | - | ✅ (async) | FK |
| Business rules | - | - | ✅ | - |
| Availability | - | - | ✅ | - |

---

### 8.9 Workflow

```
╔═══════════════════════════════════════════════════════════════════════╗
║  DEVELOPMENT WORKFLOW                                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. BACKEND: Buat/update Pydantic DTO                                 ║
║     └── services/pms/dtos.py                                          ║
║                                                                        ║
║  2. TEST: Jalankan backend, cek /docs                                 ║
║     └── http://localhost:8001/docs                                    ║
║                                                                        ║
║  3. GENERATE: Run kubb                                                ║
║     └── npm run api:generate                                          ║
║                                                                        ║
║  4. FRONTEND: Pakai generated code                                    ║
║     └── import { schema, useHook } from '@/api/generated'             ║
║                                                                        ║
║  5. JANGAN pernah edit generated files!                               ║
║     └── Kalau perlu custom, extend di luar folder generated           ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 8.10 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Source of Truth** | Backend Pydantic DTOs |
| **Codegen Tool** | Kubb (OpenAPI → TS + Zod + RQ) |
| **Frontend Form** | React Hook Form + generated Zod |
| **API Client** | Generated React Query hooks |
| **Business Validation** | Use Case layer (async, complex rules) |
| **Database** | Constraints sebagai last defense |
| **Generated Files** | JANGAN edit manual! |
| **Workflow** | Backend DTO → Generate → Frontend consume |

---

## 9. Testing ✅

### 9.0 Prinsip Testing

```
╔═══════════════════════════════════════════════════════════════════════╗
║  TESTING PRINCIPLES                                                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. TEST PYRAMID      → Unit > Integration > E2E (banyak ke sedikit) ║
║  2. TEST BEHAVIOR     → Test apa yang dilakukan, bukan implementasi  ║
║  3. FAST FEEDBACK     → Unit test harus cepat (<5 detik total)       ║
║  4. ISOLATED          → Test tidak depend ke test lain               ║
║  5. DETERMINISTIC     → Hasil sama setiap kali run                   ║
║  6. REALISTIC MOCKS   → Mock external services, bukan internal logic ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 9.1 Test Pyramid

```
                    ┌───────────┐
                    │   E2E     │  ← Sedikit, lambat, mahal
                    │(Playwright)│    Test critical user flows
                    ├───────────┤
                    │Integration│  ← Medium, API + DB
                    │ (pytest)  │    Test endpoints + repositories
                    ├───────────┤
                    │           │
                    │   Unit    │  ← Banyak, cepat, murah
                    │ (pytest)  │    Test use cases, validators
                    │           │
                    └───────────┘

RATIO TARGET:
├── Unit Tests:        70%  (ratusan tests, <5 detik)
├── Integration Tests: 20%  (puluhan tests, <1 menit)
└── E2E Tests:         10%  (belasan tests, <5 menit)
```

---

### 9.2 Tech Stack Testing

| Layer | Backend (Python) | Frontend (React) |
|-------|------------------|------------------|
| **Unit** | pytest | Vitest |
| **Integration** | pytest + TestClient | Vitest + MSW |
| **E2E** | - | Playwright |
| **Mocking** | pytest-mock, unittest.mock | MSW (Mock Service Worker) |
| **Coverage** | pytest-cov | vitest --coverage |
| **API Mocks** | - | MSW (dari Kubb generated) |

---

### 9.3 Backend Testing

#### Unit Test (Use Cases)

```python
# tests/unit/pms/test_create_reservation.py
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

from services.pms.use_cases.create_reservation import CreateReservationUseCase
from services.pms.dtos import CreateReservationDTO
from shared.exceptions import NotFoundError, RoomNotAvailableError


class TestCreateReservationUseCase:
    """Unit test untuk CreateReservationUseCase."""

    @pytest.fixture
    def mock_repos(self):
        return {
            "reservation_repo": AsyncMock(),
            "guest_repo": AsyncMock(),
            "room_repo": AsyncMock(),
            "availability_service": AsyncMock()
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        return CreateReservationUseCase(**mock_repos)

    @pytest.fixture
    def valid_dto(self):
        return CreateReservationDTO(
            guest_id=1,
            room_id=101,
            arrival_date=date.today() + timedelta(days=1),
            departure_date=date.today() + timedelta(days=3),
            adults=2
        )

    async def test_create_success(self, use_case, mock_repos, valid_dto):
        """Should create reservation when all validations pass."""
        # Arrange
        mock_repos["guest_repo"].get_by_id.return_value = MagicMock(id=1)
        mock_repos["room_repo"].get_by_id.return_value = MagicMock(id=101, is_active=True)
        mock_repos["availability_service"].check.return_value = True
        mock_repos["reservation_repo"].create.return_value = MagicMock(id=1)

        # Act
        result = await use_case.execute(valid_dto)

        # Assert
        assert result.id == 1
        mock_repos["reservation_repo"].create.assert_called_once()

    async def test_fail_guest_not_found(self, use_case, mock_repos, valid_dto):
        """Should raise NotFoundError when guest doesn't exist."""
        # Arrange
        mock_repos["guest_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await use_case.execute(valid_dto)

        assert exc_info.value.code == "RESOURCE_NOT_FOUND"
        assert "Guest" in exc_info.value.message

    async def test_fail_room_not_available(self, use_case, mock_repos, valid_dto):
        """Should raise RoomNotAvailableError when room is booked."""
        # Arrange
        mock_repos["guest_repo"].get_by_id.return_value = MagicMock(id=1)
        mock_repos["room_repo"].get_by_id.return_value = MagicMock(id=101, is_active=True)
        mock_repos["availability_service"].check.return_value = False

        # Act & Assert
        with pytest.raises(RoomNotAvailableError):
            await use_case.execute(valid_dto)
```

#### Integration Test (API Endpoints)

```python
# tests/integration/pms/test_reservation_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from tests.factories import GuestFactory, RoomFactory, UserFactory


@pytest.mark.integration
class TestReservationAPI:
    """Integration test untuk reservation endpoints."""

    @pytest.fixture
    async def auth_headers(self, db_session: AsyncSession):
        """Create user and return auth headers."""
        user = await UserFactory.create(db_session)
        token = create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def setup_data(self, db_session: AsyncSession):
        """Setup test data."""
        guest = await GuestFactory.create(db_session)
        room = await RoomFactory.create(db_session, is_active=True)
        return {"guest": guest, "room": room}

    async def test_create_reservation_success(
        self, client: AsyncClient, auth_headers, setup_data
    ):
        """POST /reservations should create reservation."""
        # Arrange
        payload = {
            "guest_id": setup_data["guest"].id,
            "room_id": setup_data["room"].id,
            "arrival_date": "2025-01-15",
            "departure_date": "2025-01-18",
            "adults": 2
        }

        # Act
        response = await client.post(
            "/api/v1/pms/reservations",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["guest_id"] == setup_data["guest"].id

    async def test_create_reservation_guest_not_found(
        self, client: AsyncClient, auth_headers, setup_data
    ):
        """POST /reservations should return 404 for invalid guest."""
        # Arrange
        payload = {
            "guest_id": 99999,  # Non-existent
            "room_id": setup_data["room"].id,
            "arrival_date": "2025-01-15",
            "departure_date": "2025-01-18"
        }

        # Act
        response = await client.post(
            "/api/v1/pms/reservations",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
```

---

### 9.4 Frontend Testing

#### Unit Test (Hooks, Utils)

```typescript
// src/features/reservations/hooks/__tests__/useReservationForm.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useReservationForm } from '../useReservationForm';

describe('useReservationForm', () => {
  it('should initialize with default values', () => {
    const { result } = renderHook(() => useReservationForm());

    expect(result.current.form.getValues('adults')).toBe(1);
    expect(result.current.form.getValues('children')).toBe(0);
  });

  it('should validate departure after arrival', async () => {
    const { result } = renderHook(() => useReservationForm());

    await act(async () => {
      result.current.form.setValue('arrival_date', '2025-01-15');
      result.current.form.setValue('departure_date', '2025-01-10');
      await result.current.form.trigger();
    });

    expect(result.current.form.formState.errors.departure_date).toBeDefined();
  });
});
```

#### Integration Test (Components + MSW)

```typescript
// src/features/reservations/components/__tests__/ReservationForm.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReservationForm } from '../ReservationForm';
import { server } from '@/tests/mocks/server';
import { http, HttpResponse } from 'msw';

describe('ReservationForm', () => {
  it('should submit form successfully', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    render(
      <QueryClientProvider client={queryClient}>
        <ReservationForm onSuccess={onSuccess} />
      </QueryClientProvider>
    );

    // Fill form
    await user.type(screen.getByLabelText(/arrival/i), '2025-01-15');
    await user.type(screen.getByLabelText(/departure/i), '2025-01-18');
    await user.selectOptions(screen.getByLabelText(/guest/i), '1');
    await user.selectOptions(screen.getByLabelText(/room/i), '101');

    // Submit
    await user.click(screen.getByRole('button', { name: /create/i }));

    // Assert
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('should display server validation errors', async () => {
    // Mock server error
    server.use(
      http.post('/api/v1/pms/reservations', () => {
        return HttpResponse.json({
          success: false,
          error: {
            code: 'PMS_ROOM_NOT_AVAILABLE',
            message: 'Room is not available',
            details: [{ field: 'room_id', message: 'Room 101 is booked' }]
          }
        }, { status: 422 });
      })
    );

    const user = userEvent.setup();
    render(<ReservationForm />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/room 101 is booked/i)).toBeInTheDocument();
    });
  });
});
```

#### MSW Mocks (Generated dari Kubb)

```typescript
// src/tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/pms/reservations', () => {
    return HttpResponse.json({
      success: true,
      data: [
        { id: 1, guest_id: 1, room_id: 101, status: 'confirmed' }
      ],
      meta: { total: 1, page: 1 }
    });
  }),

  http.post('/api/v1/pms/reservations', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      success: true,
      data: { id: 1, ...body }
    }, { status: 201 });
  })
];
```

---

### 9.5 E2E Testing (Playwright)

```typescript
// e2e/reservations.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Reservation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@hotel.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create a new reservation', async ({ page }) => {
    await page.click('text=Reservations');
    await page.click('text=New Reservation');

    await page.fill('[name="arrival_date"]', '2025-01-15');
    await page.fill('[name="departure_date"]', '2025-01-18');
    await page.selectOption('[name="guest_id"]', '1');
    await page.selectOption('[name="room_id"]', '101');

    await page.click('button:text("Create")');

    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page).toHaveURL(/\/reservations\/\d+/);
  });

  test('should show error for unavailable room', async ({ page }) => {
    await page.goto('/reservations/new');

    await page.fill('[name="arrival_date"]', '2025-01-15');
    await page.fill('[name="departure_date"]', '2025-01-18');
    await page.selectOption('[name="room_id"]', '101');

    await page.click('button:text("Create")');

    await expect(page.locator('text=Room is not available')).toBeVisible();
  });
});
```

---

### 9.6 Test Organization

```
Backend:
tests/
├── unit/                          # Unit tests (70%)
│   ├── pms/
│   │   ├── test_create_reservation.py
│   │   └── test_check_availability.py
│   └── shared/
├── integration/                   # Integration tests (20%)
│   ├── pms/
│   │   └── test_reservation_api.py
│   └── conftest.py
├── factories/                     # Test data factories
│   ├── guest_factory.py
│   └── room_factory.py
└── conftest.py                   # Global pytest config

Frontend:
src/
├── tests/
│   ├── mocks/
│   │   ├── handlers.ts           # MSW handlers
│   │   └── server.ts
│   └── utils/
│       └── test-utils.tsx
└── features/
    └── reservations/
        └── __tests__/            # Co-located tests

E2E:
e2e/
├── reservations.spec.ts
├── auth.spec.ts
└── playwright.config.ts
```

---

### 9.7 What to Test

| Layer | What to Test | What NOT to Test |
|-------|--------------|------------------|
| **Unit** | Use case logic, validators, utils | Framework code, getters |
| **Integration** | API endpoints, DB queries, auth | External services (mock) |
| **E2E** | Critical user journeys | Every possible path |

**WAJIB Test:**
- ✅ Happy path (success)
- ✅ Validation errors
- ✅ Business rule violations
- ✅ Auth/permission denied
- ✅ Not found cases

---

### 9.8 Coverage Target

| Type | Target | Command |
|------|--------|---------|
| **Unit** | 80%+ | `pytest --cov=services` |
| **Integration** | 60%+ | `pytest --cov -m integration` |
| **Frontend** | 70%+ | `npm run test -- --coverage` |

---

### 9.9 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=services --cov-fail-under=80

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run test -- --coverage
      - run: npm run test:e2e
```

---

### 9.10 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Pyramid** | Unit 70% > Integration 20% > E2E 10% |
| **Backend Unit** | pytest + mock, test use cases |
| **Backend Integration** | pytest + TestClient + real DB |
| **Frontend Unit** | Vitest, test hooks/utils |
| **Frontend Integration** | Vitest + MSW |
| **E2E** | Playwright, critical flows only |
| **Coverage** | Unit 80%+, Integration 60%+ |
| **CI** | Run on every PR, block if fail |

---

## 10. Code Structure ✅

### 10.0 Prinsip Code Structure

```
╔═══════════════════════════════════════════════════════════════════════╗
║  CODE STRUCTURE PRINCIPLES                                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. MODULAR MONOLITH   → Deploy 1 container, tapi struktur siap split║
║  2. SINGLE RESPONSIBILITY → 1 class/function = 1 tujuan jelas        ║
║  3. EXPLICIT CONTRACTS → Komunikasi antar service via interface      ║
║  4. DEPENDENCY INWARD  → Outer layers depend ke inner, bukan sebalik ║
║  5. NO CROSS-IMPORT    → Service A tidak import langsung dari B      ║
║  6. FEATURE-BASED      → Organisasi per fitur, bukan per layer       ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 10.1 Modular Monolith Architecture

```
╔════════════════════════════════════════════════════════════════════════╗
║                        MODULAR MONOLITH                                 ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║  SEKARANG: Deploy sebagai 1 container (monolith)                       ║
║  NANTI: Bisa split jadi microservices tanpa refactor besar             ║
║                                                                         ║
║  ┌──────────────────────────────────────────────────────────┐          ║
║  │                    API Gateway / Routes                   │          ║
║  └──────────────────────────────────────────────────────────┘          ║
║                              │                                          ║
║       ┌──────────────────────┼──────────────────────┐                  ║
║       │                      │                      │                  ║
║       ▼                      ▼                      ▼                  ║
║  ┌─────────┐           ┌─────────┐           ┌─────────┐              ║
║  │   PMS   │           │   HRM   │           │  ACCT   │              ║
║  │ Service │           │ Service │           │ Service │              ║
║  │         │    ◄──────│         │──────►    │         │              ║
║  │         │   Contract│         │Contract   │         │              ║
║  └─────────┘    Only   └─────────┘   Only    └─────────┘              ║
║       │                      │                      │                  ║
║       └──────────────────────┼──────────────────────┘                  ║
║                              │                                          ║
║  ┌──────────────────────────────────────────────────────────┐          ║
║  │                      Shared Layer                         │          ║
║  │          (Database, Config, Utils, Base Classes)          │          ║
║  └──────────────────────────────────────────────────────────┘          ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

### 10.2 Service Communication - Contracts

```python
# ❌ SALAH: Direct import antar service
# services/hrm/use_cases/create_employee.py
from services.pms.repositories.guest_repo import GuestRepository  # SALAH!

# ✅ BENAR: Komunikasi via contract/interface
# shared/contracts/pms_contract.py
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class GuestInfo:
    """Contract DTO - data yang boleh di-share."""
    id: int
    full_name: str
    email: Optional[str]

class PMSContract(ABC):
    """Contract untuk mengakses data PMS dari service lain."""

    @abstractmethod
    async def get_guest_info(self, guest_id: int) -> Optional[GuestInfo]:
        """Get basic guest info. Returns None if not found."""
        pass

    @abstractmethod
    async def is_guest_checked_in(self, guest_id: int) -> bool:
        """Check if guest is currently checked in."""
        pass


# services/pms/contracts/pms_contract_impl.py
class PMSContractImpl(PMSContract):
    """Implementation of PMS contract."""

    def __init__(self, guest_repo: GuestRepository):
        self.guest_repo = guest_repo

    async def get_guest_info(self, guest_id: int) -> Optional[GuestInfo]:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            return None
        return GuestInfo(
            id=guest.id,
            full_name=f"{guest.first_name} {guest.last_name}",
            email=guest.email
        )


# services/hrm/use_cases/assign_employee_to_guest.py
class AssignEmployeeToGuestUseCase:
    """HRM service yang perlu data dari PMS."""

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        pms_contract: PMSContract  # Inject contract, bukan repo langsung!
    ):
        self.employee_repo = employee_repo
        self.pms_contract = pms_contract

    async def execute(self, employee_id: int, guest_id: int):
        # Akses PMS via contract
        guest_info = await self.pms_contract.get_guest_info(guest_id)
        if not guest_info:
            raise NotFoundError("Guest", guest_id)

        # Lanjut logic HRM...
```

**Kenapa Contract Pattern?**

| Tanpa Contract | Dengan Contract |
|---------------|-----------------|
| Direct import = tight coupling | Interface = loose coupling |
| Sulit split jadi microservice | Mudah split (contract jadi API) |
| Circular dependency risk | No circular dependency |
| Sulit test (perlu mock internal) | Mudah test (mock contract) |

---

### 10.3 Backend Folder Structure

```
backend-python/
├── services/                     # Modular services (12+ apps)
│   ├── pms/                      # Property Management System
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── dtos.py               # Pydantic DTOs
│   │   ├── routes.py             # FastAPI routes (thin!)
│   │   ├── repositories/         # Data access
│   │   │   ├── __init__.py
│   │   │   ├── guest_repo.py
│   │   │   └── reservation_repo.py
│   │   ├── use_cases/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── create_reservation.py
│   │   │   └── check_availability.py
│   │   └── contracts/            # Implementation of contracts
│   │       └── pms_contract_impl.py
│   │
│   ├── hrm/                      # HR Management
│   │   └── ...
│   ├── accounting/               # Accounting
│   │   └── ...
│   └── [12+ services lainnya]
│
├── shared/                       # Shared across ALL services
│   ├── __init__.py
│   ├── config.py                 # App configuration
│   ├── database.py               # DB connection
│   ├── exceptions.py             # Base exceptions
│   ├── api_routes.py             # Centralized route registry
│   ├── contracts/                # Contracts/Interfaces
│   │   ├── __init__.py
│   │   ├── pms_contract.py
│   │   ├── hrm_contract.py
│   │   └── accounting_contract.py
│   ├── base/                     # Base classes
│   │   ├── repository.py
│   │   └── use_case.py
│   └── utils/                    # Common utilities
│       ├── pagination.py
│       └── validators.py
│
├── main.py                       # FastAPI app entry
└── requirements.txt
```

---

### 10.4 Frontend Folder Structure

```
cms-vite/
├── src/
│   ├── api/
│   │   ├── generated/           # Kubb generated (JANGAN EDIT!)
│   │   │   ├── types/
│   │   │   ├── zod/
│   │   │   └── hooks/
│   │   └── client.ts            # Axios instance
│   │
│   ├── features/                # Feature modules
│   │   ├── pms/                 # PMS module
│   │   │   ├── reservations/
│   │   │   │   ├── api/         # API-specific (extend generated)
│   │   │   │   ├── components/  # UI components
│   │   │   │   ├── hooks/       # Custom hooks
│   │   │   │   └── types/       # Additional types
│   │   │   ├── guests/
│   │   │   └── rooms/
│   │   ├── hrm/
│   │   └── accounting/
│   │
│   ├── shared/                  # Shared across features
│   │   ├── components/          # Reusable UI
│   │   │   ├── ui/              # Base components (shadcn)
│   │   │   ├── forms/           # Form components
│   │   │   └── layouts/         # Layout components
│   │   ├── hooks/               # Shared hooks
│   │   ├── utils/               # Utilities
│   │   └── types/               # Global types
│   │
│   ├── stores/                  # Global state (Zustand)
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   │
│   ├── router/                  # Route definitions
│   └── App.tsx
│
├── e2e/                         # Playwright tests
├── kubb.config.ts
└── vite.config.ts
```

---

### 10.5 Single Responsibility - Kapan Split?

**TIDAK ADA batas baris yang kaku!** Fokus pada Single Responsibility:

```
╔═══════════════════════════════════════════════════════════════════════╗
║  KAPAN HARUS SPLIT?                                                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  SPLIT ketika:                                                         ║
║  ✅ Class/function punya lebih dari 1 alasan untuk berubah            ║
║  ✅ Sulit menjelaskan apa yang dilakukan dalam 1 kalimat              ║
║  ✅ Banyak if/else yang handle cases berbeda                          ║
║  ✅ Sulit dites tanpa setup yang kompleks                             ║
║  ✅ Copy-paste logic di tempat lain                                   ║
║                                                                        ║
║  JANGAN SPLIT ketika:                                                  ║
║  ❌ Hanya karena "file terlalu panjang"                               ║
║  ❌ Logic masih cohesive dan related                                  ║
║  ❌ Split malah bikin navigasi lebih susah                            ║
║  ❌ Premature optimization                                             ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Contoh: Use Case yang BENAR walau panjang**

```python
# services/pms/use_cases/process_checkout.py
# File ini 500+ baris, TAPI ini BENAR karena:
# - Semua logic related ke 1 proses: checkout
# - Tidak ada logic yang bisa di-reuse di tempat lain
# - Kalau di-split, malah susah follow flownya

class ProcessCheckoutUseCase:
    """
    Handle complete checkout process.

    Single Responsibility: "Process guest checkout"
    Semua di sini related ke checkout, jadi 1 file OK.
    """

    async def execute(self, folio_id: int) -> CheckoutResult:
        # 1. Validate folio
        folio = await self._validate_folio(folio_id)

        # 2. Calculate final charges
        charges = await self._calculate_charges(folio)

        # 3. Process payment
        payment = await self._process_payment(folio, charges)

        # 4. Update room status
        await self._release_room(folio)

        # 5. Generate invoice
        invoice = await self._generate_invoice(folio, charges)

        # 6. Send notification
        await self._send_notification(folio, invoice)

        # 7. Audit log
        await self._log_checkout(folio)

        return CheckoutResult(...)

    # Private methods - semua related ke checkout
    async def _validate_folio(self, folio_id: int) -> Folio: ...
    async def _calculate_charges(self, folio: Folio) -> Charges: ...
    async def _process_payment(self, folio: Folio, charges: Charges) -> Payment: ...
    async def _release_room(self, folio: Folio) -> None: ...
    async def _generate_invoice(self, folio: Folio, charges: Charges) -> Invoice: ...
    async def _send_notification(self, folio: Folio, invoice: Invoice) -> None: ...
    async def _log_checkout(self, folio: Folio) -> None: ...
```

**Contoh: Kapan HARUS Split**

```python
# ❌ SALAH: 1 file handle terlalu banyak tanggung jawab
# services/pms/use_cases/guest_operations.py
class GuestOperationsUseCase:
    async def create_guest(self, dto): ...      # Responsibility 1
    async def update_guest(self, dto): ...      # Responsibility 1
    async def check_in_guest(self, dto): ...    # Responsibility 2 - BEDA!
    async def check_out_guest(self, dto): ...   # Responsibility 3 - BEDA!
    async def generate_invoice(self, dto): ...  # Responsibility 4 - BEDA!


# ✅ BENAR: Split per responsibility
# services/pms/use_cases/create_guest.py
class CreateGuestUseCase: ...

# services/pms/use_cases/update_guest.py
class UpdateGuestUseCase: ...

# services/pms/use_cases/process_checkin.py
class ProcessCheckInUseCase: ...

# services/pms/use_cases/process_checkout.py
class ProcessCheckoutUseCase: ...

# services/accounting/use_cases/generate_invoice.py
class GenerateInvoiceUseCase: ...  # Ini bahkan pindah ke service lain!
```

---

### 10.6 Dependency Flow

```
╔═══════════════════════════════════════════════════════════════════════╗
║  DEPENDENCY DIRECTION (Clean Architecture)                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║       OUTER LAYERS                    INNER LAYERS                    ║
║  ┌─────────────────┐             ┌─────────────────┐                  ║
║  │    Routes       │────────────▶│   Use Cases     │                  ║
║  │   (FastAPI)     │             │  (Business)     │                  ║
║  └─────────────────┘             └────────┬────────┘                  ║
║                                           │                           ║
║  ┌─────────────────┐                      │                           ║
║  │  Repositories   │◀─────────────────────┘                           ║
║  │ (Data Access)   │                                                  ║
║  └────────┬────────┘                                                  ║
║           │                                                           ║
║           ▼                                                           ║
║  ┌─────────────────┐                                                  ║
║  │    Models       │  ← Entities, paling dalam                        ║
║  │   (Domain)      │                                                  ║
║  └─────────────────┘                                                  ║
║                                                                        ║
║  RULES:                                                               ║
║  • Routes depend on Use Cases (✅)                                    ║
║  • Use Cases depend on Repositories (✅)                              ║
║  • Use Cases depend on Models/Entities (✅)                           ║
║  • Models TIDAK depend ke siapapun (✅)                               ║
║  • Use Cases TIDAK depend ke Routes (❌)                              ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 10.7 File Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| **Use Case** | `{verb}_{noun}.py` | `create_reservation.py` |
| **Repository** | `{noun}_repo.py` | `guest_repo.py` |
| **Model** | `{noun}_model.py` atau di `models.py` | `guest_model.py` |
| **DTO** | di `dtos.py` | `CreateGuestDTO` |
| **Route** | `routes.py` per service | `services/pms/routes.py` |
| **Contract** | `{service}_contract.py` | `pms_contract.py` |
| **React Component** | `{Name}.tsx` (PascalCase) | `ReservationForm.tsx` |
| **React Hook** | `use{Name}.ts` | `useReservationForm.ts` |
| **Zustand Store** | `{name}Store.ts` | `authStore.ts` |

---

### 10.8 Import Rules

```python
# ✅ BENAR: Import order dan grouping
# 1. Standard library
from datetime import date
from typing import Optional, List

# 2. Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. Shared (project-wide)
from shared.database import get_db
from shared.exceptions import NotFoundError
from shared.contracts.pms_contract import PMSContract

# 4. Same service (local)
from .repositories.guest_repo import GuestRepository
from .dtos import CreateGuestDTO


# ❌ SALAH: Import dari service lain
from services.hrm.repositories.employee_repo import EmployeeRepository  # NO!
from services.accounting.use_cases.create_invoice import CreateInvoiceUseCase  # NO!
```

---

### 10.9 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Architecture** | Modular Monolith (deploy 1, struktur ready split) |
| **Service Communication** | Via contracts/interfaces, BUKAN direct import |
| **File Size** | Tidak ada batas baris, fokus Single Responsibility |
| **Split Criteria** | Split kalau punya >1 alasan berubah |
| **Dependency** | Outer → Inner only, never reverse |
| **Folder Structure** | Feature-based, max 3 level depth |
| **Imports** | Standard → Third-party → Shared → Local |
| **Future Microservices** | Contract jadi API boundary

---

## 11. Frontend Patterns ✅

### 11.0 Prinsip Frontend

```
╔═══════════════════════════════════════════════════════════════════════╗
║  FRONTEND PRINCIPLES                                                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. SEPARATION OF CONCERNS  → State, UI, Logic terpisah jelas        ║
║  2. COMPOSITION > INHERITANCE → Compose components, jangan extend    ║
║  3. COLOCATION             → Taruh code dekat dengan yang pakai      ║
║  4. SINGLE SOURCE          → 1 source untuk setiap data/state        ║
║  5. PROGRESSIVE ENHANCEMENT → Core features work, enhance gradually  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.1 Tech Stack Frontend

```
╔═══════════════════════════════════════════════════════════════════════╗
║  FRONTEND TECH STACK                                                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  RUNTIME & TOOLING                                                     ║
║  ├── Bun           → Package manager + runtime (bukan npm/node)       ║
║  ├── Vite          → Dev server + bundler (HMR, build)               ║
║  └── TypeScript    → Type safety                                      ║
║                                                                        ║
║  UI FRAMEWORK                                                          ║
║  ├── React 18+     → UI library                                       ║
║  ├── Tailwind CSS  → Utility-first styling                           ║
║  └── shadcn/ui     → Component library (Radix-based)                 ║
║                                                                        ║
║  STATE MANAGEMENT                                                      ║
║  ├── Zustand       → Global state (auth, UI preferences)             ║
║  ├── TanStack Query→ Server state (data fetching, caching)           ║
║  └── React Hook Form → Form state                                     ║
║                                                                        ║
║  DATA & TABLES                                                         ║
║  ├── TanStack Table → Headless table (pagination, sorting, filter)   ║
║  └── TanStack Virtual → Virtual scrolling untuk list panjang         ║
║                                                                        ║
║  VALIDATION (Generated)                                                ║
║  ├── Kubb          → Generate dari OpenAPI                            ║
║  └── Zod           → Schema validation (generated)                    ║
║                                                                        ║
║  I18N                                                                  ║
║  └── Lingui        → Compile-time i18n, ICU standard                 ║
║                                                                        ║
║  NOTIFICATIONS                                                         ║
║  └── Sonner        → Toast notifications                              ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.2 State Management Pattern

```
╔═══════════════════════════════════════════════════════════════════════╗
║  STATE SEPARATION - Setiap state punya tempatnya                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ZUSTAND (Global UI State)                                            ║
║  ├── Auth state (user, permissions)                                  ║
║  ├── UI preferences (sidebar open, theme)                            ║
║  └── App-wide state yang persist                                      ║
║                                                                        ║
║  TANSTACK QUERY (Server State)                                        ║
║  ├── Data dari API                                                    ║
║  ├── Caching otomatis                                                 ║
║  ├── Background refetch                                               ║
║  └── Optimistic updates                                               ║
║                                                                        ║
║  REACT HOOK FORM (Form State)                                         ║
║  ├── Form values                                                      ║
║  ├── Validation state                                                 ║
║  ├── Dirty/touched state                                              ║
║  └── Submit handling                                                  ║
║                                                                        ║
║  LOCAL STATE (useState)                                               ║
║  ├── Component-specific UI state                                     ║
║  ├── Modal open/close                                                 ║
║  └── Temporary state                                                  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```typescript
// ✅ BENAR: State sesuai tempatnya

// Zustand - Global auth
const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  permissions: [],
  setUser: (user) => set({ user }),
  logout: () => set({ user: null, permissions: [] })
}));

// TanStack Query - Server data
const { data: reservations, isLoading } = useQuery({
  queryKey: ['reservations', filters],
  queryFn: () => fetchReservations(filters)
});

// React Hook Form - Form state
const form = useForm<CreateReservationDTO>({
  resolver: zodResolver(createReservationSchema)
});

// Local state - Component UI
const [isModalOpen, setIsModalOpen] = useState(false);
```

---

### 11.3 Component Library Pattern

```
╔═══════════════════════════════════════════════════════════════════════╗
║  COMPONENT ORGANIZATION                                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  src/shared/components/                                                ║
║  ├── ui/                  ← shadcn/ui base components                 ║
║  │   ├── button.tsx                                                   ║
║  │   ├── input.tsx                                                    ║
║  │   ├── dialog.tsx                                                   ║
║  │   └── ...                                                          ║
║  ├── forms/               ← Form wrappers                             ║
║  │   ├── FormField.tsx                                                ║
║  │   ├── FormSelect.tsx                                               ║
║  │   └── FormDatePicker.tsx                                           ║
║  ├── data/                ← Data display components                   ║
║  │   ├── DataTable.tsx    ← TanStack Table wrapper                    ║
║  │   ├── DataCard.tsx                                                 ║
║  │   └── EmptyState.tsx                                               ║
║  └── layouts/             ← Layout components                         ║
║      ├── Sidebar.tsx                                                  ║
║      ├── Header.tsx                                                   ║
║      └── PageContainer.tsx                                            ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Semua apps import dari shared:**
```typescript
// ✅ BENAR: Import dari shared
import { Button, Input } from '@/shared/components/ui';
import { DataTable } from '@/shared/components/data';
import { FormField } from '@/shared/components/forms';

// ❌ SALAH: Buat component sendiri yang duplikat
import { MyButton } from './MyButton'; // Jangan!
```

---

### 11.4 Data Table Pattern

```typescript
// shared/components/data/DataTable.tsx
// Wrapper untuk TanStack Table dengan fitur standar

interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];

  // Pagination (server-side)
  pagination?: PaginationState;
  onPaginationChange?: (pagination: PaginationState) => void;
  pageCount?: number;

  // Sorting (server-side)
  sorting?: SortingState;
  onSortingChange?: (sorting: SortingState) => void;

  // Row selection
  enableRowSelection?: boolean;
  onRowSelectionChange?: (rows: TData[]) => void;

  // Loading & empty
  isLoading?: boolean;
  emptyMessage?: string;
}

// Usage di feature
function ReservationList() {
  const { data, isLoading } = useReservations(filters);

  return (
    <DataTable
      columns={reservationColumns}
      data={data?.items ?? []}
      pagination={pagination}
      onPaginationChange={setPagination}
      pageCount={data?.meta.totalPages}
      isLoading={isLoading}
      emptyMessage="No reservations found"
    />
  );
}
```

---

### 11.5 Auth Flow Pattern

```
╔═══════════════════════════════════════════════════════════════════════╗
║  AUTH FLOW - httpOnly Cookie                                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  LOGIN FLOW                                                            ║
║  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐            ║
║  │  User   │───▶│ Login   │───▶│ Backend │───▶│ Set     │            ║
║  │ Submit  │    │  API    │    │ Verify  │    │ Cookie  │            ║
║  └─────────┘    └─────────┘    └─────────┘    └─────────┘            ║
║                                                     │                  ║
║                                                     ▼                  ║
║  ┌─────────┐    ┌─────────┐    ┌─────────────────────────┐            ║
║  │Redirect │◀───│ Store   │◀───│ httpOnly Cookie         │            ║
║  │Dashboard│    │ User    │    │ (Frontend tidak pegang) │            ║
║  └─────────┘    └─────────┘    └─────────────────────────┘            ║
║                                                                        ║
║  TOKEN REFRESH                                                         ║
║  ├── Access Token: 15 menit                                           ║
║  ├── Refresh Token: 7 hari                                            ║
║  ├── Auto-refresh sebelum expire                                      ║
║  └── Backend handle via cookie                                        ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```typescript
// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) return <PageSkeleton />;

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Permission-based rendering
function Can({
  permission,
  children
}: {
  permission: string;
  children: React.ReactNode
}) {
  const { hasPermission } = useAuthStore();

  if (!hasPermission(permission)) return null;

  return <>{children}</>;
}

// Usage
<Can permission="reservation.create">
  <Button>Create Reservation</Button>
</Can>
```

---

### 11.6 Error Handling UI

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ERROR HANDLING UI                                                     ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  TOAST (Sonner)                                                        ║
║  ├── Success: toast.success("Reservation created")                   ║
║  ├── Error: toast.error("Failed to create")                          ║
║  ├── Warning: toast.warning("Session expiring")                      ║
║  └── Info: toast.info("New update available")                        ║
║                                                                        ║
║  FORM ERRORS                                                           ║
║  ├── Field-level: di bawah input                                     ║
║  ├── Form-level: di atas form                                         ║
║  └── Server errors di-map ke fields                                   ║
║                                                                        ║
║  PAGE ERRORS                                                           ║
║  ├── 404: NotFoundPage                                                ║
║  ├── 403: ForbiddenPage                                               ║
║  ├── 500: ServerErrorPage                                             ║
║  └── Offline: OfflinePage                                             ║
║                                                                        ║
║  ERROR BOUNDARY                                                        ║
║  └── Catch React errors, show fallback UI                             ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```typescript
// API error handling utility
function handleApiError(error: ApiError, form?: UseFormReturn) {
  // Validation errors → map ke form fields
  if (error.code === 'VALIDATION_ERROR' && form) {
    error.details?.forEach(({ field, message }) => {
      form.setError(field, { message });
    });
    return;
  }

  // Auth errors → redirect
  if (error.code === 'AUTH_UNAUTHORIZED') {
    window.location.href = '/login';
    return;
  }

  // Business errors → toast
  toast.error(error.message);
}
```

---

### 11.7 Loading States

```typescript
// 1. Skeleton untuk initial load
function ReservationPage() {
  const { data, isLoading } = useReservations();

  if (isLoading) return <ReservationSkeleton />;

  return <ReservationList data={data} />;
}

// 2. Button loading saat submit
<Button disabled={mutation.isPending}>
  {mutation.isPending && <Spinner className="mr-2" />}
  Create Reservation
</Button>

// 3. Table loading (keep data visible)
<DataTable
  data={data}
  isLoading={isFetching}  // Overlay, tapi data tetap visible
/>

// 4. Route-based lazy loading
const ReservationPage = lazy(() => import('./pages/ReservationPage'));

<Suspense fallback={<PageSkeleton />}>
  <ReservationPage />
</Suspense>
```

---

### 11.8 i18n Pattern (Lingui)

```typescript
// lingui.config.ts
export default {
  locales: ['id', 'en'],
  sourceLocale: 'id',
  catalogs: [{
    path: 'src/locales/{locale}',
    include: ['src']
  }]
};

// Usage dengan macro
import { t, Trans } from '@lingui/macro';

function ReservationForm() {
  return (
    <form>
      <label>{t`Guest Name`}</label>
      <Button>
        <Trans>Create Reservation</Trans>
      </Button>
    </form>
  );
}

// Plural handling
t`${count} reservation`;  // Auto-handle plurals

// Extract & compile
// bun run lingui:extract
// bun run lingui:compile
```

---

### 11.9 Performance Patterns

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PERFORMANCE PATTERNS                                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. CODE SPLITTING                                                     ║
║     └── Setiap module (PMS, HRM, dll) = chunk terpisah               ║
║                                                                        ║
║  2. LAZY LOADING                                                       ║
║     └── Heavy components: Charts, Editors, Modals                     ║
║                                                                        ║
║  3. VIRTUAL SCROLLING                                                  ║
║     └── TanStack Virtual untuk list 1000+ items                       ║
║                                                                        ║
║  4. MEMOIZATION (hanya jika perlu!)                                   ║
║     ├── React.memo() untuk expensive render                          ║
║     ├── useMemo() untuk expensive calculation                        ║
║     └── JANGAN overuse!                                               ║
║                                                                        ║
║  5. IMAGE OPTIMIZATION                                                 ║
║     ├── Lazy load                                                     ║
║     ├── WebP format                                                   ║
║     └── CDN                                                           ║
║                                                                        ║
║  6. TANSTACK QUERY CACHING                                            ║
║     ├── staleTime: 5 menit (data jarang berubah)                     ║
║     ├── staleTime: 0 (data sering berubah)                           ║
║     └── Optimistic updates untuk UX instant                          ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.10 Accessibility

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ACCESSIBILITY - Built-in dari shadcn/ui                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  OTOMATIS (dari Radix UI):                                            ║
║  ├── Keyboard navigation                                              ║
║  ├── ARIA attributes                                                  ║
║  ├── Focus management                                                 ║
║  └── Screen reader support                                            ║
║                                                                        ║
║  YANG PERLU DIJAGA:                                                    ║
║  ├── Semantic HTML (<button>, <nav>, <main>)                         ║
║  ├── Alt text untuk images                                            ║
║  ├── Label untuk form inputs                                          ║
║  └── Sufficient color contrast                                        ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.11 Additional Libraries

#### Routing (TanStack Router)

```typescript
// 100% typesafe routing
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/reservations/$id')({
  component: ReservationDetail,
  loader: ({ params }) => fetchReservation(params.id),  // typed!
});

// Usage
const { id } = Route.useParams();  // id: string (typed!)
const { status } = Route.useSearch();  // Fully typed search params
```

#### Date/Time (date-fns)

```typescript
import { format, differenceInDays, addDays } from 'date-fns';
import { id } from 'date-fns/locale';  // Indonesian locale

// Format
format(checkInDate, 'dd MMMM yyyy', { locale: id });  // "15 Januari 2025"

// Calculate nights
const nights = differenceInDays(checkOutDate, checkInDate);  // 3

// Add days
const checkOut = addDays(checkInDate, 3);
```

#### Charts (ECharts)

```typescript
import ReactECharts from 'echarts-for-react';

// 50+ chart types, WebGL support untuk data besar
<ReactECharts
  option={{
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value' },
    series: [{ data: occupancyData, type: 'bar' }]
  }}
/>
```

#### Rich Text Editor (Tiptap)

```typescript
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

// Headless, extensible, open source
const editor = useEditor({
  extensions: [StarterKit],
  content: '<p>Guest notes here...</p>',
});

<EditorContent editor={editor} />
```

#### Dark Mode (next-themes)

```typescript
// Theme Provider
import { ThemeProvider } from 'next-themes';

<ThemeProvider attribute="class" defaultTheme="system">
  <App />
</ThemeProvider>

// Theme Toggle
import { useTheme } from 'next-themes';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <Button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  );
}

// Tailwind config
// darkMode: 'class'
```

---

### 11.12 PDF & Print System

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PDF GENERATION - PLAYWRIGHT (Backend)                                 ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  APPROACH:                                                             ║
║  ├── Template: HTML + Tailwind + Jinja2                               ║
║  ├── Render: Playwright (headless browser)                            ║
║  ├── Output: PDF 100% sama dengan layar                               ║
║  └── Storage: MinIO/S3                                                ║
║                                                                        ║
║  FLOW:                                                                 ║
║  Request → Render HTML → Playwright → PDF → Storage → URL             ║
║                                                                        ║
║  USE CASES:                                                            ║
║  ├── Invoice / Folio                                                  ║
║  ├── Receipt                                                          ║
║  ├── Registration Card                                                ║
║  ├── Reports (occupancy, revenue, audit)                             ║
║  └── Batch generation (night audit)                                   ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```python
# Backend PDF Generation
async def generate_pdf(template: str, data: dict) -> bytes:
    html = render_template(f"pdf/{template}.html", data=data)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        pdf_bytes = await page.pdf(format="A4")
        await browser.close()

    return pdf_bytes
```

---

### 11.13 Report Builder (Future Phase)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  CUSTOM REPORT BUILDER - Phase Akhir                                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  FEATURES:                                                             ║
║  ├── Level 1: Template Library (developer share templates)           ║
║  ├── Level 2: Admin Customization (logo, columns, styling)          ║
║  └── Level 3: Full Report Builder (SQL query + drag & drop layout)  ║
║                                                                        ║
║  COMPONENTS:                                                           ║
║  ├── Query Builder: react-querybuilder                               ║
║  ├── Layout Designer: @dnd-kit + react-grid-layout                   ║
║  ├── Styling: Tailwind                                                ║
║  ├── Template Storage: PostgreSQL (JSONB)                            ║
║  └── PDF Export: Playwright                                           ║
║                                                                        ║
║  DATABASE:                                                             ║
║  ├── report_templates (organization_id, name, data_source, layout)  ║
║  └── generated_reports (template_id, parameters, pdf_url)           ║
║                                                                        ║
║  PRIORITY: Develop after core PMS features complete                   ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.14 Thermal Printer (POS)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  THERMAL PRINTER - Restaurant & Purchasing                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  USE CASES:                                                            ║
║  ├── Restaurant receipt (58mm/80mm)                                   ║
║  ├── Purchasing receipt                                               ║
║  └── Kitchen order ticket                                             ║
║                                                                        ║
║  APPROACH:                                                             ║
║  ├── ESC/POS commands untuk thermal printer                          ║
║  ├── WebSocket/USB connection                                        ║
║  └── Fixed template format                                            ║
║                                                                        ║
║  PRIORITY: Develop dengan POS module                                  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 11.15 Ringkasan Lengkap

| Category | Stack/Pattern |
|----------|---------------|
| **Runtime** | Bun |
| **Bundler** | Vite |
| **UI Framework** | React 18+ |
| **Styling** | Tailwind CSS |
| **Components** | shadcn/ui |
| **Routing** | TanStack Router |
| **Global State** | Zustand |
| **Server State** | TanStack Query |
| **Forms** | React Hook Form + Zod (generated) |
| **Tables** | TanStack Table |
| **Virtual Scroll** | TanStack Virtual |
| **Date/Time** | date-fns |
| **Charts** | ECharts |
| **Rich Text** | Tiptap |
| **i18n** | Lingui |
| **Toast** | Sonner |
| **Auth** | httpOnly Cookie |
| **Dark Mode** | next-themes |
| **PDF Generation** | Playwright (backend) |
| **Report Builder** | Custom (future phase) |
| **Accessibility** | shadcn/ui (built-in) |

---

## 12. Infrastructure & DevOps ✅

### 12.0 Prinsip Infrastructure

```
╔═══════════════════════════════════════════════════════════════════════╗
║  INFRASTRUCTURE PRINCIPLES                                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. START SMALL, SCALE BIG  → Arsitektur sama dari awal sampai 500+ ║
║  2. OBSERVABLE              → Logs, metrics, traces di semua layer   ║
║  3. RESILIENT               → Handle failures gracefully             ║
║  4. SECURE BY DEFAULT       → Full compliance dari awal              ║
║  5. AUTOMATED               → CI/CD, auto-scaling, self-healing      ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.1 Multi-Tenancy Architecture

```
╔═══════════════════════════════════════════════════════════════════════╗
║  DATABASE-PER-TENANT + SCHEMA-PER-APP                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  Hotel A (Database: hotel_a_db)                                       ║
║  ├── Schema: pms          → Reservations, Rooms, Rates               ║
║  ├── Schema: accounting   → GL, AP, AR, Journal                      ║
║  ├── Schema: hrm          → Employees, Payroll                       ║
║  ├── Schema: inventory    → Stock, Purchase                          ║
║  └── Schema: shared       → Users, Audit, Settings                   ║
║                                                                        ║
║  Hotel B (Database: hotel_b_db)                                       ║
║  ├── Schema: pms                                                      ║
║  ├── Schema: accounting                                               ║
║  └── ...                                                              ║
║                                                                        ║
║  Central Platform (Database: central_db)                              ║
║  ├── User authentication                                              ║
║  ├── Cross-organization relationships                                 ║
║  ├── Platform analytics                                               ║
║  └── Billing & subscription                                           ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Keuntungan:**
- ✅ Isolasi penuh antar hotel (database level)
- ✅ Isolasi antar modul (schema level)
- ✅ Backup per hotel mudah
- ✅ Migrasi schema per app independent
- ✅ Permission granular per schema

---

### 12.2 Tech Stack Infrastructure

```
╔═══════════════════════════════════════════════════════════════════════╗
║  INFRASTRUCTURE TECH STACK                                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  DATABASE                                                              ║
║  ├── TimescaleDB        → PostgreSQL + time-series extension          ║
║  └── PgBouncer          → Connection pooling (10,000+ connections)   ║
║                                                                        ║
║  CACHING & SESSION                                                     ║
║  └── Redis              → Session, cache, rate limiting, pub/sub     ║
║                                                                        ║
║  MESSAGE BROKER                                                        ║
║  └── RabbitMQ           → Event-driven messaging                      ║
║                                                                        ║
║  BACKGROUND JOBS                                                       ║
║  └── Dramatiq + RabbitMQ → Async task processing                     ║
║                                                                        ║
║  FILE STORAGE                                                          ║
║  └── Cloudflare R2      → S3-compatible, zero egress fee, CDN        ║
║                                                                        ║
║  SEARCH                                                                ║
║  └── Meilisearch        → Full-text search, typo-tolerant            ║
║                                                                        ║
║  REAL-TIME                                                             ║
║  └── Centrifugo         → WebSocket server, scalable                 ║
║                                                                        ║
║  ORCHESTRATION                                                         ║
║  └── Docker Swarm       → Container orchestration                    ║
║                                                                        ║
║  MONITORING                                                            ║
║  ├── Prometheus         → Metrics collection                         ║
║  ├── Grafana            → Dashboards & visualization                 ║
║  └── Jaeger             → Distributed tracing                        ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.3 Event-Driven Architecture (RabbitMQ)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  EVENT-DRIVEN WITH RABBITMQ                                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌─────────────────────────────────────────────────────────┐          ║
║  │                     Services                             │          ║
║  ├─────────────────────────────────────────────────────────┤          ║
║  │  PMS  │ Accounting │  HRM  │  POS  │  Reports          │          ║
║  └───┬───┴─────┬──────┴───┬───┴───┬───┴─────┬─────────────┘          ║
║      │         │          │       │         │                         ║
║      ▼         ▼          ▼       ▼         ▼                         ║
║  ┌─────────────────────────────────────────────────────────┐          ║
║  │              RabbitMQ (Events)                          │          ║
║  │  exchanges:                                              │          ║
║  │  ├── events.reservation (created, modified, cancelled) │          ║
║  │  ├── events.payment (received, failed, refunded)       │          ║
║  │  ├── events.checkout (completed, no_show)              │          ║
║  │  ├── events.inventory (low_stock, received)            │          ║
║  │  └── events.notification (email, sms, push)            │          ║
║  └─────────────────────────────────────────────────────────┘          ║
║                                                                        ║
║  USE CASES:                                                            ║
║  ├── reservation_created → Accounting create invoice                 ║
║  ├── payment_received    → Update AR, trigger receipt                ║
║  ├── checkout_completed  → Revenue posting, room status              ║
║  └── night_audit         → Batch processing semua modul              ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.4 Background Jobs (Dramatiq)

```python
# Dramatiq - Simple API, reuse RabbitMQ broker

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

broker = RabbitmqBroker(url="amqp://guest:guest@rabbitmq:5672")
dramatiq.set_broker(broker)

@dramatiq.actor
def run_night_audit(hotel_id: int):
    """Night audit processing - runs daily at 02:00."""
    process_daily_charges(hotel_id)
    calculate_revenue(hotel_id)
    generate_daily_report(hotel_id)

@dramatiq.actor
def generate_report(report_type: str, params: dict):
    """Heavy report generation."""
    data = fetch_report_data(report_type, params)
    pdf = generate_pdf(data)
    upload_to_storage(pdf)
    notify_user(params["user_id"])

@dramatiq.actor
def send_email(to: str, template: str, data: dict):
    """Email notification."""
    html = render_template(template, data)
    send_via_email_service(to, html)

# Usage
run_night_audit.send(hotel_id=123)
generate_report.send(report_type="revenue", params={...})
```

**Task Categories:**
| Category | Examples | Priority |
|----------|----------|----------|
| **Critical** | Night audit, payment processing | High, retry 3x |
| **Important** | Report generation, data sync | Medium, retry 5x |
| **Background** | Email, notifications, cleanup | Low, retry 10x |

---

### 12.5 File Storage (Cloudflare R2)

```python
# S3-compatible API - same code for R2 or MinIO

import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://xxx.r2.cloudflarestorage.com',
    aws_access_key_id=settings.R2_ACCESS_KEY,
    aws_secret_access_key=settings.R2_SECRET_KEY,
    config=Config(signature_version='s3v4')
)

# Upload file
s3.upload_file(
    'invoice.pdf',
    'hotel-a',
    'invoices/2025/01/INV-001.pdf'
)

# Generate presigned URL (for frontend download)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'hotel-a', 'Key': 'invoices/2025/01/INV-001.pdf'},
    ExpiresIn=3600  # 1 hour
)
```

**Bucket Structure:**
```
Cloudflare R2 Buckets:
├── hotel-{id}/
│   ├── guests/           → ID scans, passport
│   ├── documents/        → Contracts
│   ├── invoices/         → Generated PDFs
│   └── reports/          → Generated reports
└── shared/
    └── templates/        → Report templates
```

**Keuntungan R2:**
- ✅ Zero egress fee (download gratis)
- ✅ Built-in CDN
- ✅ S3-compatible
- ✅ ~$7.50/bulan untuk 500GB

---

### 12.6 Real-time Communication (Centrifugo)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  CENTRIFUGO - REAL-TIME WEBSOCKET                                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────────────────────────────────────────────────┐         ║
║  │              Architecture                                 │         ║
║  ├──────────────────────────────────────────────────────────┤         ║
║  │  Frontend ←──WebSocket──→ Centrifugo                     │         ║
║  │                              ↑                           │         ║
║  │                         Redis Pub/Sub                    │         ║
║  │                              ↑                           │         ║
║  │  Backend (FastAPI) ─────publish──────                    │         ║
║  └──────────────────────────────────────────────────────────┘         ║
║                                                                        ║
║  CHANNELS:                                                             ║
║  ├── hotel:{id}:rooms       → Room status updates                    ║
║  ├── hotel:{id}:reservations → New bookings, modifications           ║
║  ├── hotel:{id}:notifications → Staff notifications                  ║
║  └── user:{id}              → Personal notifications                 ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```python
# Backend - Publish to Centrifugo
from cent import Client

centrifugo = Client(
    address="http://centrifugo:8000/api",
    api_key=settings.CENTRIFUGO_API_KEY
)

# Publish room status change
async def publish_room_update(hotel_id: int, room_id: int, status: str):
    await centrifugo.publish(
        channel=f"hotel:{hotel_id}:rooms",
        data={"room_id": room_id, "status": status}
    )
```

```typescript
// Frontend - Subscribe to channel
import { Centrifuge } from 'centrifuge';

const centrifuge = new Centrifuge('wss://realtime.example.com/connection/websocket');

const sub = centrifuge.newSubscription(`hotel:${hotelId}:rooms`);
sub.on('publication', (ctx) => {
  console.log('Room update:', ctx.data);
  // Update UI
});

sub.subscribe();
centrifuge.connect();
```

---

### 12.7 Caching Strategy (Redis)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  CACHING PATTERNS BY DATA TYPE                                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────────┬──────────────────────────────────────┐          ║
║  │ Data             │ Pattern & TTL                        │          ║
║  ├──────────────────┼──────────────────────────────────────┤          ║
║  │ Room rates       │ Cache-aside, TTL 5 min              │          ║
║  │ Room availability│ Cache-aside, TTL 1 min              │          ║
║  │ Hotel settings   │ Cache-aside, TTL 1 hour             │          ║
║  │ User session     │ Write-through (always fresh)        │          ║
║  │ Report cache     │ Cache-aside, TTL 15 min             │          ║
║  │ Exchange rates   │ Cache-aside, TTL 1 hour             │          ║
║  │ Menu items       │ Cache-aside, TTL 30 min             │          ║
║  └──────────────────┴──────────────────────────────────────┘          ║
║                                                                        ║
║  REDIS USE CASES:                                                      ║
║  ├── Session storage (JWT, user sessions)                            ║
║  ├── API rate limiting per tenant                                    ║
║  ├── Real-time room availability                                     ║
║  ├── Pub/Sub for notifications                                       ║
║  ├── Distributed locks (prevent double booking)                      ║
║  └── Query result caching                                            ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```python
# Cache-aside pattern
async def get_room_rates(hotel_id: int, date: date) -> list[Rate]:
    cache_key = f"rates:{hotel_id}:{date.isoformat()}"

    # 1. Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Cache miss - fetch from DB
    rates = await rate_repo.get_by_date(hotel_id, date)

    # 3. Store in cache
    await redis.setex(cache_key, 300, json.dumps(rates))  # 5 min TTL

    return rates

# Cache invalidation on write
async def update_rate(hotel_id: int, rate: Rate):
    await rate_repo.update(rate)

    # Invalidate cache
    pattern = f"rates:{hotel_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
```

---

### 12.8 Logging Standard (Structured JSON)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  STRUCTURED LOGGING                                                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  FORMAT: JSON (machine-readable)                                       ║
║                                                                        ║
║  {                                                                     ║
║    "timestamp": "2025-01-15T10:30:00.123Z",                           ║
║    "level": "INFO",                                                    ║
║    "correlation_id": "abc-123-def-456",                               ║
║    "service": "pms",                                                   ║
║    "message": "Reservation created",                                   ║
║    "context": {                                                        ║
║      "reservation_id": 12345,                                          ║
║      "hotel_id": 1,                                                    ║
║      "user_id": 42                                                     ║
║    }                                                                   ║
║  }                                                                     ║
║                                                                        ║
║  LOG LEVELS:                                                           ║
║  ├── DEBUG   → Detailed debugging info                               ║
║  ├── INFO    → Normal operations                                     ║
║  ├── WARNING → Recoverable issues                                    ║
║  ├── ERROR   → Failures that need attention                          ║
║  └── CRITICAL→ System failures                                       ║
║                                                                        ║
║  CORRELATION ID:                                                       ║
║  ├── Generated at API gateway                                        ║
║  ├── Passed through all services                                     ║
║  ├── Included in all logs                                            ║
║  └── Used for distributed tracing                                    ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Usage with context
async def create_reservation(dto: CreateReservationDTO):
    log = logger.bind(
        correlation_id=get_correlation_id(),
        hotel_id=dto.hotel_id,
        user_id=current_user.id
    )

    log.info("Creating reservation", guest_id=dto.guest_id)

    try:
        reservation = await repo.create(dto)
        log.info("Reservation created", reservation_id=reservation.id)
        return reservation
    except Exception as e:
        log.error("Failed to create reservation", error=str(e))
        raise
```

---

### 12.9 Security Compliance

```
╔═══════════════════════════════════════════════════════════════════════╗
║  SECURITY STANDARDS - FULL COMPLIANCE                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  OWASP TOP 10                                                          ║
║  ├── ✅ Injection prevention (parameterized queries)                 ║
║  ├── ✅ Broken authentication (JWT + httpOnly + MFA)                 ║
║  ├── ✅ Sensitive data exposure (encryption at rest/transit)         ║
║  ├── ✅ XML External Entities (disabled)                             ║
║  ├── ✅ Broken access control (RBAC + RLS)                           ║
║  ├── ✅ Security misconfiguration (hardened defaults)                ║
║  ├── ✅ XSS prevention (output encoding)                             ║
║  ├── ✅ Insecure deserialization (validated input)                   ║
║  ├── ✅ Known vulnerabilities (dependency scanning)                  ║
║  └── ✅ Insufficient logging (structured audit logs)                 ║
║                                                                        ║
║  ENCRYPTION                                                            ║
║  ├── At rest: AES-256 (database, files)                              ║
║  ├── In transit: TLS 1.3 (all connections)                           ║
║  └── Sensitive fields: Column-level encryption (PII)                 ║
║                                                                        ║
║  COMPLIANCE READY                                                      ║
║  ├── PCI-DSS: Payment card handling via gateway only                 ║
║  ├── GDPR: Consent management, data retention, right to forget       ║
║  └── Rate limiting: Brute force protection                           ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.10 Auth Flow (JWT + httpOnly Cookie)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  AUTH FLOW - JWT + httpOnly Cookie + Redis                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  LOGIN FLOW                                                            ║
║  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐            ║
║  │  User   │───▶│ Login   │───▶│ Backend │───▶│ Generate│            ║
║  │ Submit  │    │  API    │    │ Verify  │    │   JWT   │            ║
║  └─────────┘    └─────────┘    └─────────┘    └────┬────┘            ║
║                                                     │                  ║
║                                      ┌──────────────┴────────────┐    ║
║                                      │                           │    ║
║                                      ▼                           ▼    ║
║                              ┌─────────────┐            ┌─────────┐   ║
║                              │ httpOnly    │            │ Redis   │   ║
║                              │ Cookie      │            │ Refresh │   ║
║                              │ (Access)    │            │ Token   │   ║
║                              └─────────────┘            └─────────┘   ║
║                                                                        ║
║  TOKEN CONFIGURATION:                                                  ║
║  ├── Access Token: 15 menit (in httpOnly cookie)                     ║
║  ├── Refresh Token: 7 hari (in Redis)                                ║
║  ├── Auto-refresh sebelum expire                                     ║
║  └── Revocation list di Redis                                        ║
║                                                                        ║
║  SECURITY:                                                             ║
║  ├── httpOnly: Frontend tidak bisa akses token (XSS safe)           ║
║  ├── Secure: HTTPS only                                              ║
║  ├── SameSite: Strict (CSRF protection)                              ║
║  └── Redis: Centralized revocation                                   ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.11 Monitoring Stack

```
╔═══════════════════════════════════════════════════════════════════════╗
║  MONITORING - PROMETHEUS + GRAFANA + JAEGER                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  PROMETHEUS (Metrics)                                                  ║
║  ├── API latency & error rates                                       ║
║  ├── Database connection pool stats                                  ║
║  ├── Queue depth & processing time                                   ║
║  ├── Resource utilization (CPU, memory, disk)                        ║
║  └── Custom business metrics                                         ║
║                                                                        ║
║  GRAFANA (Dashboards)                                                  ║
║  ├── System Overview dashboard                                       ║
║  ├── API Performance dashboard                                       ║
║  ├── Database Health dashboard                                       ║
║  ├── Business Metrics dashboard                                      ║
║  └── Tenant Usage dashboard                                          ║
║                                                                        ║
║  JAEGER (Tracing)                                                      ║
║  ├── Request tracing across services                                 ║
║  ├── Latency analysis                                                ║
║  ├── Dependency mapping                                              ║
║  └── Error tracking                                                  ║
║                                                                        ║
║  ALERTING:                                                             ║
║  ├── API error rate > 1%                                             ║
║  ├── Response time p99 > 500ms                                       ║
║  ├── Database connections > 80%                                      ║
║  ├── Queue depth > 1000                                              ║
║  └── Disk usage > 80%                                                ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.12 Orchestration (Docker Swarm)

```yaml
# docker-compose.swarm.yml
version: '3.8'

services:
  api:
    image: registry/hospitality-api:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: registry/hospitality-worker:latest
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  centrifugo:
    image: centrifugo/centrifugo:latest
    deploy:
      replicas: 2

networks:
  default:
    driver: overlay
    attachable: true
```

---

### 12.13 Notifications (Prepare for Later)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  NOTIFICATION SERVICES - PREPARED, DEVELOP LATER                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  TRANSACTIONAL EMAIL                                                   ║
║  ├── Provider: Resend / AWS SES                                      ║
║  ├── Use cases:                                                       ║
║  │   ├── Password reset (mandatory)                                  ║
║  │   ├── Booking confirmation (optional)                             ║
║  │   ├── Invoice email (optional)                                    ║
║  │   └── Scheduled reports (future)                                  ║
║  └── Status: Architecture ready, implement when needed               ║
║                                                                        ║
║  SMS / WHATSAPP                                                        ║
║  ├── Provider: Twilio / WhatsApp Business API                        ║
║  ├── Use cases:                                                       ║
║  │   ├── OTP verification (2FA)                                      ║
║  │   ├── Urgent alerts to manager                                    ║
║  │   └── Guest notifications (optional)                              ║
║  └── Status: Architecture ready, implement when needed               ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.14 Scaling Path

```
╔═══════════════════════════════════════════════════════════════════════╗
║  SCALING STRATEGY - SAME ARCHITECTURE, DIFFERENT SCALE               ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  Stage 1: 0-30 tenants                                                ║
║  ├── 1 VPS (4 vCPU, 8GB RAM)                                         ║
║  ├── All services in Docker Compose                                  ║
║  └── Cost: $50-100/month                                             ║
║                                                                        ║
║  Stage 2: 30-100 tenants                                              ║
║  ├── 1 VPS (8 vCPU, 16GB RAM)                                        ║
║  ├── Docker Swarm mode                                               ║
║  └── Cost: $150-300/month                                            ║
║                                                                        ║
║  Stage 3: 100-300 tenants                                             ║
║  ├── Separate servers (DB, App, Cache)                               ║
║  ├── Read replicas for reporting                                     ║
║  └── Cost: $500-800/month                                            ║
║                                                                        ║
║  Stage 4: 300-500+ tenants                                            ║
║  ├── Full cluster (3+ nodes)                                         ║
║  ├── Auto-scaling enabled                                            ║
║  └── Cost: $2,000-5,000/month                                        ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 12.15 Ringkasan Infrastructure

| Category | Decision |
|----------|----------|
| **Multi-tenancy** | Database-per-tenant + Schema-per-app |
| **Database** | TimescaleDB + PgBouncer |
| **Cache** | Redis (session, cache, pub/sub) |
| **Message Broker** | RabbitMQ (events) |
| **Background Jobs** | Dramatiq + RabbitMQ |
| **File Storage** | Cloudflare R2 |
| **Search** | Meilisearch |
| **Real-time** | Centrifugo |
| **Auth** | JWT + httpOnly Cookie + Redis |
| **Orchestration** | Docker Swarm |
| **Monitoring** | Prometheus + Grafana + Jaeger |
| **Logging** | Structured JSON + Correlation ID |
| **Security** | OWASP + Encryption + PCI-DSS + GDPR |
| **API Versioning** | URL Path (/api/v1/) |
| **Email** | Resend/SES (prepared, develop later) |
| **SMS/WhatsApp** | Twilio (prepared, develop later) |

---

## 13. Payment & Licensing ✅

### 13.0 Prinsip Payment & Licensing

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PAYMENT & LICENSING PRINCIPLES                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. FLEXIBLE LICENSING   → Support multiple pricing models            ║
║  2. SEPARATION           → Platform payment ≠ Organization payment   ║
║  3. NO PAYMENT FACILITATOR → Uang langsung ke rekening masing-masing ║
║  4. INTEGRATION BASED    → Platform sediakan integrasi, bukan collect║
║  5. MULTI-GATEWAY        → Support berbagai payment gateway          ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 13.1 Payment Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PAYMENT ARCHITECTURE                                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. PLATFORM SUBSCRIPTION (Tenant → Platform Owner)                   ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  Hotel ──→ Platform Gateway ──→ Platform Owner Account          │  ║
║  │              (Xendit/Midtrans)                                   │  ║
║  │                                                                  │  ║
║  │  Methods: VA, Credit Card, E-Wallet, QRIS                       │  ║
║  │  Features: Recurring billing, auto-invoice                      │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
║  2. ORGANIZATION PAYMENT (Guest → Hotel)                              ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  Guest ──→ Hotel's Gateway ──→ Hotel's Bank Account             │  ║
║  │              (via Platform integration)                          │  ║
║  │                                                                  │  ║
║  │  Setup: Hotel input their own API keys                          │  ║
║  │  Flow: Payment → Webhook → Auto-posting to folio               │  ║
║  │  Money: Direct to hotel (NOT through platform)                  │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 13.2 Supported Payment Gateways

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PAYMENT GATEWAY SUPPORT                                               ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────┬─────┬─────┬──────────┬──────┬───────────┐          ║
║  │ Gateway      │ VA  │ CC  │ E-Wallet │ QRIS │ Recurring │          ║
║  ├──────────────┼─────┼─────┼──────────┼──────┼───────────┤          ║
║  │ Midtrans     │ ✅  │ ✅  │ ✅       │ ✅   │ ✅        │          ║
║  │ Xendit       │ ✅  │ ✅  │ ✅       │ ✅   │ ✅        │          ║
║  │ Stripe       │ ❌  │ ✅  │ ❌       │ ❌   │ ✅        │          ║
║  └──────────────┴─────┴─────┴──────────┴──────┴───────────┘          ║
║                                                                        ║
║  USE CASES:                                                            ║
║  ├── Midtrans: Indonesia - full payment methods                      ║
║  ├── Xendit: Indonesia - developer-friendly                          ║
║  └── Stripe: International credit cards                              ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 13.3 Flexible Licensing System

```
╔═══════════════════════════════════════════════════════════════════════╗
║  FLEXIBLE LICENSING - SUPPORT ALL PRICING MODELS                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  SUPPORTED MODELS (Business decision later):                          ║
║                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  A. PER-APP PURCHASE                                            │  ║
║  │     PMS: $50/mo, Accounting: $30/mo, HRM: $20/mo               │  ║
║  │     → Hotel bayar per aplikasi yang dipakai                    │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  B. TIER/BUNDLE PACKAGE                                         │  ║
║  │     Bronze ($50): PMS only                                      │  ║
║  │     Silver ($100): PMS + Accounting                            │  ║
║  │     Gold ($200): All apps                                       │  ║
║  │     → Bundle pricing, semakin tinggi semakin hemat             │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  C. BASE + ADD-ON                                               │  ║
║  │     Base ($50): Core PMS                                        │  ║
║  │     +Accounting: $30, +HRM: $20, +POS: $40                     │  ║
║  │     → Flexible, bayar base + pilih add-on                      │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  D. USAGE-BASED                                                 │  ║
║  │     Per room night: $0.50                                       │  ║
║  │     Per transaction: $0.05                                      │  ║
║  │     Per employee: $2/mo                                         │  ║
║  │     → Pay as you go, cocok untuk hotel kecil                   │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 13.4 Licensing Database Schema (Central DB)

```sql
-- Plans: Template paket yang dijual
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,        -- 'starter', 'professional'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    plan_type VARCHAR(20) NOT NULL,          -- 'tier', 'per_app', 'base_addon', 'usage'
    base_price NUMERIC(15,2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL,      -- 'monthly', 'yearly'
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Features: Definisi semua fitur/aplikasi
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,        -- 'pms', 'accounting', 'hrm'
    name VARCHAR(100) NOT NULL,
    feature_type VARCHAR(20) NOT NULL,       -- 'app', 'module', 'addon'
    parent_feature_id INTEGER REFERENCES features(id),
    standalone_price NUMERIC(15,2),
    metadata JSONB
);

-- Plan-Feature mapping
CREATE TABLE plan_features (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES plans(id),
    feature_id INTEGER REFERENCES features(id),
    included BOOLEAN DEFAULT TRUE,
    limit_type VARCHAR(20),                  -- 'unlimited', 'capped', 'usage'
    limit_value INTEGER,                     -- max rooms, users, etc
    overage_price NUMERIC(15,4),
    UNIQUE(plan_id, feature_id)
);

-- Organization Subscriptions
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plan_id INTEGER REFERENCES plans(id),
    status VARCHAR(20) NOT NULL,             -- 'active', 'trial', 'past_due', 'cancelled'
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    billing_cycle_anchor TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscription Add-ons
CREATE TABLE subscription_addons (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id),
    feature_id INTEGER REFERENCES features(id),
    quantity INTEGER DEFAULT 1,
    price_override NUMERIC(15,2),
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ
);

-- Usage Records (untuk usage-based billing)
CREATE TABLE usage_records (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    feature_id INTEGER REFERENCES features(id),
    metric VARCHAR(50) NOT NULL,             -- 'rooms', 'transactions'
    quantity NUMERIC(15,4) NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ
);

-- Invoices
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    subscription_id INTEGER REFERENCES subscriptions(id),
    invoice_number VARCHAR(50) UNIQUE,
    status VARCHAR(20) NOT NULL,             -- 'draft', 'open', 'paid', 'void'
    subtotal NUMERIC(15,2),
    tax NUMERIC(15,2),
    total NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'IDR',
    due_date DATE,
    paid_at TIMESTAMPTZ,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    line_items JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 13.5 Organization Payment Settings Schema (Tenant DB)

```sql
-- Payment Gateway Configuration per Organization
CREATE TABLE payment_gateway_settings (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    gateway_code VARCHAR(20) NOT NULL,       -- 'midtrans', 'xendit', 'stripe'
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    environment VARCHAR(20) DEFAULT 'sandbox', -- 'sandbox', 'production'

    -- Encrypted credentials (use pgcrypto)
    merchant_id VARCHAR(100),
    server_key_encrypted BYTEA,              -- encrypted
    client_key VARCHAR(100),

    -- Gateway-specific config
    config JSONB,                            -- webhook_url, notification_url, etc

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    created_by_id INTEGER REFERENCES users(id),

    UNIQUE(organization_id, gateway_code)
);

-- Payment Transactions (Guest payments)
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,

    -- Reference
    folio_id INTEGER REFERENCES folios(id),
    invoice_id INTEGER,

    -- Transaction info
    transaction_id VARCHAR(100) UNIQUE,      -- from gateway
    gateway_code VARCHAR(20) NOT NULL,
    payment_type VARCHAR(50),                -- 'va', 'credit_card', 'ewallet', 'qris'

    -- Amount
    amount NUMERIC(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',

    -- Status
    status VARCHAR(20) NOT NULL,             -- 'pending', 'success', 'failed', 'expired'
    gateway_status VARCHAR(50),              -- original status from gateway

    -- Details
    payment_details JSONB,                   -- VA number, card last4, etc
    gateway_response JSONB,                  -- full response for debugging

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,

    -- Audit
    created_by_id INTEGER REFERENCES users(id)
);

-- Webhook Logs (for debugging)
CREATE TABLE payment_webhook_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    gateway_code VARCHAR(20) NOT NULL,
    event_type VARCHAR(50),
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    received_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 13.6 License Check Service

```python
# Service untuk check akses fitur

class LicenseService:
    """Check organization access to features based on subscription."""

    async def has_feature(self, org_id: int, feature_code: str) -> bool:
        """Check if organization has access to a feature."""
        subscription = await self.get_active_subscription(org_id)
        if not subscription:
            return False

        # Check plan features
        plan_feature = await self.get_plan_feature(
            subscription.plan_id, feature_code
        )
        if plan_feature and plan_feature.included:
            return True

        # Check add-ons
        addon = await self.get_subscription_addon(
            subscription.id, feature_code
        )
        return addon is not None

    async def get_feature_limit(
        self, org_id: int, feature_code: str, metric: str
    ) -> int | None:
        """Get limit for a feature metric (e.g., max_rooms)."""
        subscription = await self.get_active_subscription(org_id)
        if not subscription:
            return 0

        plan_feature = await self.get_plan_feature(
            subscription.plan_id, feature_code
        )
        if plan_feature and plan_feature.limit_type == 'unlimited':
            return None  # No limit

        return plan_feature.limit_value if plan_feature else 0

    async def check_within_limit(
        self, org_id: int, metric: str
    ) -> tuple[bool, int, int | None]:
        """Check if org is within usage limit.

        Returns: (within_limit, current_usage, limit)
        """
        limit = await self.get_feature_limit(org_id, metric)
        if limit is None:
            return (True, 0, None)  # Unlimited

        current = await self.get_current_usage(org_id, metric)
        return (current < limit, current, limit)


# Usage in API endpoints
@router.post("/reservations")
async def create_reservation(
    dto: CreateReservationDTO,
    license_service: LicenseService = Depends()
):
    # Check PMS access
    if not await license_service.has_feature(org_id, "pms"):
        raise HTTPException(
            status_code=403,
            detail="PMS feature not available in your plan"
        )

    # Check room limit
    within_limit, used, limit = await license_service.check_within_limit(
        org_id, "rooms"
    )
    if not within_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Room limit exceeded ({used}/{limit}). Please upgrade."
        )

    # Proceed with reservation
    return await reservation_service.create(dto)
```

---

### 13.7 Payment Gateway Integration

```python
# Abstract Payment Gateway Interface

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class PaymentRequest(BaseModel):
    amount: int
    currency: str = "IDR"
    order_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    description: str
    payment_type: str  # 'va', 'credit_card', 'ewallet', 'qris'

class PaymentResponse(BaseModel):
    transaction_id: str
    status: str
    payment_url: Optional[str]  # redirect URL for payment
    va_number: Optional[str]
    qr_code: Optional[str]
    expiry_time: Optional[datetime]
    raw_response: dict

class PaymentGateway(ABC):
    """Abstract base class for payment gateways."""

    @abstractmethod
    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Create a new payment."""
        pass

    @abstractmethod
    async def check_status(self, transaction_id: str) -> PaymentResponse:
        """Check payment status."""
        pass

    @abstractmethod
    async def cancel_payment(self, transaction_id: str) -> bool:
        """Cancel a pending payment."""
        pass

    @abstractmethod
    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature."""
        pass


# Midtrans Implementation
class MidtransGateway(PaymentGateway):
    def __init__(self, server_key: str, client_key: str, is_production: bool):
        self.server_key = server_key
        self.client_key = client_key
        self.base_url = (
            "https://api.midtrans.com" if is_production
            else "https://api.sandbox.midtrans.com"
        )

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        # Implementation for Midtrans
        ...


# Xendit Implementation
class XenditGateway(PaymentGateway):
    def __init__(self, api_key: str, is_production: bool):
        self.api_key = api_key
        self.base_url = "https://api.xendit.co"

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        # Implementation for Xendit
        ...


# Stripe Implementation
class StripeGateway(PaymentGateway):
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        # Implementation for Stripe
        ...


# Factory to get gateway based on org settings
class PaymentGatewayFactory:
    async def get_gateway(
        self, org_id: int, gateway_code: str = None
    ) -> PaymentGateway:
        """Get payment gateway instance for organization."""
        settings = await self.get_gateway_settings(org_id, gateway_code)

        if settings.gateway_code == "midtrans":
            return MidtransGateway(
                server_key=decrypt(settings.server_key_encrypted),
                client_key=settings.client_key,
                is_production=settings.environment == "production"
            )
        elif settings.gateway_code == "xendit":
            return XenditGateway(
                api_key=decrypt(settings.server_key_encrypted),
                is_production=settings.environment == "production"
            )
        elif settings.gateway_code == "stripe":
            return StripeGateway(
                secret_key=decrypt(settings.server_key_encrypted)
            )

        raise ValueError(f"Unknown gateway: {settings.gateway_code}")
```

---

### 13.8 Ringkasan Payment & Licensing

| Category | Decision |
|----------|----------|
| **Licensing Model** | Flexible - support per-app, tier, base+addon, usage |
| **Platform Payment** | Xendit/Midtrans (subscription billing) |
| **Organization Payment** | Integration-based (hotel's own merchant) |
| **Supported Gateways** | Midtrans + Xendit + Stripe |
| **Money Flow** | Direct to respective accounts (no PayFac) |
| **Feature Access** | LicenseService check at API layer |

---

## 14. TimescaleDB & Operational Standards ✅

> Keputusan operational dari hasil audit multi-agent (2025-12-07)

---

### 14.1 TimescaleDB Hypertable

#### 14.1.1 Kapan Gunakan Hypertable

| Kriteria | Hypertable? | Alasan |
|----------|-------------|--------|
| Data time-series (append-mostly) | ✅ Ya | Optimized untuk INSERT |
| Volume > 100K rows/tahun | ✅ Ya | Benefit dari partitioning |
| Query sering filter by date | ✅ Ya | Chunk pruning |
| Butuh retention policy | ✅ Ya | Auto-delete old data |
| Data sering UPDATE random | ❌ Tidak | Hypertable kurang optimal |
| Tabel target FK dari banyak tabel | ❌ Tidak | FK ke hypertable tidak supported |
| Data statis/master | ❌ Tidak | Tidak perlu partitioning |

#### 14.1.2 Tabel yang Menjadi Hypertable

| Schema | Table | Chunk Interval | Compression | Retention |
|--------|-------|----------------|-------------|-----------|
| shared | audit_logs | 1 bulan | > 1 bulan | 7 tahun |
| pms | folio_transactions | 1 bulan | > 3 bulan | 7 tahun |
| pms | daily_statistics | 1 bulan | > 6 bulan | 10 tahun |
| pms | housekeeping_logs | 1 bulan | > 3 bulan | 3 tahun |
| accounting | journal_entries | 1 bulan | > 6 bulan | 10 tahun |

#### 14.1.3 Tabel yang TETAP Regular

| Table | Alasan |
|-------|--------|
| reservations | Sering UPDATE status |
| guests | Bukan time-series, butuh FK |
| rooms | Data statis |
| invoices | Butuh FK dari payments |
| users | Master data |

#### 14.1.4 Mitigasi Kekurangan Hypertable

**A. FK ke Hypertable → Application-Level Validation**
```python
# Validasi di Use Case layer (bukan database FK)
class CreatePaymentUseCase:
    async def execute(self, transaction_id: int, amount: Decimal):
        # Validasi transaction exists
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError("Transaction", transaction_id)
        # Proceed
        return await self.payment_repo.create(...)
```

**B. Primary Key Composite → Surrogate UUID Pattern**
```sql
CREATE TABLE pms.folio_transactions (
    -- Internal composite PK (untuk TimescaleDB)
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    transaction_date TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, transaction_date),

    -- External UUID (untuk API & reference)
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,

    -- Data columns
    amount NUMERIC(15,2) NOT NULL
);

-- Tabel lain reference via UUID
CREATE TABLE pms.payments (
    id SERIAL PRIMARY KEY,
    transaction_uuid UUID NOT NULL,  -- Reference ke UUID, bukan composite PK
    amount NUMERIC(15,2) NOT NULL
);
```

**C. Unique Constraint → Include Time Column**
```sql
-- Unique harus include partition key
CREATE UNIQUE INDEX idx_folio_trans_receipt
ON pms.folio_transactions(receipt_number, transaction_date);

-- Untuk lookup tanpa time, tambah regular index
CREATE INDEX idx_folio_trans_receipt_lookup
ON pms.folio_transactions(receipt_number);
```

**D. Compressed Data Read-Only → Decompress Workflow**
```python
# Untuk edit historical data (rare case, butuh approval)
class UpdateHistoricalTransactionUseCase:
    async def execute(self, transaction_id: int, data: dict):
        chunk_info = await self.db.get_chunk_info(transaction_id)

        if chunk_info.is_compressed:
            await self.db.decompress_chunk(chunk_info.chunk_name)
            await self.transaction_repo.update(transaction_id, data)
            await self.db.compress_chunk(chunk_info.chunk_name)
            await self.audit_log.log_historical_edit(...)
        else:
            await self.transaction_repo.update(transaction_id, data)
```

#### 14.1.5 Hypertable Setup Example

```sql
-- 1. Create table dengan composite PK
CREATE TABLE pms.folio_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    transaction_date TIMESTAMPTZ NOT NULL,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    folio_id INTEGER NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, transaction_date)
);

-- 2. Convert to hypertable
SELECT create_hypertable(
    'pms.folio_transactions',
    'transaction_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 3. Compression policy (compress > 3 bulan)
ALTER TABLE pms.folio_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'folio_id'
);
SELECT add_compression_policy('pms.folio_transactions', INTERVAL '3 months');

-- 4. Retention policy (hapus > 7 tahun)
SELECT add_retention_policy('pms.folio_transactions', INTERVAL '7 years');

-- 5. Continuous aggregate untuk reporting
CREATE MATERIALIZED VIEW pms.daily_revenue
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', transaction_date) AS day,
    SUM(amount) AS total_revenue,
    COUNT(*) AS transaction_count
FROM pms.folio_transactions
WHERE amount > 0
GROUP BY day;

SELECT add_continuous_aggregate_policy(
    'pms.daily_revenue',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

---

### 14.2 Backup & Disaster Recovery

#### 14.2.1 Tiered Backup Strategy

| Scale | Strategy | RPO | RTO | Cost/bulan |
|-------|----------|-----|-----|------------|
| Development (0-10 tenants) | Basic: pg_dump + S3 | 24 jam | 4-8 jam | $50 |
| Production (10-100 tenants) | Standard: pgBackRest + WAL | 5-15 menit | 1-2 jam | $100 |
| Scale (100-500 tenants) | Enterprise: Replication + Multi-Region | < 1 menit | 5-15 menit | $500 |
| Alternative | Cloud-Managed: RDS/Cloud SQL | 5 menit | 5-30 menit | $800-1500 |

#### 14.2.2 Retention Policy

| Backup Type | Retention |
|-------------|-----------|
| Daily | 7 hari |
| Weekly | 4 minggu |
| Monthly | 12 bulan |
| Yearly | 7 tahun (financial compliance) |

#### 14.2.3 RPO/RTO Targets

| Skenario | RPO (Data Loss) | RTO (Downtime) |
|----------|-----------------|----------------|
| Single tenant corruption | < 1 jam | < 15 menit |
| Database server failure | < 5 menit | < 5 menit |
| Data center failure | < 1 jam | < 4 jam |
| Ransomware attack | < 24 jam | < 8 jam |

---

### 14.3 Event-Driven Architecture

#### 14.3.1 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Message Broker | RabbitMQ | Task queue + Event pub/sub |
| Task Library | Celery | Background jobs |
| Result Backend | Redis (DB 1) | Task results |
| Cache | Redis (DB 0) | API cache, RBAC |
| Session | Redis (DB 2) | JWT refresh tokens |

#### 14.3.2 Redis Database Allocation

| DB | Purpose | TTL Default |
|----|---------|-------------|
| 0 | API Cache (query, RBAC) | 15 menit |
| 1 | Celery Results | 24 jam |
| 2 | Session & JWT Refresh | 7 hari |
| 3 | Rate Limiting | 1 jam |

#### 14.3.3 Celery Configuration

```python
from celery import Celery
from kombu import Exchange, Queue

app = Celery('platform_tasks')

app.conf.update(
    # Broker (RabbitMQ)
    broker_url='amqp://user:pass@rabbitmq:5672/platform',

    # Result Backend (Redis)
    result_backend='redis://redis:6379/1',

    # Quality Settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,

    # Serialization
    task_serializer='json',
    accept_content=['json'],
)

# Queue Definitions
app.conf.task_queues = (
    Queue('high', Exchange('high'), routing_key='high'),
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('low', Exchange('low'), routing_key='low'),
)

# Task Routing
app.conf.task_routes = {
    'tasks.notifications.*': {'queue': 'high'},
    'tasks.email.*': {'queue': 'high'},
    'tasks.reports.*': {'queue': 'low'},
}
```

#### 14.3.4 Event Naming Convention

```python
# Format: {app}.{entity}.{action}
"pms.reservation.created"
"pms.reservation.checked_in"
"pms.reservation.checked_out"
"accounting.invoice.created"
"accounting.payment.received"
"hrm.employee.hired"
```

---

### 14.4 CI/CD Pipeline

#### 14.4.1 Platform & Tools

| Component | Tool |
|-----------|------|
| CI/CD Platform | GitHub Actions |
| Container Registry | GitHub Container Registry (ghcr.io) |
| Security Scan | Trivy (container), Snyk (dependencies) |
| Coverage | Codecov |

#### 14.4.2 Branch Strategy

```
main ─────────────────────► Production (manual approve)
  │
  └── develop ────────────► Staging (auto deploy)
        │
        └── feature/* ────► CI only (tests)
```

#### 14.4.3 Pipeline Triggers

| Event | CI | Staging | Production |
|-------|----|---------|-----------|
| Push to `feature/*` | ✅ | ❌ | ❌ |
| PR to `develop` | ✅ | ❌ | ❌ |
| Push to `develop` | ✅ | ✅ Auto | ❌ |
| Push to `main` | ✅ | ❌ | ⏳ Manual |

#### 14.4.4 CI Pipeline Steps

```yaml
# Backend CI
- Checkout
- Setup Python 3.11
- Install dependencies
- Lint (ruff)
- Type check (mypy)
- Unit tests (pytest --cov)
- Upload coverage

# Frontend CI
- Checkout
- Setup Bun
- Install dependencies
- Lint (eslint)
- Type check (tsc)
- Unit tests (vitest)
- Build

# Security
- Trivy vulnerability scan
- Dependency audit
```

---

### 14.5 Code Generation (Kubb)

#### 14.5.1 Generated Output

| Output | Location | Purpose |
|--------|----------|---------|
| TypeScript Types | `/src/api/generated/types/` | Interface definitions |
| Zod Schemas | `/src/api/generated/zod/` | Runtime validation |
| React Query Hooks | `/src/api/generated/hooks/` | Data fetching |
| Axios Client | `/src/api/generated/client/` | HTTP client |

#### 14.5.2 Folder Structure

```
cms-vite/src/
├── api/
│   ├── generated/           # ⚠️ Auto-generated, JANGAN edit manual
│   │   ├── types/
│   │   ├── zod/
│   │   ├── hooks/
│   │   └── client/
│   └── custom/              # Custom overrides jika perlu
```

#### 14.5.3 NPM Scripts

```json
{
  "scripts": {
    "api:generate": "kubb",
    "api:generate:watch": "kubb --watch",
    "predev": "bun run api:generate"
  }
}
```

#### 14.5.4 Workflow

```
Backend update Pydantic DTO
       │
       ▼
FastAPI auto-update OpenAPI (/openapi.json)
       │
       ▼
Run: bun run api:generate
       │
       ▼
Kubb generates types, zod, hooks
       │
       ▼
Frontend import dari generated
```

---

### 14.6 Testing Strategy

#### 14.6.1 Testing Pyramid

| Layer | Coverage Target | Tools |
|-------|-----------------|-------|
| Unit Tests | 70% | Pytest (backend), Vitest (frontend) |
| Integration Tests | 20% | Pytest + TestClient, MSW |
| E2E Tests | 10% | Playwright |

#### 14.6.2 Backend Test Structure

```
backend-python/
├── services/
│   └── auth/
│       ├── use_cases/
│       │   └── login.py
│       └── tests/
│           ├── test_login.py
│           └── test_register.py
└── tests/
    └── api/
        └── test_auth_api.py
```

#### 14.6.3 Frontend Test Structure

```
cms-vite/
├── src/
│   └── features/
│       └── auth/
│           └── hooks/
│               ├── useAuth.ts
│               └── __tests__/
│                   └── useAuth.test.ts
└── e2e/
    └── tests/
        ├── auth.spec.ts
        └── devices.spec.ts
```

#### 14.6.4 Testing Tools

| Purpose | Backend | Frontend |
|---------|---------|----------|
| Unit Test | pytest | Vitest |
| Mocking | unittest.mock | MSW |
| Coverage | pytest-cov | @vitest/coverage-v8 |
| E2E | - | Playwright |
| API Test | TestClient | MSW |

#### 14.6.5 CI Requirements

- Tests run on every PR
- Block merge if coverage < 70%
- E2E tests run before production deploy

---

### 14.7 Ringkasan Keputusan Operational

| # | Area | Keputusan |
|---|------|-----------|
| 236 | TimescaleDB | Hypertables untuk time-series + mitigasi FK dengan UUID |
| 237 | Firebird | Referensi saja, tidak ada migrasi |
| 238 | Backup/DR | Tiered approach sesuai scale |
| 239 | Event-Driven | Celery + RabbitMQ (quality-focused) |
| 240 | Payment | Recording only, PCI-DSS not applicable |
| 241 | CI/CD | Full GitHub Actions pipeline |
| 242 | Code Generation | Full Kubb (types + zod + hooks) |
| 243 | Testing | Full suite, 70% coverage target |

---

## 15. Logging & Observability ✅

### 15.1 Prinsip Logging

```
╔═══════════════════════════════════════════════════════════════════════╗
║  LOGGING PRINCIPLES                                                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. STRUCTURED LOGS    → JSON format, bukan plain text                ║
║  2. CORRELATION ID     → Track request across all services            ║
║  3. TENANT ISOLATION   → Setiap log ada tenant_id                     ║
║  4. LEVELS MATTER      → ERROR/WARN/INFO/DEBUG sesuai konteks         ║
║  5. NO SECRETS         → JANGAN log password, tokens, PII             ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 15.2 Log Format (JSON Structured)

```json
{
  "timestamp": "2025-12-07T10:30:00.123Z",
  "level": "INFO",
  "service": "pms",
  "tenant_id": "org_123",
  "correlation_id": "req-abc-123-def",
  "user_id": 456,
  "message": "Reservation created",
  "data": {
    "reservation_id": 789,
    "room_number": "101",
    "guest_name": "John Doe"
  },
  "duration_ms": 45
}
```

**Required Fields:**
| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO8601 | Waktu log dibuat (UTC) |
| level | string | ERROR, WARN, INFO, DEBUG |
| service | string | Nama service (auth, pms, accounting) |
| tenant_id | string | Organization ID untuk multi-tenant |
| correlation_id | string | Request tracking ID |
| message | string | Human-readable message |

**Optional Fields:**
| Field | Type | Description |
|-------|------|-------------|
| user_id | int | User yang melakukan action |
| data | object | Additional context |
| duration_ms | int | Execution time |
| error | object | Error details (untuk ERROR level) |

---

### 15.3 Log Levels

| Level | Kapan Digunakan | Contoh |
|-------|-----------------|--------|
| **ERROR** | Exception, gagal total, perlu immediate action | Database connection failed, Payment failed |
| **WARN** | Degraded performance, retry berhasil, unusual | Rate limit approached, Slow query detected |
| **INFO** | Business events, state changes | Reservation created, User logged in |
| **DEBUG** | Technical detail, request/response | API request payload, SQL query |

**Default Level per Environment:**
| Environment | Default Level |
|-------------|---------------|
| Production | INFO |
| Staging | DEBUG |
| Development | DEBUG |

---

### 15.4 Correlation ID

#### 15.4.1 Flow

```
┌─────────────┐    X-Correlation-ID    ┌─────────────┐
│   Frontend  │ ──────────────────────▶│   Backend   │
│   (React)   │    req-abc-123-def     │   (FastAPI) │
└─────────────┘                        └──────┬──────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
            │   Celery    │           │   Database  │           │   Redis     │
            │   Task      │           │   Query     │           │   Cache     │
            └─────────────┘           └─────────────┘           └─────────────┘
                    │                         │                         │
                    └─────────────────────────┴─────────────────────────┘
                                              │
                                              ▼
                                    All logs have same
                                    correlation_id: req-abc-123-def
```

#### 15.4.2 Implementation

**Frontend (Axios Interceptor):**
```typescript
import { v4 as uuidv4 } from 'uuid';

api.interceptors.request.use((config) => {
  config.headers['X-Correlation-ID'] = `req-${uuidv4()}`;
  return config;
});
```

**Backend (FastAPI Middleware):**
```python
from starlette.middleware.base import BaseHTTPMiddleware
import contextvars

correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)

        response = await call_next(request)
        response.headers['X-Correlation-ID'] = correlation_id
        return response
```

---

### 15.5 Observability Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY STACK                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  METRICS (Prometheus + Grafana)                                         │
│  ├── Application metrics (request count, latency, errors)              │
│  ├── Business metrics (reservations/day, revenue)                      │
│  ├── Infrastructure metrics (CPU, memory, disk)                        │
│  └── Per-tenant dashboards                                              │
│                                                                          │
│  LOGS (Loki)                                                            │
│  ├── Centralized log aggregation                                        │
│  ├── Label-based filtering (service, tenant_id, level)                 │
│  ├── Integration with Grafana                                           │
│  └── Retention: 30 days hot, 1 year cold                               │
│                                                                          │
│  TRACING (Jaeger)                                                       │
│  ├── Distributed tracing across services                                │
│  ├── Request flow visualization                                         │
│  ├── Latency breakdown                                                  │
│  └── Sampling: 1% production, 100% staging                             │
│                                                                          │
│  ERRORS (Sentry)                                                        │
│  ├── Error tracking & grouping                                          │
│  ├── Stack traces                                                       │
│  ├── Release tracking                                                   │
│  └── Alerting                                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 15.6 Grafana Dashboards

#### 15.6.1 Dashboard Hierarchy

```
Grafana/
├── Platform Overview          # Semua tenants, high-level metrics
├── Service Health             # Per-service (auth, pms, accounting)
├── Tenant Dashboard           # Per-organization metrics
│   ├── {tenant_id}/
│   │   ├── Operations         # Reservations, check-ins, revenue
│   │   ├── Performance        # Response times, errors
│   │   └── Usage              # API calls, storage
└── Infrastructure             # Server metrics
```

#### 15.6.2 Key Metrics per Tenant

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| request_count | Total API requests | - |
| request_latency_p95 | 95th percentile latency | > 2s |
| error_rate | Errors / Total requests | > 1% |
| active_users | Concurrent logged-in users | - |
| reservations_today | Business metric | - |

---

### 15.7 Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| High Error Rate | error_rate > 5% for 5m | CRITICAL | PagerDuty |
| Slow Response | p95_latency > 5s for 10m | WARNING | Slack |
| Database Down | db_up == 0 for 1m | CRITICAL | PagerDuty |
| Disk Full | disk_usage > 90% | WARNING | Slack |
| Memory High | memory_usage > 85% | WARNING | Slack |

---

### 15.8 Log Retention

| Type | Hot Storage | Cold Storage | Total |
|------|-------------|--------------|-------|
| Application Logs | 30 days | 11 months | 1 year |
| Audit Logs | 1 year | 6 years | 7 years |
| Error Logs | 90 days | 9 months | 1 year |
| Debug Logs | 7 days | - | 7 days |

---

### 15.9 Sentry Integration (Error Tracking)

#### 15.9.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SENTRY - ERROR TRACKING SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Purpose:                                                                │
│  ├── Error tracking & grouping                                          │
│  ├── Stack traces with source maps                                      │
│  ├── Performance monitoring (transactions, spans)                       │
│  ├── Session replay for debugging                                       │
│  ├── Release tracking & deployment                                      │
│  └── Alerting on new/recurring issues                                   │
│                                                                          │
│  Deployment: Sentry SaaS (sentry.io) OR Self-hosted                     │
│                                                                          │
│  Multi-Tenant: All errors tagged with organization_id, tenant_id        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 15.9.2 Backend Integration (FastAPI)

**Dependencies:**
```
# requirements.txt
sentry-sdk[fastapi,celery,sqlalchemy,redis,httpx]==2.19.0
```

**Initialization:**
```python
# app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


def init_sentry():
    """Initialize Sentry SDK with all integrations."""
    if not settings.SENTRY_DSN:
        return  # Sentry disabled

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,  # production, staging, development
        release=settings.APP_VERSION,       # e.g., "pms@1.2.3"

        # Performance monitoring
        traces_sample_rate=_get_traces_sample_rate(),
        profiles_sample_rate=0.1,  # 10% profiling

        # Error sampling (100% - capture all errors)
        sample_rate=1.0,

        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            CeleryIntegration(monitor_beat_tasks=True),
            SqlalchemyIntegration(),
            RedisIntegration(),
            HttpxIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],

        # Multi-tenant context
        before_send=add_tenant_context,
        before_send_transaction=add_tenant_context_to_transaction,

        # PII scrubbing
        send_default_pii=False,

        # Ignore certain errors
        ignore_errors=[
            KeyboardInterrupt,
            ConnectionResetError,
        ],
    )


def _get_traces_sample_rate() -> float:
    """Dynamic sample rate based on environment."""
    rates = {
        "production": 0.1,   # 10% sampling
        "staging": 0.5,      # 50% sampling
        "development": 1.0,  # 100% sampling
    }
    return rates.get(settings.ENVIRONMENT, 0.1)


def add_tenant_context(event, hint):
    """Add tenant context to all Sentry events."""
    from app.core.context import get_current_tenant

    tenant = get_current_tenant()
    if tenant:
        event.setdefault("tags", {})
        event["tags"]["organization_id"] = tenant.organization_id
        event["tags"]["org_code"] = tenant.org_code
        event["tags"]["tenant_id"] = tenant.tenant_id

        event.setdefault("extra", {})
        event["extra"]["tenant"] = {
            "organization_id": tenant.organization_id,
            "org_code": tenant.org_code,
            "tenant_id": tenant.tenant_id,
        }

    return event


def add_tenant_context_to_transaction(event, hint):
    """Add tenant context to performance transactions."""
    return add_tenant_context(event, hint)


# === Manual Error Capture ===

def capture_error(error: Exception, extra: dict = None):
    """Manually capture an error with extra context."""
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", extra: dict = None):
    """Capture a message (not an exception)."""
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)
```

**Usage in FastAPI:**
```python
# app/main.py
from app.core.sentry import init_sentry

# Initialize before app creation
init_sentry()

app = FastAPI(...)

# Sentry automatically captures exceptions from routes
@app.get("/api/v1/reservations/{id}")
async def get_reservation(id: int):
    reservation = await repo.get(id)
    if not reservation:
        # This error will be auto-captured by Sentry
        raise HTTPException(404, "Reservation not found")
    return reservation
```

**User Context:**
```python
# app/api/deps.py
import sentry_sdk

async def get_current_user_with_sentry(
    user: User = Depends(get_current_user)
) -> User:
    """Set Sentry user context for better error tracking."""
    sentry_sdk.set_user({
        "id": str(user.id),
        "email": user.email,
        "username": user.name,
        "ip_address": "{{auto}}",  # Auto-detect from request
    })
    return user
```

#### 15.9.3 Frontend Integration (React)

**Dependencies:**
```json
// package.json
{
  "dependencies": {
    "@sentry/react": "^8.40.0"
  }
}
```

**Initialization:**
```typescript
// src/lib/sentry.ts
import * as Sentry from "@sentry/react";

export function initSentry() {
  if (!import.meta.env.VITE_SENTRY_DSN) return;

  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENVIRONMENT,
    release: import.meta.env.VITE_APP_VERSION,

    integrations: [
      // Browser tracing for performance
      Sentry.browserTracingIntegration(),

      // Session replay for debugging
      Sentry.replayIntegration({
        maskAllText: false,
        maskAllInputs: true,  // Mask password, credit card fields
        blockAllMedia: false,
      }),

      // React-specific error boundary
      Sentry.reactRouterV6BrowserTracingIntegration({
        useEffect: React.useEffect,
      }),
    ],

    // Performance sampling
    tracesSampleRate: import.meta.env.VITE_ENVIRONMENT === "production" ? 0.1 : 1.0,

    // Session replay sampling
    replaysSessionSampleRate: 0.1,  // 10% of all sessions
    replaysOnErrorSampleRate: 1.0,  // 100% of sessions with errors

    // Filter out noisy errors
    ignoreErrors: [
      "ResizeObserver loop limit exceeded",
      "Network request failed",
      "Load failed",
    ],

    // Multi-tenant context
    beforeSend(event) {
      const tenant = getTenantFromStore();  // Get from Zustand/Redux
      if (tenant) {
        event.tags = {
          ...event.tags,
          organization_id: tenant.organizationId,
          org_code: tenant.orgCode,
        };
      }
      return event;
    },
  });
}

// Set user context after login
export function setSentryUser(user: User | null) {
  if (user) {
    Sentry.setUser({
      id: String(user.id),
      email: user.email,
      username: user.name,
    });
  } else {
    Sentry.setUser(null);
  }
}

// Manual error capture
export function captureError(error: Error, context?: Record<string, unknown>) {
  Sentry.captureException(error, { extra: context });
}
```

**Error Boundary:**
```tsx
// src/components/ErrorBoundary.tsx
import * as Sentry from "@sentry/react";

export const SentryErrorBoundary = Sentry.withErrorBoundary;

// Usage in App.tsx
import { SentryErrorBoundary } from "./components/ErrorBoundary";

function App() {
  return (
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }) => (
        <ErrorFallback error={error} onRetry={resetError} />
      )}
      showDialog  // Show feedback dialog to users
    >
      <RouterProvider router={router} />
    </Sentry.ErrorBoundary>
  );
}
```

**Source Maps Upload (CI/CD):**
```yaml
# .github/workflows/deploy.yml
- name: Upload Source Maps to Sentry
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org
    SENTRY_PROJECT: frontend
  run: |
    npx @sentry/cli releases new ${{ env.VERSION }}
    npx @sentry/cli releases files ${{ env.VERSION }} upload-sourcemaps ./dist
    npx @sentry/cli releases finalize ${{ env.VERSION }}
```

#### 15.9.4 Celery Integration

```python
# app/celery/config.py
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

# Sentry already initialized in main app, but for Celery worker:
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[
        CeleryIntegration(
            monitor_beat_tasks=True,  # Track periodic tasks
            propagate_traces=True,    # Connect traces across services
        ),
    ],
)

# Example task with manual context
@celery_app.task(bind=True)
def process_night_audit(self, organization_id: int):
    """Night audit task with Sentry context."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("organization_id", organization_id)
        scope.set_tag("task_name", "night_audit")

        try:
            # Process night audit
            result = night_audit_service.run(organization_id)
            return result
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise  # Re-raise for Celery retry
```

#### 15.9.5 Sentry Project Structure

```
Sentry Organization: your-company
│
├── Project: backend-api
│   ├── Environment: production
│   ├── Environment: staging
│   └── Alerts: High error rate, new issue
│
├── Project: frontend-app
│   ├── Environment: production
│   ├── Environment: staging
│   └── Alerts: JavaScript errors
│
├── Project: celery-workers
│   ├── Environment: production
│   └── Alerts: Failed tasks
│
└── Team: hospitality-platform
    └── Members: dev team
```

#### 15.9.6 Alerting Rules

| Alert | Condition | Action |
|-------|-----------|--------|
| New Issue (Production) | New error never seen before | Slack #errors |
| Regression | Previously resolved error recurs | Slack #errors + PagerDuty |
| High Error Rate | > 50 events/hour | PagerDuty |
| Performance Degradation | p95 > 3s | Slack #performance |

#### 15.9.7 Sentry + Claude Code CLI Integration

```bash
# Install sentry-cli
npm install -g @sentry/cli

# Configure authentication
sentry-cli login

# List recent issues
sentry-cli issues list --org your-org --project backend-api

# Get issue details
sentry-cli issues info ISSUE_ID

# Example: Query via API (for Claude Code)
curl -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  "https://sentry.io/api/0/projects/your-org/backend-api/issues/?query=is:unresolved"
```

**MCP Server for Sentry (Custom):**
```typescript
// For Claude Code integration, create custom MCP server
// that wraps Sentry API for error queries

// Commands available:
// - List unresolved issues
// - Get issue details + stack trace
// - Search issues by tag (organization_id, user_id)
// - Mark issue as resolved
```

---

## 16. Internationalization (i18n) ✅

### 16.1 Prinsip i18n

```
╔═══════════════════════════════════════════════════════════════════════╗
║  I18N PRINCIPLES                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. STRUCTURE FIRST    → Setup i18n dari awal, translations later     ║
║  2. SINGLE LANGUAGE    → Mulai dengan 1 bahasa (ID atau EN)           ║
║  3. KEY-BASED          → Gunakan keys, bukan hardcoded strings        ║
║  4. FILE-BASED         → Translations di JSON/PO files                ║
║  5. COMPILE-TIME       → Lingui compile untuk performance             ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 16.2 Tech Stack i18n

| Platform | Library | Notes |
|----------|---------|-------|
| Frontend (React) | **Lingui** | Modern, compile-time, smaller bundle |
| Backend (Python) | **Babel** | Standard Python i18n via gettext |

**Kenapa Lingui (bukan i18next)?**
- Compile-time extraction (lebih cepat)
- Smaller runtime bundle
- Better TypeScript support
- ICU MessageFormat standard

---

### 16.3 Folder Structure

```
cms-vite/
├── src/
│   └── locales/
│       ├── id/                    # Indonesian
│       │   ├── messages.po        # Translations (PO format)
│       │   └── messages.js        # Compiled (auto-generated)
│       ├── en/                    # English
│       │   ├── messages.po
│       │   └── messages.js
│       └── lingui.config.ts       # Lingui configuration
│
backend-python/
├── locales/
│   ├── id/
│   │   └── LC_MESSAGES/
│   │       └── messages.po
│   └── en/
│       └── LC_MESSAGES/
│           └── messages.po
```

---

### 16.4 Usage Examples

#### 16.4.1 Frontend (React + Lingui)

```tsx
import { Trans, t } from '@lingui/macro';

// Component usage
function WelcomeMessage({ name }: { name: string }) {
  return (
    <div>
      <Trans>Welcome, {name}!</Trans>
    </div>
  );
}

// Programmatic usage
const errorMessage = t`Invalid email address`;

// Pluralization
<Plural
  value={count}
  one="# item"
  other="# items"
/>
```

#### 16.4.2 Backend (Python + Babel)

```python
from flask_babel import gettext as _

# Usage in code
error_message = _("Invalid email address")

# With parameters
welcome = _("Welcome, %(name)s!") % {"name": user.name}

# In responses
raise ValidationError(_("Field is required"))
```

---

### 16.5 What to Translate

| Category | Examples | Priority |
|----------|----------|----------|
| UI Labels | Buttons, menus, form labels | 🔴 HIGH |
| Error Messages | Validation errors, API errors | 🔴 HIGH |
| Notifications | Toast messages, alerts | 🔴 HIGH |
| Email Templates | Confirmation, invoices | 🟠 MEDIUM |
| PDF Reports | Invoice, receipt, statements | 🟠 MEDIUM |
| Help Text | Tooltips, instructions | 🟡 LOW |

---

### 16.6 Implementation Strategy (Delayed)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     I18N IMPLEMENTATION PHASES                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: Structure Ready (NOW)                                         │
│  ├── Install Lingui + Babel                                             │
│  ├── Setup folder structure                                             │
│  ├── Configure extraction                                               │
│  └── Use i18n keys in new code                                          │
│                                                                          │
│  PHASE 2: Primary Language (LATER)                                      │
│  ├── Choose primary language (ID atau EN)                               │
│  ├── Extract all strings                                                │
│  ├── Translate primary language                                         │
│  └── Test full flow                                                     │
│                                                                          │
│  PHASE 3: Additional Languages (FUTURE)                                 │
│  ├── Add English (if ID primary) or vice versa                         │
│  ├── Language switcher in UI                                            │
│  └── Per-tenant default language setting                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 16.7 Lingui Configuration

```typescript
// lingui.config.ts
import { defineConfig } from '@lingui/cli';

export default defineConfig({
  locales: ['id', 'en'],
  sourceLocale: 'id',
  catalogs: [
    {
      path: '<rootDir>/src/locales/{locale}/messages',
      include: ['src'],
    },
  ],
  format: 'po',
});
```

**Package.json scripts:**
```json
{
  "scripts": {
    "i18n:extract": "lingui extract",
    "i18n:compile": "lingui compile"
  }
}
```

---

### 16.8 Date/Time & Number Formatting

| Type | Library | Example |
|------|---------|---------|
| Dates | date-fns + locale | `format(date, 'PPP', { locale: id })` → "7 Desember 2025" |
| Numbers | Intl.NumberFormat | `new Intl.NumberFormat('id-ID').format(1000)` → "1.000" |
| Currency | Intl.NumberFormat | `new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' })` |

---

### 16.9 Ringkasan Keputusan i18n & Logging

| # | Area | Keputusan |
|---|------|-----------|
| 244 | Logging | Full Observability - JSON structured, Correlation ID, per-tenant dashboards |
| 245 | i18n | Delayed - Structure ready dari awal, 1 bahasa dulu, translations later |

---

*Document ini akan di-update seiring pembahasan setiap section.*
