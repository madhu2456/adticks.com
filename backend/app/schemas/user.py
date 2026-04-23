"""AdTicks user Pydantic schemas with comprehensive validation."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration with strict validation."""
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="User's full name"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password has mix of uppercase, lowercase, and digits."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Schema for user responses (excludes sensitive data)."""
    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_superuser: bool
    plan: str
    trial_ends_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token responses."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="Long-lived refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""
    refresh_token: str = Field(description="Valid refresh token")
