"""
AdTicks — Pagination and standardized response schemas.

Provides:
- Pagination request model with limits
- Generic paginated response wrapper
- Standard API response envelope
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(
        50,
        ge=1,
        le=500,
        description="Number of items to return (max 500)"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    data: list[T]
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Number of items returned")
    has_more: bool = Field(description="Whether more items are available")
    
    @classmethod
    def create(cls, data: list[T], total: int, skip: int, limit: int):
        """Factory method to create a paginated response."""
        return cls(
            data=data,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""
    success: bool = Field(description="Whether request was successful")
    data: T | None = Field(default=None, description="Response data")
    error: str | None = Field(default=None, description="Error code if unsuccessful")
    message: str | None = Field(default=None, description="Human-readable message")
    
    @classmethod
    def success_response(cls, data: T, message: str | None = None):
        """Factory for success response."""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, error: str, message: str):
        """Factory for error response."""
        return cls(success=False, error=error, message=message)
