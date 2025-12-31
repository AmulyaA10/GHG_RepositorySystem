"""
Authentication and Authorization Module
"""
import bcrypt
import streamlit as st
from sqlalchemy.orm import Session
from models.user import User
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    user = db.query(User).filter(User.username == username, User.is_active == True).first()

    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        return None

    if not verify_password(password, user.password_hash):
        logger.warning(f"Invalid password for username: {username}")
        return None

    logger.info(f"User authenticated successfully: {username}")
    return user

def get_current_user() -> Optional[Dict]:
    """
    Get currently logged-in user from session

    Returns:
        Optional[Dict]: User data dictionary
    """
    return st.session_state.get('user')

def require_role(allowed_roles: list) -> bool:
    """
    Check if current user has one of the allowed roles

    Args:
        allowed_roles: List of allowed role codes (e.g., ['L1', 'L2'])

    Returns:
        bool: True if user has required role
    """
    user = get_current_user()

    if not user:
        st.error("⛔ Please log in to access this page")
        st.stop()
        return False

    # Handle both dict and object
    user_role = user.role if hasattr(user, 'role') else user.get('role')

    if user_role not in allowed_roles:
        st.error(f"⛔ Access Denied. This page requires one of these roles: {', '.join(allowed_roles)}")
        st.stop()
        return False

    return True

def logout():
    """Logout the current user"""
    if 'user' in st.session_state:
        user = st.session_state.user
        username = user.username if hasattr(user, 'username') else user.get('username', 'unknown')
        logger.info(f"User logged out: {username}")
        st.session_state.clear()
