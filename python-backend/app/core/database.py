from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/dinner_app"
)

# Environment-based pool configuration
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# Enhanced connection pool configuration
POOL_CONFIG = {
    "development": {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
    },
    "production": {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_timeout": 60,
        "pool_recycle": 7200,  # 2 hours for production
    }
}

config = POOL_CONFIG["production" if IS_PRODUCTION else "development"]

# Create engine with enhanced connection pool and monitoring
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Enhanced connection pool settings
    poolclass=QueuePool,
    pool_size=config["pool_size"],
    max_overflow=config["max_overflow"],
    pool_timeout=config["pool_timeout"],
    pool_recycle=config["pool_recycle"],
    pool_pre_ping=True,  # Verify connections before use
    pool_reset_on_return="commit",  # Reset connections on return
    
    # Enhanced connection settings for PostgreSQL
    connect_args={
        "connect_timeout": 10,
        "application_name": "dinner_first_soul_app",
        "options": "-c default_transaction_isolation=read committed"
    },
    
    # Performance optimizations
    echo=False,  # Disable in production
    echo_pool=not IS_PRODUCTION,  # Pool debugging in dev only
    
    # Query optimization settings
    execution_options={
        "isolation_level": "READ_COMMITTED",
        "autocommit": False,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Connection pool event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set connection-level optimizations"""
    if "postgresql" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_connection.cursor()
        # Set PostgreSQL-specific optimizations
        cursor.execute("SET statement_timeout = '30s'")
        cursor.execute("SET lock_timeout = '10s'")
        cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
        cursor.close()
        logger.debug("Applied PostgreSQL connection optimizations")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection pool checkout"""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection pool checkin"""
    logger.debug("Connection returned to pool")


def create_tables():
    """Function to create all database tables"""
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import User, Profile, Match, SoulConnection, DailyRevelation, Message  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency for FastAPI endpoints with enhanced error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_connection_pool_status():
    """Get current connection pool status for monitoring"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out_connections": pool.checkedout(),
        "overflow_connections": pool.overflow(),
        "invalid_connections": pool.invalidated(),
        "checked_in_connections": pool.checkedin(),
        "total_connections": pool.size() + pool.overflow(),
        "pool_timeout": config["pool_timeout"],
        "max_overflow": config["max_overflow"],
        "is_healthy": pool.checkedout() < (pool.size() + pool.overflow()) * 0.8
    }


def check_database_health():
    """Perform database health check"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        result = db.execute("SELECT 1").scalar()
        db.close()
        
        pool_status = get_connection_pool_status()
        
        return {
            "database_accessible": result == 1,
            "pool_status": pool_status,
            "health_score": 100 if result == 1 and pool_status["is_healthy"] else 50,
            "timestamp": logger.handlers[0].formatter.formatTime(None) if logger.handlers else "unknown"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "database_accessible": False,
            "error": str(e),
            "health_score": 0,
            "timestamp": logger.handlers[0].formatter.formatTime(None) if logger.handlers else "unknown"
        }


def optimize_query_performance():
    """Apply database-level optimizations"""
    try:
        db = SessionLocal()
        
        # PostgreSQL-specific optimizations
        if "postgresql" in SQLALCHEMY_DATABASE_URL:
            # Update table statistics for query planner
            db.execute("ANALYZE")
            
            # Set session-level optimizations
            db.execute("SET work_mem = '64MB'")
            db.execute("SET effective_cache_size = '1GB'")
            db.execute("SET random_page_cost = 1.1")
            
            logger.info("Applied PostgreSQL query optimizations")
        
        db.close()
        return {"optimizations_applied": True}
        
    except Exception as e:
        logger.error(f"Failed to apply query optimizations: {str(e)}")
        return {"optimizations_applied": False, "error": str(e)}
