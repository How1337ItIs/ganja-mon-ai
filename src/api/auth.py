"""
JWT Authentication Module
=========================
Based on SECURITY_PATTERNS.md research.
Database-backed JWT auth for API protection.

Security features:
- Rate limiting on login attempts
- No hardcoded default secrets in production
- Failed login tracking
- Configurable token expiration
- Database-backed user storage
"""

import os
import time
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import defaultdict

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select


# =============================================================================
# Configuration
# =============================================================================

# Environment detection
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() == "production"

# Get secret from env - FAIL in production if not set
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

if SECRET_KEY is None:
    if IS_PRODUCTION:
        raise RuntimeError("FATAL: JWT_SECRET_KEY must be set in production environment!")
    else:
        # Generate a random secret for development (changes on restart)
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using random JWT secret (will invalidate tokens on restart). Set JWT_SECRET_KEY for persistence.")

# Validate secret strength in production
if IS_PRODUCTION and len(SECRET_KEY) < 32:
    raise RuntimeError("FATAL: JWT_SECRET_KEY must be at least 32 characters in production!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# =============================================================================
# Rate Limiting
# =============================================================================

# Track failed login attempts: {ip_address: [(timestamp, count), ...]}
_login_attempts: Dict[str, list] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_ATTEMPTS = 5


def _cleanup_old_attempts(ip: str) -> None:
    """Remove attempts older than the rate limit window."""
    now = time.time()
    _login_attempts[ip] = [
        (ts, count) for ts, count in _login_attempts[ip]
        if now - ts < RATE_LIMIT_WINDOW
    ]


def _check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded rate limit. Returns True if allowed."""
    _cleanup_old_attempts(ip)
    total_attempts = sum(count for _, count in _login_attempts[ip])
    return total_attempts < RATE_LIMIT_MAX_ATTEMPTS


def _record_attempt(ip: str) -> None:
    """Record a failed login attempt."""
    _login_attempts[ip].append((time.time(), 1))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)


# =============================================================================
# Models
# =============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None
    is_admin: Optional[bool] = False

class UserInDB(User):
    hashed_password: str


# =============================================================================
# Database-Backed User Store
# =============================================================================

# Admin password MUST be set via environment variable
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if ADMIN_PASSWORD is None:
    if IS_PRODUCTION:
        raise RuntimeError("FATAL: ADMIN_PASSWORD must be set in production environment!")
    else:
        # Generate random password for development
        ADMIN_PASSWORD = secrets.token_urlsafe(16)
        print(f"WARNING: Using random admin password: {ADMIN_PASSWORD}")
        print("Set ADMIN_PASSWORD environment variable for a persistent password.")

# Viewer password from environment (optional user)
VIEWER_PASSWORD = os.environ.get("VIEWER_PASSWORD")

# Track whether admin user has been migrated to database
_admin_migrated = False


async def _ensure_admin_user():
    """Ensure admin user exists in database. Auto-migrate on first startup."""
    global _admin_migrated
    if _admin_migrated:
        return

    try:
        from src.db.connection import get_db_session
        from src.db.models import User as DBUser

        async with get_db_session() as session:
            # Check if admin user exists
            result = await session.execute(
                select(DBUser).where(DBUser.username == "admin")
            )
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                # Create admin user
                admin_user = DBUser(
                    username="admin",
                    hashed_password=pwd_context.hash(ADMIN_PASSWORD),
                    disabled=False,
                    is_admin=True,
                )
                session.add(admin_user)
                await session.commit()
                print("[AUTH] Admin user created in database")

            # Also create viewer user if password is set
            if VIEWER_PASSWORD:
                result = await session.execute(
                    select(DBUser).where(DBUser.username == "viewer")
                )
                viewer_user = result.scalar_one_or_none()
                if not viewer_user:
                    viewer_user = DBUser(
                        username="viewer",
                        hashed_password=pwd_context.hash(VIEWER_PASSWORD),
                        disabled=False,
                        is_admin=False,
                    )
                    session.add(viewer_user)
                    await session.commit()
                    print("[AUTH] Viewer user created in database")

        _admin_migrated = True
    except Exception as e:
        print(f"[AUTH] Warning: Could not migrate users to database: {e}")
        # Fall back to in-memory for this session
        _admin_migrated = True


async def get_user_from_db(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    try:
        from src.db.connection import get_db_session
        from src.db.models import User as DBUser

        await _ensure_admin_user()

        async with get_db_session() as session:
            result = await session.execute(
                select(DBUser).where(DBUser.username == username)
            )
            db_user = result.scalar_one_or_none()

            if db_user:
                return UserInDB(
                    username=db_user.username,
                    hashed_password=db_user.hashed_password,
                    disabled=db_user.disabled,
                    is_admin=db_user.is_admin,
                )
        return None
    except Exception as e:
        print(f"[AUTH] Database error, falling back to in-memory: {e}")
        # Fallback to in-memory for backward compatibility
        fallback_users = {
            "admin": UserInDB(
                username="admin",
                hashed_password=pwd_context.hash(ADMIN_PASSWORD),
                disabled=False,
                is_admin=True,
            )
        }
        if VIEWER_PASSWORD:
            fallback_users["viewer"] = UserInDB(
                username="viewer",
                hashed_password=pwd_context.hash(VIEWER_PASSWORD),
                disabled=False,
                is_admin=False,
            )
        return fallback_users.get(username)


# =============================================================================
# Helper Functions
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


async def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    return await get_user_from_db(username)


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password"""
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =============================================================================
# Dependency Functions
# =============================================================================

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Get current user from JWT token.
    Returns None if no token or invalid token (for optional auth).
    """
    if token is None:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None

    user = await get_user(username=token_data.username)
    if user is None:
        return None

    return User(
        username=user.username,
        disabled=user.disabled,
        is_admin=user.is_admin,
    )


async def get_current_user_required(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current user from JWT token.
    Raises 401 if no token or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return User(
        username=user.username,
        disabled=user.disabled,
        is_admin=user.is_admin,
    )


async def get_current_admin(current_user: User = Depends(get_current_user_required)) -> User:
    """Get current user and verify they are an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# =============================================================================
# Route Handlers (to be registered in app.py)
# =============================================================================

async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    OAuth2 compatible token login with rate limiting.
    POST /api/auth/token with form data: username, password

    Rate limited to 5 attempts per minute per IP address.
    """
    # Get client IP (handle proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        # Record failed attempt
        _record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


async def get_current_user_info(current_user: User = Depends(get_current_user_required)) -> dict:
    """Get info about the currently authenticated user"""
    return {
        "username": current_user.username,
        "is_admin": current_user.is_admin,
    }
