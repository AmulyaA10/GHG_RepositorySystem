"""
Configuration Management for GHG Sustainability Application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file (for local development)
load_dotenv()

def get_database_url():
    """
    Get database URL from multiple sources with validation
    Priority: Streamlit secrets > Environment variable > Default
    """
    database_url = None

    # 1. Try Streamlit secrets (for Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            database_url = st.secrets['DATABASE_URL']
            logger.info("Using DATABASE_URL from Streamlit secrets")
    except ImportError:
        pass  # Streamlit not available (running tests, etc.)
    except Exception as e:
        logger.warning(f"Could not read Streamlit secrets: {e}")

    # 2. Try environment variable
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            logger.info("Using DATABASE_URL from environment variable")

    # 3. Fall back to default (local development)
    if not database_url:
        database_url = "postgresql://ghg_user:ghg_password@localhost:5432/ghg_db"
        logger.warning("Using default DATABASE_URL (local development)")

    # Validate format
    if not database_url or not database_url.startswith('postgresql://'):
        error_msg = f"Invalid DATABASE_URL format. Got: {database_url[:30] if database_url else 'None'}..."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Remove any whitespace/newlines
    database_url = database_url.strip()

    return database_url

class Settings:
    """Application settings"""

    # Application
    APP_NAME: str = os.getenv("APP_NAME", "GHG Sustainability Reporting System")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database - Use function to get URL from multiple sources
    try:
        DATABASE_URL: str = get_database_url()
    except Exception as e:
        logger.critical(f"Failed to get DATABASE_URL: {e}")
        # Use a placeholder to prevent import errors
        DATABASE_URL: str = "postgresql://placeholder:placeholder@localhost:5432/placeholder"

    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@ghg-app.com")
    SMTP_USE_TLS: bool = True

    # File Storage
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: set = {".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png", ".doc", ".docx"}

    # Session
    SESSION_LIFETIME_HOURS: int = int(os.getenv("SESSION_LIFETIME_HOURS", "8"))

    # Pagination
    ECOINVENT_PAGE_SIZE: int = 50

    # Workflow States
    WORKFLOW_STATES = [
        "DRAFT",
        "SUBMITTED",
        "UNDER_CALCULATION",
        "PENDING_REVIEW",
        "REJECTED",
        "APPROVED",
        "LOCKED"
    ]

    # Roles
    ROLES = {
        "L1": "Data Entry Specialist",
        "L2": "Calculation Specialist",
        "L3": "QA Reviewer",
        "L4": "Approver/Manager"
    }

    # Email Templates
    EMAIL_TEMPLATES_DIR: Path = Path("./templates/emails")

    def __init__(self):
        # Ensure directories exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.EMAIL_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
