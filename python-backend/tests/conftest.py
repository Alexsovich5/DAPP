import os
import random
import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from httpx import AsyncClient
from faker import Faker

from app.core.database import Base, get_db
from app.main import app
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus
from app.models.soul_connection import SoulConnection

# Import test factories
from tests.factories import (
    UserFactory, ProfileFactory, SoulConnectionFactory, 
    DailyRevelationFactory, MessageFactory, UserPhotoFactory,
    setup_factories, create_complete_soul_connection
)

# Seed randomness for deterministic tests
random.seed(1)
Faker.seed(1)

# Test database URL (use file-based SQLite for better test isolation)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_database.db")

# Create test database engine with proper settings for testing
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {},
    poolclass=None if TEST_DATABASE_URL.startswith("sqlite") else None,
)

# Create test SessionLocal class
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables with safe drop/create behavior"""
    is_sqlite = TEST_DATABASE_URL.startswith("sqlite")
    
    # For SQLite file-based testing, remove existing database
    if is_sqlite and "test_database.db" in TEST_DATABASE_URL:
        import os
        if os.path.exists("./test_database.db"):
            os.remove("./test_database.db")
    
    # For non-SQLite databases
    allow_drop = os.getenv("ALLOW_DB_DROP") == "1"
    if not is_sqlite and allow_drop:
        if database_exists(TEST_DATABASE_URL):
            drop_database(TEST_DATABASE_URL)
        create_database(TEST_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine

    # Cleanup
    if not is_sqlite and allow_drop:
        drop_database(TEST_DATABASE_URL)
    elif is_sqlite and "test_database.db" in TEST_DATABASE_URL:
        import os
        if os.path.exists("./test_database.db"):
            os.remove("./test_database.db")


@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    session = TestSessionLocal()
    
    yield session
    
    # Clean up after each test by removing all data
    session.close()
    # Truncate all tables to ensure clean state for next test
    with test_db.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with a test database session"""

    def override_get_db():
        """Return the same session instance used by the test"""
        return db_session

    # Set dependency override on main app
    app.dependency_overrides[get_db] = override_get_db
    
    # CRITICAL FIX: Also set dependency override on mounted sub-apps
    # The main app mounts v1_app at /api/v1 and /api, so we need to override both
    from starlette.routing import Mount
    for route in app.routes:
        if isinstance(route, Mount) and hasattr(route.app, 'dependency_overrides'):
            route.app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides from both main app and sub-apps
    app.dependency_overrides.clear()
    for route in app.routes:
        if isinstance(route, Mount) and hasattr(route.app, 'dependency_overrides'):
            route.app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> Dict[str, str]:
    """Create a test user and return credentials"""
    # Ensure we're in testing mode for password hashing
    import os
    import uuid
    os.environ["TESTING"] = "1"
    
    # Generate unique identifiers to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    email = f"test{unique_id}@example.com"
    username = f"testuser{unique_id}"
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Verify the password hash was created correctly
    assert verify_password("testpassword", user.hashed_password), "Password hash verification failed in fixture"

    token = create_access_token({"sub": user.email})
    return {
        "user_id": user.id, 
        "email": user.email,
        "username": user.username,
        "password": "testpassword",  # Plain text password for testing
        "token": token,
        "access_token": token  # Add both for compatibility
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
        'photo_reveal': UserPhotoFactory,
    }


@pytest.fixture
def soul_connection_data(db_session):
    """Create complete soul connection test data"""
    return create_complete_soul_connection(db_session)


@pytest.fixture
def authenticated_user(db_session) -> Dict[str, Any]:
    """Create authenticated user with emotional profile"""
    # Setup factories to use the test session
    from tests.factories import setup_factories
    setup_factories(db_session)
    
    user = UserFactory(
        email="souluser@test.com",
        username="souluser",
        emotional_onboarding_completed=True,
        emotional_depth_score=8.5
    )
    # No need to add/commit - factory handles this
    
    profile = ProfileFactory(
        user_id=user.id,
        # Remove non-existent Profile fields
        bio="Connection before appearance, soul before skin",
        location="Test City"
    )
    # No need to add/commit - factory handles this
    
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
    # Setup factories to use the test session
    from tests.factories import setup_factories
    setup_factories(db_session)
    
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
        bio="Love cooking and outdoor adventures",
        cuisine_preferences="Italian, Asian"
    )
    
    profile2 = ProfileFactory(
        user_id=user2.id,
        bio="Music lover and art enthusiast",
        cuisine_preferences="Italian, Mediterranean"
    )
    
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


@pytest.fixture
def realtime_service(db_session):
    """Mock realtime service for WebSocket testing"""
    from unittest.mock import MagicMock, AsyncMock
    
    class MockRealtimeService:
        def __init__(self):
            self.connection_manager = MagicMock()
            self.typing_sessions = {}
            self.presence_privacy = {}
        
        def send_message_to_connection(self, message):
            """Mock message sending"""
            return True
        
        def send_and_save_message(self, message_data):
            """Mock message saving and sending"""
            from unittest.mock import MagicMock
            mock_message = MagicMock()
            mock_message.connection_id = message_data["connection_id"]
            mock_message.sender_id = message_data["sender_id"]
            mock_message.message_text = message_data["content"]
            return mock_message
        
        def format_message_for_realtime(self, msg_data):
            """Mock message formatting"""
            return {
                "type": msg_data["type"],
                "content": msg_data["content"],
                "timestamp": "2024-01-01T00:00:00Z",
                "message_type": msg_data["type"]
            }
        
        def start_typing_indicator(self, connection_id, user_id):
            """Mock typing indicator start"""
            if connection_id not in self.typing_sessions:
                self.typing_sessions[connection_id] = set()
            self.typing_sessions[connection_id].add(user_id)
        
        def stop_typing_indicator(self, connection_id, user_id):
            """Mock typing indicator stop"""
            if connection_id in self.typing_sessions:
                self.typing_sessions[connection_id].discard(user_id)
        
        def is_user_typing(self, connection_id, user_id):
            """Mock typing status check"""
            return user_id in self.typing_sessions.get(connection_id, set())
        
        def get_typing_users(self, connection_id):
            """Mock get typing users"""
            return list(self.typing_sessions.get(connection_id, set()))
        
        def notify_presence_change(self, user_id, status):
            """Mock presence change notification"""
            pass
        
        def set_presence_privacy(self, user_id, privacy_level):
            """Mock presence privacy setting"""
            self.presence_privacy[user_id] = privacy_level
        
        def is_user_visible_online(self, user_id, viewer_id):
            """Mock presence visibility check"""
            privacy = self.presence_privacy.get(user_id, "public")
            return privacy == "public"
        
        def send_connection_notification(self, user_id, notification_data):
            """Mock connection notification"""
            pass
        
        def notify_revelation_shared(self, connection_id, sender_id, revelation_data):
            """Mock revelation notification"""
            pass
        
        def notify_photo_consent(self, connection_id, sender_id, consent_data):
            """Mock photo consent notification"""
            pass
        
        def send_notification_with_queue(self, user_id, notification):
            """Mock notification with queuing"""
            return {
                "queued": True,
                "delivery_status": "pending"
            }
        
        def get_queued_notifications(self, user_id):
            """Mock queued notifications retrieval"""
            return [{"type": "test_notification", "message": "Test notification for offline user"}]
        
        def validate_incoming_message(self, message):
            """Mock message validation"""
            if not message or not message.get("type"):
                return False
            if message.get("type") == "unknown_type":
                return False
            if message.get("type") == "message" and not message.get("content"):
                return False
            if len(message.get("content", "")) > 1000:
                return False
            return True
        
        def is_message_authorized(self, message):
            """Mock message authorization"""
            # Simulate authorization check
            connection_id = message.get("connection_id")
            return connection_id != 999  # 999 is unauthorized in tests
    
    return MockRealtimeService()
