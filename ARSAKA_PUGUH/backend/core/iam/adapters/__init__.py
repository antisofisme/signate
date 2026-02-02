"""
IAM Adapters

Concrete implementations of IAM interfaces.
"""

from .postgres_iam_repository import PostgresIAMRepository

__all__ = ["PostgresIAMRepository"]
