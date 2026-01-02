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
