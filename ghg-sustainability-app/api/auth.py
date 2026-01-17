"""
JWT Authentication for FastAPI

Security features:
- JWT token-based authentication
- Role-based access control (RBAC)
- Token expiration
- Secure password verification
- Audit logging for security events
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.db import get_db
from core.auth import verify_password
from models.user import User

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = settings.SESSION_LIFETIME_HOURS
TOKEN_ISSUER = "ghg-sustainability-api"
TOKEN_AUDIENCE = "ghg-sustainability-app"

# Validate secret key on module load
if not SECRET_KEY or SECRET_KEY == "dev-secret-key-change-in-production":
    logger.warning(
        "WARNING: Using default or weak SECRET_KEY. "
        "Set a strong SECRET_KEY in production!"
    )

# Security scheme
security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT token",
    auto_error=True
)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid."""
    pass


def create_access_token(user: User) -> str:
    """
    Create JWT access token for a user.

    Args:
        user: User object

    Returns:
        str: JWT token

    Raises:
        ValueError: If user is None
    """
    if user is None:
        raise ValueError("User cannot be None")

    now = datetime.utcnow()
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        # Standard claims
        "sub": str(user.id),
        "iat": now,
        "exp": expire,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        # Custom claims
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
    }

    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Token created for user {user.username} (ID: {user.id})")
        return token
    except Exception as e:
        logger.error(f"Failed to create token for user {user.id}: {e}")
        raise


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=TOKEN_AUDIENCE,
            issuer=TOKEN_ISSUER
        )
        return payload

    except ExpiredSignatureError:
        logger.warning(f"Expired token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password.

    Uses constant-time comparison for password verification to prevent
    timing attacks.

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if not username or not password:
        logger.warning("Authentication attempt with empty credentials")
        return None

    try:
        # Query user - always query to prevent timing attacks
        user = db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()

        if not user:
            # Perform dummy password check to prevent timing attacks
            verify_password("dummy_password", "$2b$12$dummy_hash_for_timing")
            logger.warning(f"Failed login attempt for unknown user: {username}")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {username} (wrong password)")
            return None

        logger.info(f"Successful authentication for user: {username}")
        return user

    except SQLAlchemyError as e:
        logger.error(f"Database error during authentication: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")

        if not user_id_str:
            logger.warning("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier"
            )

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id in token: {user_id_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: invalid user identifier"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    try:
        user = db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )

    if user is None:
        logger.warning(f"Token references non-existent user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        logger.warning(f"Disabled user attempted access: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory to require specific roles.

    Args:
        allowed_roles: List of allowed role codes (e.g., ["L1", "L2"])

    Returns:
        Dependency function that validates user role
    """
    if not allowed_roles:
        raise ValueError("allowed_roles cannot be empty")

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Access denied for user {current_user.username} "
                f"(role: {current_user.role}, required: {allowed_roles})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


# Pre-defined role dependencies for common access patterns
require_l1 = require_roles(["L1"])
require_l2 = require_roles(["L2"])
require_l3 = require_roles(["L3"])
require_l4 = require_roles(["L4"])
require_l1_or_l2 = require_roles(["L1", "L2"])
require_l2_or_l3 = require_roles(["L2", "L3"])
require_l3_or_l4 = require_roles(["L3", "L4"])
require_any = require_roles(["L1", "L2", "L3", "L4"])
