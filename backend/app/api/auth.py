"""
AdTicks — Auth router.

Endpoints
---------
POST /auth/register  — create a new account
POST /auth/login     — obtain a JWT
GET  /auth/me        — return the authenticated user
POST /auth/refresh   — refresh an access token using a refresh token
POST /auth/logout    — logout (client-side token invalidation)
"""

import uuid
from fastapi import APIRouter, Depends, Request, status, File, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.transactions import transaction_scope
from app.core.storage import storage
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.models.user import User
from app.schemas.user import RefreshTokenRequest, Token, UserCreate, UserLogin, UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

# OAuth2 scheme for token extraction
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_token(token: str = Depends(_oauth2_scheme)) -> str:
    """Extract and return the current token."""
    return token




@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user account with email and password. The email must be unique.
    
    **Request body:**
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be hashed before storage)
    - **full_name**: User's full name
    
    **Returns:**
    - User object with id, email, full_name, and timestamps
    
    **Responses:**
    - 201 Created: User successfully registered
    - 409 Conflict: Email already registered
    - 422 Unprocessable Entity: Invalid input
    """
    async with transaction_scope(db) as tx:
        # Check if email already exists
        result = await tx.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none():
            logger.warning("registration_failed", extra={"email": payload.email, "reason": "email_exists"})
            raise ConflictError("Email already registered")
        
        # Create user
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        tx.add(user)
        await tx.flush()
        
        logger.info("user_registered", extra={"user_id": str(user.id), "email": user.email})
        return user


@router.post("/login", response_model=Token)
async def login(
    request: Request, payload: UserLogin, db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and receive JWT tokens.
    
    Validates email and password credentials. Returns JWT access token (expires in 1 hour)
    and refresh token (expires in 7 days).
    
    **Request body:**
    - **email**: User's registered email
    - **password**: User's password
    
    **Returns:**
    - **access_token**: JWT token for API requests (1 hour validity)
    - **refresh_token**: Token to refresh access_token (7 days validity)
    - **token_type**: Always "bearer"
    
    **Responses:**
    - 200 OK: Authentication successful
    - 401 Unauthorized: Invalid credentials or inactive account
    - 422 Unprocessable Entity: Invalid input
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(
            "login_failed",
            extra={
                "email": payload.email,
                "reason": "invalid_credentials",
                "ip": request.client.host if request.client else "unknown",
            },
        )
        raise AuthenticationError("Invalid email or password")
    
    if not user.is_active:
        logger.warning("login_failed", extra={"email": payload.email, "reason": "inactive_user"})
        raise AuthenticationError("Account is inactive")
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    logger.info("user_login", extra={"user_id": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh the access token using a refresh token.
    
    When the access token expires, use the refresh token to obtain a new access token
    and refresh token pair without re-authenticating.
    
    **Request body:**
    - **refresh_token**: The refresh token received during login
    
    **Returns:**
    - **access_token**: New JWT token for API requests (1 hour validity)
    - **refresh_token**: New refresh token (7 days validity)
    - **token_type**: Always "bearer"
    
    **Responses:**
    - 200 OK: Token refreshed successfully
    - 401 Unauthorized: Invalid or expired refresh token
    - 422 Unprocessable Entity: Invalid input
    """
    try:
        user_id = verify_refresh_token(payload.refresh_token)
    except Exception as e:
        logger.warning("refresh_token_invalid", extra={"error": str(e)})
        raise AuthenticationError("Invalid refresh token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        logger.warning("refresh_failed", extra={"user_id": str(user_id), "reason": "user_inactive"})
        raise AuthenticationError("User not found or inactive")
    
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    logger.info("token_refreshed", extra={"user_id": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_token),
):
    """
    Logout and revoke the current access token.
    
    Adds the token to a revocation blacklist. The token cannot be used for
    future API requests after logout.
    
    **Authentication:** Required (Bearer token)
    
    **Returns:**
    - Success message
    
    **Responses:**
    - 200 OK: Logged out successfully
    - 401 Unauthorized: Invalid or missing token
    """
    from app.core.security import revoke_token
    
    await revoke_token(token)
    logger.info("user_logout", extra={"user_id": str(current_user.id)})
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    
    Returns the currently authenticated user's information including email,
    full name, and account status.
    
    **Authentication:** Required (Bearer token)
    
    **Returns:**
    - User object with id, email, full_name, is_active, created_at, updated_at
    
    **Responses:**
    - 200 OK: User profile returned
    - 401 Unauthorized: Invalid or missing token
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's profile information.
    
    **Authentication:** Required (Bearer token)
    
    **Returns:**
    - Updated user object
    """
    async with transaction_scope(db) as tx:
        if payload.full_name is not None:
            current_user.full_name = payload.full_name
            
        if payload.company_name is not None:
            current_user.company_name = payload.company_name
        
        if payload.email is not None:
            # Check if email is already taken by another user
            if payload.email != current_user.email:
                result = await tx.execute(select(User).where(User.email == payload.email))
                if result.scalar_one_or_none():
                    raise ConflictError("Email already registered")
                current_user.email = payload.email
        
        if payload.password is not None:
            current_user.hashed_password = hash_password(payload.password)
            
        tx.add(current_user)
        await tx.flush()
        
        logger.info("user_updated", extra={"user_id": str(current_user.id)})
        return current_user


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a new profile avatar.
    """
    # 1. Validate file extension
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension"
        )

    # 2. Read content
    content = await file.read()
    
    # 3. Upload to storage
    filename = f"avatar_{uuid.uuid4().hex}.{ext}"
    path = storage.avatar_path(str(current_user.id), filename)
    
    try:
        public_url = storage.upload_file(path, content)
    except Exception as exc:
        logger.error("Failed to upload avatar: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )

    # 4. Update user record
    async with transaction_scope(db) as tx:
        # Delete old avatar if exists
        if current_user.avatar_url:
            try:
                # Extract path from URL (naive)
                old_path = current_user.avatar_url.split(settings.DO_SPACES_BUCKET + "/")[-1]
                storage.delete_file(old_path)
            except Exception:
                pass
        
        current_user.avatar_url = public_url
        tx.add(current_user)
        await tx.flush()
        
    return current_user
