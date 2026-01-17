#!/usr/bin/env python3
"""
Quick Deployment Checker
Verifies that your app is ready for Streamlit Cloud deployment
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "Required" if required else "Optional"
    print(f"{status} {filepath} - {req_text}")
    return exists

def check_database_connection():
    """Test database connection"""
    print("\n📊 Testing Database Connection...")

    try:
        from core.config import settings
        from sqlalchemy import create_engine

        # Get database URL
        db_url = settings.DATABASE_URL
        print(f"   Database: {db_url.split('@')[1] if '@' in db_url else 'Not configured'}")

        # Test connection
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        print("✅ Database connection successful!")

        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if len(tables) == 0:
            print("⚠️  No tables found. Run: alembic upgrade head")
            return False
        else:
            print(f"✅ Found {len(tables)} tables in database")

            # Check for users table
            if 'users' in tables:
                print("✅ Users table exists")
            else:
                print("❌ Users table missing. Run: alembic upgrade head")
                return False

        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 To fix:")
        print("   1. Set up a cloud PostgreSQL database (Neon, Supabase, etc.)")
        print("   2. Set DATABASE_URL in .streamlit/secrets.toml")
        print("   3. Run: alembic upgrade head")
        print("   4. Run: python scripts/seed_all.py")
        return False

def check_secrets():
    """Check if secrets are configured"""
    print("\n🔒 Checking Secrets Configuration...")

    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        print("✅ Local secrets file exists")

        # Read and check for required keys
        with open(secrets_file) as f:
            content = f.read()

        required_keys = ["DATABASE_URL", "SECRET_KEY"]
        for key in required_keys:
            if key in content:
                print(f"✅ {key} configured")
            else:
                print(f"⚠️  {key} not found in secrets.toml")

        return True
    else:
        print("⚠️  No local secrets file (OK for Streamlit Cloud)")
        print("   For Streamlit Cloud: Configure secrets in app settings")
        return False

def check_requirements():
    """Check requirements.txt"""
    print("\n📦 Checking Requirements...")

    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt missing!")
        return False

    with open(req_file) as f:
        requirements = f.read()

    critical_packages = [
        "streamlit",
        "sqlalchemy",
        "psycopg2-binary",
        "alembic",
        "bcrypt"
    ]

    all_found = True
    for package in critical_packages:
        if package in requirements:
            print(f"✅ {package}")
        else:
            print(f"❌ {package} missing!")
            all_found = False

    return all_found

def main():
    """Run all checks"""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║         🚀 GHG App - Deployment Readiness Check                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    print("\n📁 Checking Required Files...")
    files_ok = True
    files_ok &= check_file_exists("app.py", required=True)
    files_ok &= check_file_exists("requirements.txt", required=True)
    files_ok &= check_file_exists(".streamlit/config.toml", required=True)
    files_ok &= check_file_exists("alembic.ini", required=True)
    files_ok &= check_file_exists("core/config.py", required=True)

    requirements_ok = check_requirements()
    secrets_ok = check_secrets()
    db_ok = check_database_connection()

    print("\n" + "="*70)
    print("\n📋 Summary:")
    print(f"   Files: {'✅' if files_ok else '❌'}")
    print(f"   Requirements: {'✅' if requirements_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Secrets: {'✅' if secrets_ok else '⚠️  (Configure in Streamlit Cloud)'}")

    if files_ok and requirements_ok and db_ok:
        print("\n✅ Your app is ready for deployment!")
        print("\n🚀 Next steps:")
        print("   1. Push code to GitHub")
        print("   2. Go to https://share.streamlit.io")
        print("   3. Create new app and select your repository")
        print("   4. Configure secrets (DATABASE_URL, etc.)")
        print("   5. Deploy!")
    else:
        print("\n❌ Some issues need to be fixed before deployment.")
        print("   See DEPLOYMENT.md for detailed instructions")
        sys.exit(1)

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
