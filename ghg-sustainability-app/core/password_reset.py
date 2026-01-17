"""
Password Reset Utilities
Handles password reset token generation, validation, and reset flow
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from models import User, PasswordResetToken
from core.email import email_service

logger = logging.getLogger(__name__)


def create_password_reset_token(
    db: Session,
    user: User,
    expiration_hours: int = 24
) -> Optional[PasswordResetToken]:
    """
    Create a password reset token for a user

    Args:
        db: Database session
        user: User object
        expiration_hours: Token expiration in hours (default 24)

    Returns:
        PasswordResetToken: Created token object or None on failure
    """
    try:
        # Invalidate any existing unused tokens for this user
        existing_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).all()

        for token in existing_tokens:
            token.used = True
            token.used_at = datetime.utcnow()

        # Create new token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=PasswordResetToken.generate_token(),
            expires_at=PasswordResetToken.get_expiration_time(expiration_hours)
        )

        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)

        logger.info(f"Password reset token created for user: {user.username}")
        return reset_token

    except Exception as e:
        logger.error(f"Error creating password reset token: {e}")
        db.rollback()
        return None


def validate_reset_token(
    db: Session,
    token: str
) -> Optional[PasswordResetToken]:
    """
    Validate a password reset token

    Args:
        db: Database session
        token: Token string

    Returns:
        PasswordResetToken: Valid token object or None if invalid
    """
    try:
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()

        if not reset_token:
            logger.warning(f"Password reset token not found: {token[:10]}...")
            return None

        if not reset_token.is_valid():
            if reset_token.used:
                logger.warning(f"Password reset token already used: {token[:10]}...")
            else:
                logger.warning(f"Password reset token expired: {token[:10]}...")
            return None

        return reset_token

    except Exception as e:
        logger.error(f"Error validating reset token: {e}")
        return None


def reset_password(
    db: Session,
    token: str,
    new_password_hash: str
) -> tuple[bool, str]:
    """
    Reset user password using token

    Args:
        db: Database session
        token: Reset token string
        new_password_hash: Hashed new password

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Validate token
        reset_token = validate_reset_token(db, token)

        if not reset_token:
            return False, "Invalid or expired reset token"

        # Get user
        user = db.query(User).filter(User.id == reset_token.user_id).first()

        if not user:
            return False, "User not found"

        if not user.is_active:
            return False, "User account is disabled"

        # Update password
        user.password_hash = new_password_hash

        # Mark token as used
        reset_token.used = True
        reset_token.used_at = datetime.utcnow()

        db.commit()

        logger.info(f"Password reset successful for user: {user.username}")

        # Send confirmation email (non-blocking)
        try:
            email_service.send_password_changed_notification(
                user.email,
                user.username
            )
        except Exception as e:
            logger.warning(f"Failed to send password change notification: {e}")

        return True, "Password reset successful"

    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        db.rollback()
        return False, f"Error resetting password: {str(e)}"


def send_password_reset_email(
    db: Session,
    email_or_username: str,
    reset_url_base: str
) -> tuple[bool, str]:
    """
    Send password reset email to user

    Args:
        db: Database session
        email_or_username: User's email or username
        reset_url_base: Base URL for reset link (e.g., "http://localhost:8501/Reset_Password")

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Check if email service is configured
        if not email_service.is_configured():
            logger.error("Email service not configured")
            return False, "Email service not configured. Please contact administrator."

        # Find user by email or username
        user = db.query(User).filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()

        # Always return success message to prevent user enumeration
        success_message = "If an account exists with that email/username, a password reset link has been sent."

        if not user:
            logger.warning(f"Password reset requested for non-existent user: {email_or_username}")
            return True, success_message

        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {user.username}")
            return True, success_message

        # Create reset token
        reset_token = create_password_reset_token(db, user)

        if not reset_token:
            logger.error(f"Failed to create reset token for user: {user.username}")
            return False, "Failed to generate reset token. Please try again."

        # Build reset link
        reset_link = f"{reset_url_base}?token={reset_token.token}"

        # Send email
        email_sent = email_service.send_password_reset_email(
            user.email,
            user.username,
            reset_link
        )

        if not email_sent:
            logger.error(f"Failed to send reset email to: {user.email}")
            return False, "Failed to send reset email. Please try again or contact support."

        logger.info(f"Password reset email sent to: {user.email}")
        return True, success_message

    except Exception as e:
        logger.error(f"Error in send_password_reset_email: {e}")
        return False, "An error occurred. Please try again."


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired password reset tokens
    Should be run periodically (e.g., daily cron job)

    Args:
        db: Database session

    Returns:
        int: Number of tokens deleted
    """
    try:
        # Delete tokens that expired more than 7 days ago
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        deleted = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {deleted} expired password reset tokens")
        return deleted

    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        db.rollback()
        return 0
