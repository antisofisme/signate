---
description: Validation patterns for PROJECT_BESAR
---

# Validation Patterns Reference

## Pydantic (Backend)

```python
from pydantic import BaseModel, Field, validator, EmailStr
from uuid import UUID
from datetime import date
from typing import Literal

class EntityCreate(BaseModel):
    # Required with constraints
    name: str = Field(..., min_length=1, max_length=100)

    # Optional
    description: str | None = None

    # Regex pattern
    code: str = Field(..., regex=r'^[A-Z]{3}-\d{3}$')

    # Numeric range
    amount: Decimal = Field(..., ge=0, le=999999.99)

    # Email
    email: EmailStr

    # Enum/Literal
    status: Literal["active", "inactive"]

    # Custom validator
    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Cannot be empty')
        return v.strip()

    class Config:
        str_strip_whitespace = True
```

## Zod (Frontend)

```typescript
import { z } from 'zod';

export const entitySchema = z.object({
  // Required
  name: z.string().min(1, 'Required').max(100),

  // Optional
  description: z.string().optional(),

  // Regex
  code: z.string().regex(/^[A-Z]{3}-\d{3}$/, 'Format: ABC-123'),

  // Number
  amount: z.number().min(0).max(999999.99),

  // Email
  email: z.string().email('Invalid email'),

  // Enum
  status: z.enum(['active', 'inactive']),

  // Date
  date: z.date(),

  // UUID
  id: z.string().uuid(),

  // Array
  tags: z.array(z.string()).min(1),

  // Nested
  address: z.object({
    street: z.string(),
    city: z.string(),
  }),
});

// Infer type
type EntityFormData = z.infer<typeof entitySchema>;
```

## Common Patterns

| Validation | Pydantic | Zod |
|------------|----------|-----|
| Required | `Field(...)` | `.min(1)` |
| Optional | `\| None = None` | `.optional()` |
| Email | `EmailStr` | `.email()` |
| UUID | `UUID` | `.uuid()` |
| Min/Max | `Field(ge=, le=)` | `.min().max()` |
| Regex | `Field(regex=)` | `.regex()` |
| Enum | `Literal[...]` | `.enum([...])` |
