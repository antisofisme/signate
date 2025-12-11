# Testing Strategy

> **Date**: 2025-12-07
> **Status**: Draft
> **Coverage Target**: 80% (Backend), 70% (Frontend)

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TESTING PYRAMID                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                          ┌───────────┐                                  │
│                          │   E2E     │  ~10%                           │
│                          │  Tests    │  (Critical flows)               │
│                       ┌──┴───────────┴──┐                              │
│                       │   Integration   │  ~20%                        │
│                       │     Tests       │  (API, DB)                   │
│                    ┌──┴─────────────────┴──┐                           │
│                    │      Unit Tests       │  ~70%                     │
│                    │   (Business logic)    │  (Fast, isolated)         │
│                    └───────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Testing Tools

### 1.1 Backend (Python)

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner, fixtures |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **httpx** | API testing |
| **factory_boy** | Test data factories |
| **faker** | Fake data generation |
| **pytest-mock** | Mocking |
| **testcontainers** | Docker containers for tests |

### 1.2 Frontend (React/TypeScript)

| Tool | Purpose |
|------|---------|
| **Vitest** | Test runner (Vite-native) |
| **Testing Library** | Component testing |
| **MSW** | API mocking |
| **Playwright** | E2E testing |
| **happy-dom** | DOM simulation |

---

## Part 2: Backend Testing

### 2.1 Unit Tests

#### 2.1.1 Use Case Tests

```python
# tests/unit/use_cases/test_create_tenant.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.tenant.use_cases.create_tenant import CreateTenantUseCase
from services.tenant.dtos import CreateTenantDTO

class TestCreateTenantUseCase:
    """Tests for CreateTenantUseCase"""

    @pytest.fixture
    def mock_tenant_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_org_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_tenant_repo, mock_org_repo):
        return CreateTenantUseCase(
            tenant_repo=mock_tenant_repo,
            org_repo=mock_org_repo
        )

    @pytest.mark.asyncio
    async def test_create_tenant_success(self, use_case, mock_tenant_repo):
        """Should create tenant with valid data"""
        # Arrange
        dto = CreateTenantDTO(
            code="HTL-001",
            name="Test Hotel",
            email="admin@test.com"
        )
        mock_tenant_repo.code_exists.return_value = False
        mock_tenant_repo.create.return_value = MagicMock(id=1, code="HTL-001")

        # Act
        result = await use_case.execute(dto)

        # Assert
        assert result.id == 1
        mock_tenant_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_code(self, use_case, mock_tenant_repo):
        """Should raise error for duplicate code"""
        # Arrange
        dto = CreateTenantDTO(code="HTL-001", name="Test", email="test@test.com")
        mock_tenant_repo.code_exists.return_value = True

        # Act & Assert
        with pytest.raises(BusinessError) as exc:
            await use_case.execute(dto)

        assert exc.value.code == "DUPLICATE_CODE"
```

#### 2.1.2 Validator Tests

```python
# tests/unit/validators/test_invoice_validator.py
import pytest
from decimal import Decimal
from services.billing.validators import InvoiceValidator
from services.billing.dtos import CreateInvoiceDTO, InvoiceItemDTO

class TestInvoiceValidator:
    """Tests for InvoiceValidator"""

    @pytest.fixture
    def validator(self):
        return InvoiceValidator()

    def test_validate_items_minimum(self, validator):
        """Should require at least one item"""
        dto = CreateInvoiceDTO(
            tenant_id=1,
            items=[]
        )
        errors = validator.validate(dto)
        assert any(e.code == "ITEMS_REQUIRED" for e in errors)

    def test_validate_tax_calculation(self, validator):
        """Should validate tax calculation"""
        dto = CreateInvoiceDTO(
            tenant_id=1,
            items=[
                InvoiceItemDTO(
                    description="Test",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000000"),
                    amount=Decimal("1000000")
                )
            ],
            subtotal=Decimal("1000000"),
            tax_amount=Decimal("100000"),  # Should be 110000 (11%)
            total_amount=Decimal("1100000")
        )
        errors = validator.validate(dto)
        assert any(e.code == "INVALID_TAX_CALCULATION" for e in errors)
```

#### 2.1.3 Entity Tests

```python
# tests/unit/entities/test_subscription.py
import pytest
from datetime import date, timedelta
from services.subscription.entities import Subscription

class TestSubscription:
    """Tests for Subscription entity"""

    def test_is_expired_true(self):
        """Should return True when subscription is expired"""
        subscription = Subscription(
            id=1,
            expires_at=date.today() - timedelta(days=1)
        )
        assert subscription.is_expired is True

    def test_is_expired_false(self):
        """Should return False when subscription is active"""
        subscription = Subscription(
            id=1,
            expires_at=date.today() + timedelta(days=30)
        )
        assert subscription.is_expired is False

    def test_days_until_expiry(self):
        """Should calculate days until expiry"""
        subscription = Subscription(
            id=1,
            expires_at=date.today() + timedelta(days=10)
        )
        assert subscription.days_until_expiry == 10
```

### 2.2 Integration Tests

#### 2.2.1 API Tests

```python
# tests/integration/api/test_tenant_api.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestTenantAPI:
    """Integration tests for Tenant API"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def auth_headers(self, client):
        """Get authenticated headers"""
        response = await client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "test_password"
        })
        token = response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_create_tenant(self, client, auth_headers):
        """POST /tenants should create tenant"""
        response = await client.post(
            "/tenants",
            headers=auth_headers,
            json={
                "code": "HTL-TEST",
                "name": "Test Hotel",
                "email": "test@hotel.com"
            }
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["code"] == "HTL-TEST"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_tenants_pagination(self, client, auth_headers):
        """GET /tenants should return paginated results"""
        response = await client.get(
            "/tenants",
            headers=auth_headers,
            params={"page": 1, "per_page": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["page"] == 1
        assert data["meta"]["per_page"] == 10

    @pytest.mark.asyncio
    async def test_tenant_not_found(self, client, auth_headers):
        """GET /tenants/{id} should return 404 for non-existent"""
        response = await client.get(
            "/tenants/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
```

#### 2.2.2 Repository Tests

```python
# tests/integration/repositories/test_tenant_repo.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from services.tenant.repositories import TenantRepository
from tests.factories import TenantFactory

class TestTenantRepository:
    """Integration tests for TenantRepository"""

    @pytest.fixture
    async def repo(self, db_session: AsyncSession):
        return TenantRepository(db_session)

    @pytest.mark.asyncio
    async def test_create_tenant(self, repo):
        """Should create tenant in database"""
        tenant = await repo.create({
            "code": "HTL-001",
            "name": "Test Hotel",
            "email": "test@hotel.com",
            "status": "pending"
        })

        assert tenant.id is not None
        assert tenant.code == "HTL-001"

    @pytest.mark.asyncio
    async def test_find_by_code(self, repo, db_session):
        """Should find tenant by code"""
        # Create tenant
        await TenantFactory.create(session=db_session, code="HTL-FIND")

        # Find
        tenant = await repo.find_by_code("HTL-FIND")
        assert tenant is not None
        assert tenant.code == "HTL-FIND"

    @pytest.mark.asyncio
    async def test_soft_delete(self, repo, db_session):
        """Should soft delete tenant"""
        tenant = await TenantFactory.create(session=db_session)

        await repo.delete(tenant.id)
        await db_session.commit()

        # Should not find with default query
        found = await repo.get(tenant.id)
        assert found is None

        # Should find with include_deleted
        found = await repo.get(tenant.id, include_deleted=True)
        assert found is not None
        assert found.is_deleted is True
```

### 2.3 Test Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container"""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    """Create database engine"""
    engine = create_async_engine(
        postgres_container.get_connection_url().replace(
            "postgresql://", "postgresql+asyncpg://"
        ),
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Create database session for each test"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

### 2.4 Test Factories

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from services.tenant.models import TenantModel
from services.user.models import UserModel

fake = Faker()

class BaseMeta:
    sqlalchemy_session = None
    sqlalchemy_session_persistence = "commit"

class TenantFactory(SQLAlchemyModelFactory):
    """Factory for Tenant model"""

    class Meta(BaseMeta):
        model = TenantModel

    code = factory.Sequence(lambda n: f"HTL-{n:03d}")
    name = factory.LazyAttribute(lambda _: fake.company())
    email = factory.LazyAttribute(lambda _: fake.company_email())
    status = "active"
    billing_cycle = "monthly"

class UserFactory(SQLAlchemyModelFactory):
    """Factory for User model"""

    class Meta(BaseMeta):
        model = UserModel

    email = factory.LazyAttribute(lambda _: fake.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    password_hash = "$2b$12$test_hash"
    is_active = True
    is_email_verified = True
```

---

## Part 3: Frontend Testing

### 3.1 Component Tests

```typescript
// tests/components/TenantList.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TenantList } from '@/features/tenants/components/TenantList'

describe('TenantList', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  it('should render tenant list', async () => {
    render(<TenantList />, { wrapper })

    expect(await screen.findByText('Tenants')).toBeInTheDocument()
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('should show loading state', () => {
    render(<TenantList />, { wrapper })

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should filter by status', async () => {
    render(<TenantList />, { wrapper })

    const statusFilter = await screen.findByLabelText('Status')
    fireEvent.change(statusFilter, { target: { value: 'active' } })

    // Verify filter applied
    expect(statusFilter).toHaveValue('active')
  })

  it('should navigate to tenant detail', async () => {
    const onNavigate = vi.fn()
    render(<TenantList onNavigate={onNavigate} />, { wrapper })

    const row = await screen.findByText('HTL-001')
    fireEvent.click(row)

    expect(onNavigate).toHaveBeenCalledWith('/tenants/1')
  })
})
```

### 3.2 Hook Tests

```typescript
// tests/hooks/useTenants.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useTenants } from '@/features/tenants/hooks/useTenants'
import { server } from '@/mocks/server'
import { rest } from 'msw'

describe('useTenants', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  beforeEach(() => {
    queryClient.clear()
  })

  it('should fetch tenants', async () => {
    const { result } = renderHook(() => useTenants(), { wrapper })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.data).toHaveLength(2)
  })

  it('should handle error', async () => {
    server.use(
      rest.get('/api/tenants', (req, res, ctx) => {
        return res(ctx.status(500))
      })
    )

    const { result } = renderHook(() => useTenants(), { wrapper })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
  })
})
```

### 3.3 API Mocking (MSW)

```typescript
// src/mocks/handlers.ts
import { rest } from 'msw'

export const handlers = [
  // List tenants
  rest.get('/api/tenants', (req, res, ctx) => {
    const page = req.url.searchParams.get('page') || '1'
    const status = req.url.searchParams.get('status')

    return res(
      ctx.json({
        data: [
          { id: 1, code: 'HTL-001', name: 'Hotel Group', status: 'active' },
          { id: 2, code: 'HTL-002', name: 'Beach Resort', status: 'trial' },
        ],
        meta: {
          page: parseInt(page),
          per_page: 20,
          total: 2
        }
      })
    )
  }),

  // Get tenant
  rest.get('/api/tenants/:id', (req, res, ctx) => {
    const { id } = req.params
    return res(
      ctx.json({
        data: {
          id: parseInt(id as string),
          code: 'HTL-001',
          name: 'Hotel Group',
          status: 'active'
        }
      })
    )
  }),

  // Create tenant
  rest.post('/api/tenants', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.status(201),
      ctx.json({
        data: {
          id: 3,
          ...body,
          status: 'pending'
        }
      })
    )
  })
]

// src/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

### 3.4 E2E Tests (Playwright)

```typescript
// e2e/tenants.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Tenant Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('[name=email]', 'admin@test.com')
    await page.fill('[name=password]', 'password')
    await page.click('button[type=submit]')
    await page.waitForURL('/dashboard')
  })

  test('should create new tenant', async ({ page }) => {
    // Navigate to tenants
    await page.click('text=Tenants')
    await page.waitForURL('/tenants')

    // Click add button
    await page.click('text=Add Tenant')
    await page.waitForURL('/tenants/new')

    // Fill form
    await page.fill('[name=code]', 'HTL-E2E')
    await page.fill('[name=name]', 'E2E Test Hotel')
    await page.fill('[name=email]', 'e2e@test.com')

    // Submit
    await page.click('button[type=submit]')

    // Verify success
    await expect(page.locator('text=Tenant created')).toBeVisible()
    await expect(page).toHaveURL(/\/tenants\/\d+/)
  })

  test('should filter tenants by status', async ({ page }) => {
    await page.goto('/tenants')

    // Select active status
    await page.selectOption('[name=status]', 'active')

    // Wait for filtered results
    await page.waitForResponse(resp =>
      resp.url().includes('/tenants') && resp.url().includes('status=active')
    )

    // Verify only active tenants shown
    const rows = await page.locator('table tbody tr')
    for (const row of await rows.all()) {
      await expect(row.locator('text=Active')).toBeVisible()
    }
  })

  test('should show tenant detail', async ({ page }) => {
    await page.goto('/tenants')

    // Click first tenant
    await page.click('table tbody tr:first-child')

    // Verify detail page
    await expect(page.locator('h1')).toContainText('HTL-')
    await expect(page.locator('text=Overview')).toBeVisible()
    await expect(page.locator('text=Subscriptions')).toBeVisible()
  })
})
```

---

## Part 4: Test Configuration

### 4.1 pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
filterwarnings =
    ignore::DeprecationWarning
```

### 4.2 vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules',
        'tests',
        '**/*.d.ts',
        '**/*.config.*'
      ],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

### 4.3 playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/e2e.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    }
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI
  }
})
```

---

## Part 5: Coverage Requirements

### 5.1 Coverage Targets

| Layer | Target | Critical Paths |
|-------|--------|----------------|
| Use Cases | 90% | All business logic |
| Validators | 95% | All validation rules |
| Repositories | 80% | CRUD operations |
| API Routes | 80% | All endpoints |
| Components | 70% | User interactions |
| Hooks | 80% | State management |

### 5.2 Coverage Exclusions

```python
# .coveragerc
[run]
omit =
    */migrations/*
    */tests/*
    */__pycache__/*
    */config.py
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    if __name__ == "__main__":
```

---

## Part 6: CI Integration

### 6.1 Test Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest tests/unit -v --cov=app --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration -v --cov=app --cov-report=xml --cov-append

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Part 7: Test Guidelines

### 7.1 Naming Conventions

```python
# Function naming: test_<what>_<when>_<expected>
def test_create_tenant_with_valid_data_returns_tenant():
    pass

def test_create_tenant_with_duplicate_code_raises_error():
    pass

def test_get_tenant_when_not_found_returns_none():
    pass
```

### 7.2 AAA Pattern

```python
def test_calculate_invoice_tax():
    # Arrange
    items = [
        InvoiceItem(amount=Decimal("1000000")),
        InvoiceItem(amount=Decimal("500000"))
    ]
    calculator = TaxCalculator()

    # Act
    result = calculator.calculate(items)

    # Assert
    assert result.subtotal == Decimal("1500000")
    assert result.tax_amount == Decimal("165000")  # 11%
    assert result.total == Decimal("1665000")
```

### 7.3 Test Independence

```python
# BAD - Tests depend on order
class TestTenant:
    tenant_id = None

    def test_create(self):
        TestTenant.tenant_id = create_tenant()

    def test_update(self):
        update_tenant(TestTenant.tenant_id)  # Depends on test_create

# GOOD - Tests are independent
class TestTenant:
    @pytest.fixture
    def tenant(self):
        return create_tenant()

    def test_update(self, tenant):
        update_tenant(tenant.id)  # Has its own tenant
```

### 7.4 Mock External Dependencies

```python
# GOOD - Mock external services
@pytest.fixture
def mock_payment_gateway(mocker):
    return mocker.patch(
        'services.payment.gateway.MidtransGateway',
        return_value=AsyncMock()
    )

async def test_process_payment(mock_payment_gateway):
    mock_payment_gateway.return_value.charge.return_value = {
        "status": "success",
        "transaction_id": "TXN-123"
    }

    result = await payment_service.process(invoice)

    assert result.status == "success"
    mock_payment_gateway.return_value.charge.assert_called_once()
```

---

*Last Updated: 2025-12-07*
