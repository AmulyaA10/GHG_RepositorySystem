"""
Configuration Management for GHG Sustainability Application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""

    # Application
    APP_NAME: str = os.getenv("APP_NAME", "GHG Sustainability Reporting System")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://ghg_user:ghg_password@localhost:5432/ghg_db"
    )

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
