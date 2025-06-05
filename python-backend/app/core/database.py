from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/dinner_app"
)

# Create engine with proper connection pool and timeout configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Connection pool settings
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Additional connections beyond pool_size
    pool_timeout=30,  # Seconds to wait for connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
    # Connection timeout settings for psycopg2
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "dinner_app",  # Application name for monitoring
    },
    # Echo SQL queries for debugging (can be disabled in production)
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    """Function to create all database tables"""
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import User, Profile, Match  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
