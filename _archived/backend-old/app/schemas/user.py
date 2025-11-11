"""
User schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_superuser: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "is_active": True,
                "is_superuser": False
            }
        }


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "updated@example.com",
                "full_name": "Updated Name",
                "is_active": True
            }
        }
