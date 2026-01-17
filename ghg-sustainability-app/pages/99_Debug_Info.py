"""
Debug Information Page
Shows configuration and connection status - helpful for troubleshooting
"""
import streamlit as st
import sys
import os
from pathlib import Path

st.set_page_config(
    page_title="Debug Info",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Debug Information")
st.markdown("Use this page to troubleshoot deployment issues")

# Environment Info
st.header("📋 Environment")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Python")
    st.code(f"Version: {sys.version}")
    st.code(f"Path: {sys.executable}")

with col2:
    st.subheader("Working Directory")
    st.code(f"{os.getcwd()}")

# Streamlit Secrets
st.header("🔒 Streamlit Secrets")
try:
    if hasattr(st, 'secrets'):
        secrets_keys = list(st.secrets.keys())
        st.success(f"✅ Secrets available: {', '.join(secrets_keys)}")

        if 'DATABASE_URL' in st.secrets:
            db_url = st.secrets['DATABASE_URL']
            # Show partial URL (hide password)
            if '@' in db_url:
                parts = db_url.split('@')
                masked = f"{parts[0].split(':')[0]}:****@{parts[1]}"
                st.info(f"DATABASE_URL: `{masked}`")
            else:
                st.warning("DATABASE_URL format looks incorrect")
        else:
            st.error("❌ DATABASE_URL not found in secrets!")
    else:
        st.warning("⚠️ Streamlit secrets not available (local mode)")
except Exception as e:
    st.error(f"Error reading secrets: {e}")

# Configuration
st.header("⚙️ Configuration")
try:
    from core.config import settings

    config_items = {
        "APP_NAME": settings.APP_NAME,
        "DEBUG": settings.DEBUG,
        "DATABASE_URL": "***hidden***" if settings.DATABASE_URL else "Not set",
    }

    for key, value in config_items.items():
        st.text(f"{key}: {value}")

except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.code(str(e))

# Database Connection Test
st.header("🗄️ Database Connection")
try:
    from core.config import settings
    from sqlalchemy import create_engine, text

    db_url = settings.DATABASE_URL

    # Show database host (without password)
    if '@' in db_url:
        host_part = db_url.split('@')[1].split('/')[0]
        st.info(f"Connecting to: `{host_part}`")

    # Test connection
    with st.spinner("Testing database connection..."):
        engine = create_engine(db_url, pool_pre_ping=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()

            if row and row[0] == 1:
                st.success("✅ Database connection successful!")

                # Check for tables
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]

                if table_count > 0:
                    st.success(f"✅ Found {table_count} tables in database")

                    # Check for users table specifically
                    result = conn.execute(text("""
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'users'
                    """))
                    has_users = result.fetchone()[0] > 0

                    if has_users:
                        st.success("✅ Users table exists")

                        # Count users
                        result = conn.execute(text("SELECT COUNT(*) FROM users"))
                        user_count = result.fetchone()[0]
                        st.info(f"📊 {user_count} users in database")
                    else:
                        st.error("❌ Users table not found")
                        st.warning("Run: `alembic upgrade head`")
                else:
                    st.error("❌ No tables found in database")
                    st.warning("Run: `alembic upgrade head` then `python scripts/seed_all.py`")

        engine.dispose()

except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.info("Make sure all dependencies are installed")

except Exception as e:
    st.error(f"❌ Database connection failed!")
    st.code(str(e))

    st.markdown("---")
    st.subheader("💡 Common Fixes")

    st.markdown("""
    **For Streamlit Cloud:**
    1. Go to app Settings → Secrets
    2. Add your DATABASE_URL like this:
       ```toml
       DATABASE_URL = "postgresql://user:pass@host.neon.tech/dbname"
       ```
    3. Make sure it's a cloud database (not localhost)
    4. Reboot your app

    **Get a free cloud database:**
    - Neon: https://neon.tech (Recommended)
    - Supabase: https://supabase.com
    - ElephantSQL: https://elephantsql.com

    **After setting up database:**
    1. Run migrations: `alembic upgrade head`
    2. Seed data: `python scripts/seed_all.py`
    """)

# Installed Packages
st.header("📦 Key Packages")
try:
    import streamlit
    import sqlalchemy
    import psycopg2

    st.success(f"✅ streamlit: {streamlit.__version__}")
    st.success(f"✅ sqlalchemy: {sqlalchemy.__version__}")
    st.success(f"✅ psycopg2: {psycopg2.__version__}")

except ImportError as e:
    st.error(f"❌ Missing package: {e}")

st.markdown("---")
st.caption("This page is for debugging only. Remove or hide it in production.")
