import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator

from app.core.database import Base
from app.main import app
from app.core.security import create_access_token
from app.models.user import User

# Test database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/test_dinner_app"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db() -> Generator:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_user(db: TestingSessionLocal) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        # password = test123
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdCGfwX2UzyFg2.",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def test_user_token(test_user: User) -> str:
    return create_access_token({"sub": test_user.email})
