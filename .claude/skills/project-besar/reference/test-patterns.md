---
description: Test patterns for PROJECT_BESAR
---

# Test Patterns Reference

## Backend (pytest)

### Test Structure
```
tests/
├── unit/
│   ├── test_services/
│   └── test_utils/
├── integration/
│   ├── test_api/
│   └── test_repositories/
├── conftest.py
└── factories.py
```

### Fixtures
```python
# conftest.py
@pytest.fixture
def db_session():
    # Transaction-based test isolation
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c

@pytest.fixture
def authenticated_client(client, test_user):
    token = create_token(test_user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### Factory Pattern
```python
# factories.py
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    name = factory.Faker('name')
    email = factory.Faker('email')
```

### Test Examples
```python
class TestUserService:
    def test_create_user(self, db_session):
        service = UserService(db_session)
        user = service.create(UserCreate(name="Test"))
        assert user.name == "Test"

    def test_get_user_not_found(self, db_session):
        service = UserService(db_session)
        with pytest.raises(EntityNotFoundError):
            service.get(uuid4())

class TestUserAPI:
    def test_create_user_endpoint(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/users",
            json={"name": "Test"}
        )
        assert response.status_code == 201
```

## Frontend (Vitest)

### Test Structure
```
src/
├── components/
│   └── UserCard/
│       ├── UserCard.tsx
│       └── UserCard.test.tsx
└── hooks/
    └── useUser.test.ts
```

### Component Test
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  it('renders user name', () => {
    render(<UserCard user={{ name: 'John' }} />);
    expect(screen.getByText('John')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<UserCard user={{ name: 'John' }} onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

### Hook Test
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useUser } from './useUser';

describe('useUser', () => {
  it('fetches user data', async () => {
    const { result } = renderHook(() => useUser('123'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data.name).toBe('John');
  });
});
```

## Coverage Target: 80%
```bash
# Backend
pytest --cov=app --cov-fail-under=80

# Frontend
bun test --coverage --coverageThreshold='{"global":{"lines":80}}'
```
