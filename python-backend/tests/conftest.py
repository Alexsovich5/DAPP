import pytest
import asyncio
import os
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from httpx import AsyncClient

# Set test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/test_dinner_app"

from app.core.database import Base, get_db
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus

# Import test factories
from tests.factories import (
    UserFactory, ProfileFactory, SoulConnectionFactory, 
    DailyRevelationFactory, MessageFactory, PhotoRevealFactory,
    setup_factories, create_complete_soul_connection
)

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres@localhost/test_dinner_app"

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)

# Create test SessionLocal class
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables"""
    if database_exists(TEST_DATABASE_URL):
        drop_database(TEST_DATABASE_URL)

    create_database(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    drop_database(TEST_DATABASE_URL)


@pytest.fixture
def db_session(test_db):
    """Create a database session that commits data so authentication can see it"""
    session = TestSessionLocal()
    
    # Setup factories with this session
    setup_factories(session)

    yield session

    # Clean up by deleting test data (committed, so auth can see it during test)
    try:
        from sqlalchemy import text
        # Delete test user and related data
        session.execute(text("DELETE FROM profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test.com')"))
        session.execute(text("DELETE FROM users WHERE email LIKE '%test.com'"))
        session.commit()
        session.close()
    except Exception as e:
        print(f"Cleanup error: {e}")
        try:
            session.rollback()
            session.close()
        except:
            pass


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client that uses test database"""
    
    def override_get_db():
        """Override database dependency to use test database engine"""
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    # Override the database dependency to use test database
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> Dict[str, str]:
    """Create a test user and return credentials"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        emotional_onboarding_completed=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {
        "user_id": user.id, 
        "token": token, 
        "email": user.email,
        "password": "testpassword"  # Store the original password for tests
    }


@pytest.fixture
def test_profile(db_session, test_user) -> Profile:
    """Create a test profile"""
    profile = Profile(
        user_id=test_user["user_id"],
        full_name="Test User",
        bio="Test bio",
        cuisine_preferences="Italian, Japanese",
        dietary_restrictions="None",
        location="New York",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def test_match(db_session, test_user) -> Match:
    """Create a test match"""
    recipient = User(
        email="recipient@example.com",
        username="recipient",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(recipient)
    db_session.commit()

    match = Match(
        sender_id=test_user["user_id"],
        receiver_id=recipient.id,
        status=MatchStatus.PENDING,
        restaurant_preference="Italian",
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Return authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {test_user['token']}"}


# New fixtures for Sprint 2 comprehensive testing

@pytest.fixture
def factories(db_session):
    """Setup test data factories with database session"""
    setup_factories(db_session)
    return {
        'user': UserFactory,
        'profile': ProfileFactory,
        'soul_connection': SoulConnectionFactory,
        'revelation': DailyRevelationFactory,
        'message': MessageFactory,
        'photo_reveal': PhotoRevealFactory,
    }


@pytest.fixture
def soul_connection_data(db_session):
    """Create complete soul connection test data"""
    return create_complete_soul_connection(db_session)


@pytest.fixture
def authenticated_user(db_session) -> Dict[str, Any]:
    """CREATE → TEST → DELETE: Create real authenticated user for testing"""
    # CREATE: Create real user that authentication system can find
    user = User(
        email="souluser@test.com",
        username="souluser",
        hashed_password=get_password_hash("testpass123"),
        first_name="Soul",
        last_name="User",
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=8.5
    )
    
    # Commit user to database so authentication can find it
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create profile for complete user setup
    profile = Profile(
        user_id=user.id,
        full_name="Soul User",
        bio="Connection before appearance, soul before skin",
        location="Test City, TC",
        cuisine_preferences="All cuisines"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    
    # Generate real JWT token for actual authentication
    token = create_access_token({"sub": user.email, "user_id": user.id})
    
    # Return everything needed for testing
    return {
        "user": user,
        "profile": profile,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }
    # DELETE: Cleanup handled by db_session fixture


@pytest.fixture
def matching_users(db_session) -> Dict[str, Any]:
    """Create two users ready for soul connection matching"""
    from datetime import date
    
    user1 = User(
        email="match1@test.com",
        username="match1",
        hashed_password=get_password_hash("testpass123"),
        first_name="Match",
        last_name="One",
        date_of_birth=date(1990, 5, 15),
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=7.5
    )
    user2 = User(
        email="match2@test.com",
        username="match2", 
        hashed_password=get_password_hash("testpass123"),
        first_name="Match",
        last_name="Two",
        date_of_birth=date(1992, 8, 20),
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=8.0
    )
    
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    return {
        "user1": user1,
        "user2": user2
    }


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTP client for testing async endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def performance_config():
    """Configuration for performance testing"""
    return {
        "matching_algorithm_max_time": 0.5,  # 500ms max
        "database_query_max_time": 0.1,      # 100ms max
        "api_response_max_time": 2.0,        # 2s max
        "concurrent_users": 50                # Load testing
    }
