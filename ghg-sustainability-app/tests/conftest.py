"""
Pytest Configuration and Fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db import Base
from models import User, Project, Criteria
from core.auth import hash_password

# Test database URL (use SQLite in memory for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role="L1",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_project(db_session, test_user):
    """Create a test project"""
    project = Project(
        project_name="Test Project",
        organization_name="Test Org",
        reporting_year=2024,
        status="DRAFT",
        created_by=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture
def test_criteria(db_session):
    """Create test criteria"""
    criteria = Criteria(
        criteria_number=1,
        scope="Scope 1",
        category="Stationary Combustion",
        unit="liters",
        is_active=True
    )
    db_session.add(criteria)
    db_session.commit()
    db_session.refresh(criteria)
    return criteria
