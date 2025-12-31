"""
Master Seed Script - Run All Seeds
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from seed_users import seed_users
from seed_criteria import seed_criteria
from seed_reason_codes import seed_reason_codes
from seed_formulas import seed_formulas
from seed_ecoinvent import seed_ecoinvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_all():
    """Run all seed scripts in correct order"""
    logger.info("="*60)
    logger.info("Starting database seeding process...")
    logger.info("="*60)

    try:
        # 1. Seed users (no dependencies)
        logger.info("\n[1/5] Seeding users...")
        seed_users()

        # 2. Seed criteria (no dependencies)
        logger.info("\n[2/5] Seeding criteria...")
        seed_criteria()

        # 3. Seed reason codes (no dependencies)
        logger.info("\n[3/5] Seeding reason codes...")
        seed_reason_codes()

        # 4. Seed formulas (no dependencies)
        logger.info("\n[4/5] Seeding formulas...")
        seed_formulas()

        # 5. Seed ecoinvent (no dependencies)
        logger.info("\n[5/5] Seeding ecoinvent emission factors...")
        seed_ecoinvent()

        logger.info("\n" + "="*60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("="*60)
        logger.info("\nDefault credentials:")
        logger.info("  L1 User: user_l1 / password123")
        logger.info("  L2 User: user_l2 / password123")
        logger.info("  L3 User: user_l3 / password123")
        logger.info("  L4 User: user_l4 / password123")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {e}")
        raise

if __name__ == "__main__":
    seed_all()
