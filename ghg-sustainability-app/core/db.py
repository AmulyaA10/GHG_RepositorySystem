"""
Database Session Management with Connection Pooling
Optimized for production use with high concurrency
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def test_database_connection(database_url: str) -> tuple[bool, str]:
    """
    Test database connection before creating the engine

    Args:
        database_url: Database connection URL

    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        # Create a temporary engine just for testing
        test_engine = create_engine(database_url, pool_pre_ping=True)

        # Try to connect
        with test_engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.close()

        test_engine.dispose()
        return True, "Database connection successful"
    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            return False, "Cannot reach database server. Please check:\n1. DATABASE_URL is correct\n2. Database server is running\n3. Network/firewall allows connections"
        elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower():
            return False, "Database authentication failed. Please check:\n1. Username is correct\n2. Password is correct\n3. User has proper permissions"
        elif "does not exist" in error_msg.lower():
            return False, "Database does not exist. Please:\n1. Create the database first\n2. Run migrations: alembic upgrade head"
        else:
            return False, f"Database connection error: {error_msg}"

# Test connection before creating engine
logger.info("Testing database connection...")
db_ok, db_message = test_database_connection(settings.DATABASE_URL)

if not db_ok:
    logger.error(f"Database connection test failed: {db_message}")
    logger.error(f"DATABASE_URL format: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'invalid'}")
    # Don't raise here - let Streamlit show a better error message
    # raise ConnectionError(db_message)
else:
    logger.info(db_message)

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
    # Additional performance settings
    connect_args={
        "options": "-c statement_timeout=60000"  # 60 second query timeout
    }
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
