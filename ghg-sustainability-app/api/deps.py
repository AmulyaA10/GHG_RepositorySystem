"""
FastAPI Dependencies
Common dependencies for API routes
"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import SessionLocal, get_db as db_generator
from core.agent import GHGAppAgent
from models.user import User
from api.auth import get_current_user


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_agent(db: Session = Depends(get_db)) -> GHGAppAgent:
    """
    GHGAppAgent dependency.

    Args:
        db: Database session

    Returns:
        GHGAppAgent: Agent instance
    """
    return GHGAppAgent(db)


class CurrentUserWithRole:
    """
    Dependency class for getting current user with role validation.
    """

    def __init__(self, allowed_roles: list = None):
        self.allowed_roles = allowed_roles or ["L1", "L2", "L3", "L4"]

    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        from fastapi import HTTPException, status

        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user
