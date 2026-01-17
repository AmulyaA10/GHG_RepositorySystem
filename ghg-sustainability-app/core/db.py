"""
Database Session Management with Connection Pooling
Optimized for production use with high concurrency
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def validate_database_url(database_url: str) -> tuple[bool, str]:
    """
    Validate DATABASE_URL format before attempting connection

    Args:
        database_url: Database connection URL

    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    if not database_url:
        return False, "DATABASE_URL is empty"

    if not database_url.startswith('postgresql://'):
        return False, f"DATABASE_URL must start with 'postgresql://'. Got: {database_url[:30]}..."

    # Check for common issues
    if 'localhost' in database_url:
        logger.warning("⚠️ Using localhost database - this won't work on Streamlit Cloud!")
        logger.warning("   Get a cloud database from: https://neon.tech or https://supabase.com")

    # Parse URL components
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)

        if not parsed.hostname:
            return False, "DATABASE_URL missing hostname"

        if parsed.port and not isinstance(parsed.port, int):
            return False, f"DATABASE_URL has invalid port: {parsed.port}"

        return True, "DATABASE_URL format is valid"
    except Exception as e:
        return False, f"DATABASE_URL parsing error: {e}"

def test_database_connection(database_url: str) -> tuple[bool, str]:
    """
    Test database connection before creating the engine

    Args:
        database_url: Database connection URL

    Returns:
        tuple[bool, str]: (success, message)
    """
    # First validate format
    is_valid, val_message = validate_database_url(database_url)
    if not is_valid:
        return False, f"❌ Invalid DATABASE_URL: {val_message}"

    try:
        # Create a temporary engine just for testing
        test_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )

        # Try to connect
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        test_engine.dispose()
        return True, "✅ Database connection successful"
    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            return False, """❌ Cannot reach database server.

Common fixes:
1. Check DATABASE_URL in Streamlit Cloud secrets
2. Make sure database server is running
3. Verify network/firewall allows connections
4. Use a cloud database (not localhost)

Get free database at: https://neon.tech"""

        elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower():
            return False, """❌ Database authentication failed.

Check your DATABASE_URL:
1. Username is correct
2. Password is correct (no typos!)
3. User has proper permissions"""

        elif "does not exist" in error_msg.lower():
            return False, """❌ Database does not exist.

Run these commands:
1. alembic upgrade head
2. python scripts/seed_all.py"""

        else:
            return False, f"❌ Database connection error:\n{error_msg[:200]}"

# Test connection before creating engine
logger.info("="*70)
logger.info("🔍 Validating database configuration...")
logger.info(f"DATABASE_URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL[:40]}...")

db_ok, db_message = test_database_connection(settings.DATABASE_URL)

if not db_ok:
    logger.error(f"❌ Database connection test failed!")
    logger.error(db_message)
    logger.error("="*70)
    # Don't raise here - let Streamlit show a user-friendly error
else:
    logger.info(db_message)
    logger.info("="*70)

# Detect if using Neon (pooled connection)
is_neon = 'neon.tech' in settings.DATABASE_URL

# Create database engine with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pooling settings for production
    poolclass=QueuePool,           # Use QueuePool for connection reuse
    pool_size=10,                  # Maintain 10 connections in the pool
    max_overflow=20,               # Allow up to 20 additional connections under load
    pool_timeout=30,               # Wait max 30 seconds for a connection
    pool_recycle=3600,             # Recycle connections after 1 hour (prevents stale connections)
    pool_pre_ping=True,            # Verify connections before using them
    echo=settings.DEBUG,           # Log SQL queries in debug mode
    # Note: Neon pooled connections don't support statement_timeout in connect_args
    # If you need query timeouts with Neon, set them per-query instead
)

# Log connection pool status (useful for monitoring)
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections"""
    logger.debug(f"Database connection established. Pool status: {engine.pool.status()}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Monitor connection pool checkout"""
    pool = engine.pool
    logger.debug(f"Connection checked out. Pool: {pool.size()}/{pool_size}, Overflow: {pool.overflow()}/{max_overflow}")

# Store pool config for monitoring
pool_size = 10
max_overflow = 20

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency function to get database session

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        logger.info(f"Connection pool configured: size={pool_size}, max_overflow={max_overflow}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_pool_status():
    """
    Get current connection pool status for monitoring

    Returns:
        dict: Pool statistics
    """
    pool = engine.pool
    return {
        'pool_size': pool.size(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'queue_size': pool.size() - pool.checkedout(),
        'total_capacity': pool_size + max_overflow,
        'utilization_pct': round((pool.checkedout() / (pool_size + max_overflow)) * 100, 2)
    }
