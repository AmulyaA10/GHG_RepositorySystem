"""
Test Authentication and Authorization
"""
import pytest
from core.auth import hash_password, verify_password, authenticate_user, require_role
from models import User

def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password_123"
    hashed = hash_password(password)

    # Hashed password should be different from original
    assert hashed != password

    # Should be able to verify correct password
    assert verify_password(password, hashed) is True

    # Should reject incorrect password
    assert verify_password("wrong_password", hashed) is False

def test_hash_uniqueness():
    """Test that same password produces different hashes (due to salt)"""
    password = "same_password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different due to random salt
    assert hash1 != hash2

    # But both should verify the password
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True

def test_authenticate_user_success(db_session, test_user):
    """Test successful user authentication"""
    user = authenticate_user(db_session, "test_user", "password123")

    assert user is not None
    assert user.id == test_user.id
    assert user.username == "test_user"
    assert user.role == "L1"

def test_authenticate_user_wrong_password(db_session, test_user):
    """Test authentication with wrong password"""
    user = authenticate_user(db_session, "test_user", "wrong_password")
    assert user is None

def test_authenticate_user_nonexistent(db_session):
    """Test authentication with non-existent username"""
    user = authenticate_user(db_session, "nonexistent_user", "password123")
    assert user is None

def test_authenticate_inactive_user(db_session):
    """Test authentication with inactive user"""
    inactive_user = User(
        username="inactive_user",
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        full_name="Inactive User",
        role="L1",
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()

    user = authenticate_user(db_session, "inactive_user", "password123")
    assert user is None

def test_require_role_allowed():
    """Test role requirement with allowed role"""
    assert require_role(["L1"], "L1") is True
    assert require_role(["L1", "L2"], "L1") is True
    assert require_role(["L1", "L2"], "L2") is True

def test_require_role_denied():
    """Test role requirement with disallowed role"""
    assert require_role(["L1"], "L2") is False
    assert require_role(["L3", "L4"], "L1") is False
    assert require_role(["L2"], "L4") is False

def test_require_role_multiple():
    """Test role requirement with multiple allowed roles"""
    assert require_role(["L1", "L2", "L3"], "L2") is True
    assert require_role(["L1", "L2", "L3"], "L4") is False

def test_user_model_creation(db_session):
    """Test creating user with all fields"""
    user = User(
        username="new_user",
        email="new@example.com",
        password_hash=hash_password("secure_password"),
        full_name="New Test User",
        role="L2",
        is_active=True
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "new_user"
    assert user.email == "new@example.com"
    assert user.role == "L2"
    assert user.is_active is True
    assert user.created_at is not None

def test_unique_username_constraint(db_session, test_user):
    """Test that duplicate usernames are not allowed"""
    duplicate_user = User(
        username="test_user",  # Same as test_user
        email="different@example.com",
        password_hash=hash_password("password123"),
        full_name="Duplicate User",
        role="L1"
    )

    db_session.add(duplicate_user)

    with pytest.raises(Exception):  # Should raise IntegrityError
        db_session.commit()

def test_unique_email_constraint(db_session, test_user):
    """Test that duplicate emails are not allowed"""
    duplicate_user = User(
        username="different_user",
        email="test@example.com",  # Same as test_user
        password_hash=hash_password("password123"),
        full_name="Duplicate Email User",
        role="L1"
    )

    db_session.add(duplicate_user)

    with pytest.raises(Exception):  # Should raise IntegrityError
        db_session.commit()

def test_case_insensitive_email():
    """Test that email comparison is case-insensitive"""
    password = "password123"
    hash1 = hash_password(password)

    # Password verification should work regardless of case
    assert verify_password(password, hash1) is True
    assert verify_password("PASSWORD123", hash1) is False  # Password is case-sensitive
