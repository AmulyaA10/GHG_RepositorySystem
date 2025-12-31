"""
Seed Reason Codes for Reviews
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db
from models import ReasonCode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_reason_codes():
    """Create standard reason codes for review rejections"""
    db = next(get_db())

    try:
        # Check if reason codes already exist
        existing_count = db.query(ReasonCode).count()

        if existing_count > 0:
            logger.info(f"Reason codes already exist ({existing_count} found). Skipping...")
            return

        # Standard reason codes
        reason_codes_data = [
            {
                "code": "DQ001",
                "description": "Incomplete or missing activity data",
                "category": "Data Quality"
            },
            {
                "code": "DQ002",
                "description": "Data values appear incorrect or unrealistic",
                "category": "Data Quality"
            },
            {
                "code": "DQ003",
                "description": "Units not specified or incorrect",
                "category": "Data Quality"
            },
            {
                "code": "EV001",
                "description": "Supporting evidence missing or insufficient",
                "category": "Evidence"
            },
            {
                "code": "EV002",
                "description": "Evidence does not match reported data",
                "category": "Evidence"
            },
            {
                "code": "CALC001",
                "description": "Emission factor selection inappropriate",
                "category": "Calculation Error"
            },
            {
                "code": "CALC002",
                "description": "Calculation methodology incorrect",
                "category": "Calculation Error"
            },
            {
                "code": "CALC003",
                "description": "Unit conversion error detected",
                "category": "Calculation Error"
            },
            {
                "code": "SCOPE001",
                "description": "Activity categorized under wrong scope",
                "category": "Scope Classification"
            },
            {
                "code": "OTHER",
                "description": "Other issues - see comments",
                "category": "Other"
            }
        ]

        # Create reason codes
        for rc_data in reason_codes_data:
            reason_code = ReasonCode(
                code=rc_data["code"],
                description=rc_data["description"],
                category=rc_data["category"],
                is_active=True
            )

            db.add(reason_code)
            logger.info(f"Created reason code: {rc_data['code']} - {rc_data['description']}")

        db.commit()
        logger.info(f"✅ Successfully created {len(reason_codes_data)} reason codes")

    except Exception as e:
        logger.error(f"Error seeding reason codes: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_reason_codes()
