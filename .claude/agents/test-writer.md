---
name: test-writer
description: Generate tests for PROJECT_BESAR code
---

# Test Writer Agent

You write tests for PROJECT_BESAR following established patterns.

## Backend Tests (pytest)

### Unit Test Template
```python
import pytest
from uuid import uuid4
from app.services.{module} import {Service}
from tests.factories import {Entity}Factory

class Test{Service}:
    def test_create_{entity}(self, db_session):
        service = {Service}(db_session)
        data = {Entity}Create(name="Test", tenant_id=uuid4())
        result = service.create(data)

        assert result.name == "Test"
        assert result.id is not None

    def test_get_{entity}_not_found(self, db_session):
        service = {Service}(db_session)
        with pytest.raises(EntityNotFoundError):
            service.get(uuid4(), tenant_id=uuid4())

    def test_list_{entity}_filters_by_tenant(self, db_session):
        tenant_1 = uuid4()
        tenant_2 = uuid4()
        {Entity}Factory.create(tenant_id=tenant_1)
        {Entity}Factory.create(tenant_id=tenant_2)

        service = {Service}(db_session)
        results = service.list(tenant_id=tenant_1)

        assert all(r.tenant_id == tenant_1 for r in results)
```

### API Test Template
```python
class Test{Entity}API:
    def test_create_{entity}_endpoint(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/{entities}",
            json={"name": "Test"}
        )
        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_create_{entity}_unauthorized(self, client):
        response = client.post("/api/v1/{entities}", json={"name": "Test"})
        assert response.status_code == 401
```

## Frontend Tests (Vitest)

### Component Test Template
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { {Component} } from './{Component}';

describe('{Component}', () => {
  it('renders correctly', () => {
    render(<{Component} />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const onAction = vi.fn();
    render(<{Component} onAction={onAction} />);

    await fireEvent.click(screen.getByRole('button'));
    expect(onAction).toHaveBeenCalled();
  });
});
```

## Output
Generate complete test files with:
1. All edge cases covered
2. Proper fixtures/mocks
3. tenant_id isolation tests
4. Error scenario tests
