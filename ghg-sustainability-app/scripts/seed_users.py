"""
Seed Default Users
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db
from core.auth import hash_password
from models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_users():
    """Create default users for all 4 levels"""
    db = next(get_db())

    try:
        # Check if users already exist
        existing_count = db.query(User).count()

        if existing_count > 0:
            logger.info(f"Users already exist ({existing_count} found). Skipping...")
            return

        # Default users
        default_users = [
            {
                "username": "user_l1",
                "email": "l1@example.com",
                "password": "password123",
                "full_name": "Level 1 Data Entry User",
                "role": "L1"
            },
            {
                "username": "user_l2",
                "email": "l2@example.com",
                "password": "password123",
                "full_name": "Level 2 Calculation User",
                "role": "L2"
            },
            {
                "username": "user_l3",
                "email": "l3@example.com",
                "password": "password123",
                "full_name": "Level 3 Review User",
                "role": "L3"
            },
            {
                "username": "user_l4",
                "email": "l4@example.com",
                "password": "password123",
                "full_name": "Level 4 Approval User",
                "role": "L4"
            }
        ]

        # Create users
        for user_data in default_users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True
            )

            db.add(user)
            logger.info(f"Created user: {user_data['username']} ({user_data['role']})")

        db.commit()
        logger.info(f"✅ Successfully created {len(default_users)} users")

    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
