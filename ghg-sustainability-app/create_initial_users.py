#!/usr/bin/env python3
"""
Create Initial Users for Production Deployment
Run this ONCE after deploying to production
"""
from core.db import get_db
from models import User
from core.auth import hash_password
import sys

def create_users():
    """Create initial users for each role"""

    print("\n" + "="*80)
    print("🔐 CREATING INITIAL USERS FOR PRODUCTION")
    print("="*80 + "\n")

    print("⚠️  WARNING: You should change these passwords immediately after first login!\n")

    users_to_create = [
        {
            "username": "admin_l4",
            "email": "admin@yourcompany.com",
            "password": "Admin@2026!Change",  # CHANGE THIS!
            "full_name": "System Administrator",
            "role": "L4"
        },
        {
            "username": "reviewer_l3",
            "email": "reviewer@yourcompany.com",
            "password": "Reviewer@2026!Change",  # CHANGE THIS!
            "full_name": "QA Reviewer",
            "role": "L3"
        },
        {
            "username": "calculator_l2",
            "email": "calculator@yourcompany.com",
            "password": "Calculator@2026!Change",  # CHANGE THIS!
            "full_name": "Calculation Specialist",
            "role": "L2"
        },
        {
            "username": "dataentry_l1",
            "email": "dataentry@yourcompany.com",
            "password": "DataEntry@2026!Change",  # CHANGE THIS!
            "full_name": "Data Entry Specialist",
            "role": "L1"
        }
    ]

    db = next(get_db())
    created_count = 0
    skipped_count = 0

    try:
        for user_data in users_to_create:
            # Check if user already exists
            existing = db.query(User).filter(
                User.username == user_data["username"]
            ).first()

            if existing:
                print(f"⏭️  Skipped: {user_data['username']} (already exists)")
                skipped_count += 1
                continue

            # Create new user
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True
            )
            db.add(user)

            print(f"✅ Created: {user_data['username']} ({user_data['role']}) - {user_data['full_name']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Temp Password: {user_data['password']}")
            print()
            created_count += 1

        db.commit()

        print("="*80)
        print(f"✅ Successfully created {created_count} user(s)")
        if skipped_count > 0:
            print(f"⏭️  Skipped {skipped_count} existing user(s)")
        print("="*80 + "\n")

        print("🔑 NEXT STEPS:")
        print("1. Login to the app with each user")
        print("2. IMMEDIATELY change the default passwords")
        print("3. Update email addresses to real ones")
        print("4. Test each user role functionality\n")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {e}\n")
        return False

    finally:
        db.close()

def verify_database_connection():
    """Verify database connection before creating users"""
    try:
        db = next(get_db())
        # Try a simple query
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}\n")
        print("Please check:")
        print("1. DATABASE_URL is set correctly")
        print("2. Database is running and accessible")
        print("3. Database migrations have been run (alembic upgrade head)")
        return False

if __name__ == "__main__":
    print("\nVerifying database connection...")

    if not verify_database_connection():
        sys.exit(1)

    print("✅ Database connection successful\n")

    # Confirm before proceeding
    response = input("Create initial users? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        success = create_users()
        sys.exit(0 if success else 1)
    else:
        print("Cancelled.")
        sys.exit(0)
