"""
Password History Repository Implementation
Prevents password reuse by checking against stored password history
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from shared.database import Base


class PasswordHistoryModel(Base):
    """Password history database model"""
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)


class PasswordHistoryRepository:
    """Repository for managing password history"""

    # Default: prevent reuse of last 5 passwords
    DEFAULT_HISTORY_LIMIT = 5

    def __init__(self, db: Session):
        self.db = db

    def get_recent_hashes(self, user_id: int, limit: int = None) -> List[str]:
        """
        Get recent password hashes for a user

        Args:
            user_id: User ID
            limit: Number of recent passwords to check (default: 5)

        Returns:
            List of password hashes (most recent first)
        """
        if limit is None:
            limit = self.DEFAULT_HISTORY_LIMIT

        records = self.db.query(PasswordHistoryModel).filter(
            PasswordHistoryModel.user_id == user_id
        ).order_by(
            PasswordHistoryModel.created_at.desc()
        ).limit(limit).all()

        return [record.password_hash for record in records]

    def add_to_history(self, user_id: int, password_hash: str) -> PasswordHistoryModel:
        """
        Add a password hash to history

        Args:
            user_id: User ID
            password_hash: Bcrypt hashed password

        Returns:
            Created PasswordHistoryModel
        """
        record = PasswordHistoryModel(
            user_id=user_id,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def cleanup_old_history(self, user_id: int, keep_count: int = None):
        """
        Remove old password history entries, keeping only the most recent N

        Args:
            user_id: User ID
            keep_count: Number of recent passwords to keep (default: 5)
        """
        if keep_count is None:
            keep_count = self.DEFAULT_HISTORY_LIMIT

        # Get IDs of records to keep
        keep_records = self.db.query(PasswordHistoryModel.id).filter(
            PasswordHistoryModel.user_id == user_id
        ).order_by(
            PasswordHistoryModel.created_at.desc()
        ).limit(keep_count).subquery()

        # Delete records not in keep list
        self.db.query(PasswordHistoryModel).filter(
            PasswordHistoryModel.user_id == user_id,
            ~PasswordHistoryModel.id.in_(keep_records)
        ).delete(synchronize_session=False)

        self.db.commit()

    def count_history(self, user_id: int) -> int:
        """Count password history entries for a user"""
        return self.db.query(PasswordHistoryModel).filter(
            PasswordHistoryModel.user_id == user_id
        ).count()
