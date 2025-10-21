"""
User Model
Authentication and authorization for admin users
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    User model for admin authentication

    Attributes:
        id: Primary key
        username: Unique username for login
        email: User email address
        password_hash: Bcrypt hashed password
        role: User role (admin, editor, viewer)
        is_active: Whether user account is active
        created_at: Timestamp when user was created
        last_login: Timestamp of last login
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # User Credentials
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Role (admin, editor, viewer)
    role = Column(String(20), default='viewer', nullable=False)

    # Status Flags
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

    # Helper property for backward compatibility
    @property
    def is_superuser(self) -> bool:
        """Check if user is superuser (admin role)"""
        return self.role == 'admin'

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
