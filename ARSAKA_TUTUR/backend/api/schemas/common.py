"""
Common schema components.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")

    @property
    def has_more(self) -> bool:
        """Check if there are more items."""
        return self.offset + self.limit < self.total


class TokenUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(0, description="Input tokens")
    completion_tokens: int = Field(0, description="Output tokens")

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class ContextInfo(BaseModel):
    """Request context information."""
    page: Optional[str] = Field(None, description="Page context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
