import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from httpx import AsyncClient

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
    """Create a fresh database session for each test"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with a test database session"""

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> Dict[str, str]:
    """Create a test user and return credentials"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"user_id": user.id, "token": token}


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
    """Create authenticated user with emotional profile"""
    user = UserFactory(
        email="souluser@test.com",
        username="souluser",
        emotional_onboarding_completed=True,
        emotional_depth_score=8.5
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    profile = ProfileFactory(
        user_id=user.id,
        life_philosophy="Connection before appearance, soul before skin",
        core_values={
            "relationship_values": ["commitment", "growth", "authenticity"],
            "life_priorities": ["love", "personal_growth", "meaningful_connections"]
        }
    )
    db_session.add(profile)
    db_session.commit()
    
    token = create_access_token({"sub": user.email})
    
    return {
        "user": user,
        "profile": profile,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def matching_users(db_session) -> Dict[str, Any]:
    """Create two users ready for soul connection matching"""
    user1 = UserFactory(
        email="match1@test.com",
        emotional_onboarding_completed=True,
        emotional_depth_score=7.5
    )
    user2 = UserFactory(
        email="match2@test.com", 
        emotional_onboarding_completed=True,
        emotional_depth_score=8.0
    )
    
    profile1 = ProfileFactory(
        user_id=user1.id,
        interests=["cooking", "reading", "hiking", "photography"],
        core_values={
            "relationship_values": ["commitment", "growth"],
            "life_priorities": ["family", "career", "travel"]
        }
    )
    
    profile2 = ProfileFactory(
        user_id=user2.id,
        interests=["cooking", "music", "hiking", "art"],  # 50% overlap
        core_values={
            "relationship_values": ["commitment", "adventure"],  # 50% overlap
            "life_priorities": ["family", "creativity", "travel"]  # 66% overlap
        }
    )
    
    for entity in [user1, user2, profile1, profile2]:
        db_session.add(entity)
    db_session.commit()
    
    return {
        "user1": user1,
        "user2": user2,
        "profile1": profile1,
        "profile2": profile2
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
