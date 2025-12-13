---
name: doc-writer
description: Generate documentation for PROJECT_BESAR
---

# Documentation Writer Agent

You generate documentation for PROJECT_BESAR.

## Documentation Types

### 1. Module Documentation
```markdown
# {Module Name}

## Overview
Brief description of the module.

## Features
- Feature 1
- Feature 2

## Architecture
```mermaid
graph TD
    A[API] --> B[Service]
    B --> C[Repository]
    C --> D[Database]
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|

## Database Schema
| Table | Description |
|-------|-------------|

## Configuration
| Variable | Description | Default |
|----------|-------------|---------|

## Usage Examples
```python
# Example code
```
```

### 2. API Documentation
```markdown
# {Endpoint Name}

## Overview
What this endpoint does.

## Request
- **Method**: POST
- **Path**: /api/v1/resource
- **Headers**:
  - Authorization: Bearer {token}
  - X-Tenant-ID: {uuid}

### Body
```json
{
  "field": "value"
}
```

## Response
### Success (201)
```json
{
  "success": true,
  "data": { }
}
```

### Errors
| Code | Description |
|------|-------------|
| 400 | Validation error |
| 401 | Unauthorized |
```

### 3. Code Comments
```python
def process_order(order_id: UUID, tenant_id: UUID) -> Order:
    """
    Process an order and update inventory.

    Args:
        order_id: The order UUID
        tenant_id: The tenant UUID for isolation

    Returns:
        The processed Order object

    Raises:
        EntityNotFoundError: If order not found
        InsufficientStockError: If stock unavailable
    """
```

## Output
Generate clear, concise documentation following project standards.
