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


# === SERVICE FIXTURES FOR COMPREHENSIVE TESTING ===

@pytest.fixture
def soul_compatibility_service(db_session):
    """Soul compatibility calculation service fixture"""
    from app.services.soul_compatibility_service import CompatibilityCalculator
    return CompatibilityCalculator()


@pytest.fixture  
def revelation_service(db_session):
    """Revelation service fixture with database session"""
    from app.services.revelation_service import RevelationService
    return RevelationService(db_session)


@pytest.fixture
def message_service(db_session):
    """Message service fixture"""
    from app.services.message_service import MessageService
    return MessageService(db_session)


@pytest.fixture
def ab_testing_service(db_session):
    """A/B testing service fixture"""
    from app.services.ab_testing import ABTestingService
    import fakeredis
    fake_redis = fakeredis.FakeRedis()
    return ABTestingService(None, fake_redis)  # None for ClickHouse (not used in tests)


@pytest.fixture
def ai_matching_service(db_session):
    """AI matching service fixture"""
    from app.services.ai_matching_service import AIMatchingService
    return AIMatchingService()


@pytest.fixture
def analytics_service(db_session):
    """Analytics service fixture"""
    from app.services.analytics_service import AnalyticsService
    return AnalyticsService(db_session)


@pytest.fixture
def push_notification_service():
    """Push notification service fixture"""
    from app.services.push_notification import PushNotificationService
    return PushNotificationService()


@pytest.fixture
def photo_reveal_service(db_session):
    """Photo reveal service fixture"""
    from app.services.photo_reveal_service import PhotoRevealService
    return PhotoRevealService(db_session)


# === ASYNC TESTING INFRASTRUCTURE ===

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_db_session(test_db):
    """Async database session for async tests"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Convert SQLite URL to async format for testing
    if TEST_DATABASE_URL.startswith("sqlite"):
        async_url = TEST_DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    else:
        async_url = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    async_engine = create_async_engine(async_url, echo=False)
    AsyncSessionLocal = sessionmaker(
        bind=async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()
    
    await async_engine.dispose()


@pytest.fixture
async def async_client_with_db(async_db_session):
    """Async test client with async database session"""
    from httpx import AsyncClient
    
    async def override_get_db():
        """Return the same async session instance used by the test"""
        return async_db_session
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def websocket_test_client():
    """WebSocket test client for async WebSocket testing"""
    from fastapi.testclient import TestClient
    from unittest.mock import AsyncMock, MagicMock
    
    class MockWebSocketTestClient:
        def __init__(self):
            self.websocket = AsyncMock()
            self.messages_sent = []
            self.messages_received = []
            self.connection_id = None
            self.user_id = None
            self.connected = False
        
        async def connect(self, url: str, headers: dict = None):
            """Mock WebSocket connection"""
            self.connected = True
            self.connection_id = "test_connection_123"
            self.user_id = headers.get("user_id", 1) if headers else 1
            return True
        
        async def send_text(self, message: str):
            """Mock sending text message"""
            if not self.connected:
                raise Exception("WebSocket not connected")
            self.messages_sent.append({"type": "text", "data": message})
        
        async def send_json(self, data: dict):
            """Mock sending JSON message"""
            if not self.connected:
                raise Exception("WebSocket not connected")
            self.messages_sent.append({"type": "json", "data": data})
        
        async def receive_text(self):
            """Mock receiving text message"""
            if self.messages_received:
                return self.messages_received.pop(0)
            return "Mock message response"
        
        async def receive_json(self):
            """Mock receiving JSON message"""
            return {"type": "response", "content": "Mock JSON response"}
        
        async def disconnect(self):
            """Mock WebSocket disconnection"""
            self.connected = False
            self.connection_id = None
        
        def simulate_incoming_message(self, message):
            """Simulate incoming message for testing"""
            self.messages_received.append(message)
    
    return MockWebSocketTestClient()


@pytest.fixture
async def mock_redis_async():
    """Async mock Redis for testing async operations"""
    import fakeredis.aioredis
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
async def async_realtime_service(async_db_session, mock_redis_async):
    """Async realtime service fixture for WebSocket testing"""
    from unittest.mock import AsyncMock, MagicMock
    
    class MockAsyncRealtimeService:
        def __init__(self):
            self.connection_manager = AsyncMock()
            self.redis = mock_redis_async
            self.active_connections = {}
            self.typing_sessions = {}
            self.presence_privacy = {}
        
        async def send_message_to_connection(self, connection_id: int, message: dict):
            """Mock async message sending"""
            return {"status": "sent", "connection_id": connection_id, "message": message}
        
        async def send_and_save_message(self, message_data: dict):
            """Mock async message saving and sending"""
            mock_message = MagicMock()
            mock_message.id = 123
            mock_message.connection_id = message_data.get("connection_id")
            mock_message.sender_id = message_data.get("sender_id")
            mock_message.message_text = message_data.get("content")
            mock_message.created_at = datetime.utcnow()
            return mock_message
        
        async def broadcast_to_connection(self, connection_id: int, data: dict):
            """Mock broadcasting to connection"""
            return {"broadcasted": True, "connection_id": connection_id, "data": data}
        
        async def start_typing_indicator(self, connection_id: int, user_id: int):
            """Mock async typing indicator start"""
            if connection_id not in self.typing_sessions:
                self.typing_sessions[connection_id] = set()
            self.typing_sessions[connection_id].add(user_id)
            return True
        
        async def stop_typing_indicator(self, connection_id: int, user_id: int):
            """Mock async typing indicator stop"""
            if connection_id in self.typing_sessions:
                self.typing_sessions[connection_id].discard(user_id)
            return True
        
        async def notify_presence_change(self, user_id: int, status: str):
            """Mock async presence change notification"""
            return {"user_id": user_id, "status": status, "notified": True}
        
        async def send_connection_notification(self, user_id: int, notification_data: dict):
            """Mock async connection notification"""
            return {"queued": True, "user_id": user_id, "notification": notification_data}
        
        async def notify_revelation_shared(self, connection_id: int, sender_id: int, revelation_data: dict):
            """Mock async revelation notification"""
            return {"sent": True, "connection_id": connection_id, "revelation": revelation_data}
        
        async def validate_websocket_auth(self, token: str):
            """Mock WebSocket authentication validation"""
            if token == "invalid_token":
                return None
            return {"user_id": 1, "email": "test@example.com"}
        
        async def handle_websocket_error(self, connection_id: int, error: Exception):
            """Mock WebSocket error handling"""
            return {"error_handled": True, "connection_id": connection_id, "error": str(error)}
    
    return MockAsyncRealtimeService()


@pytest.fixture
async def async_ai_service():
    """Async AI service fixture for testing AI-powered features"""
    from unittest.mock import AsyncMock, MagicMock
    
    class MockAsyncAIService:
        def __init__(self):
            self.model_name = "mock-ai-model"
            self.api_calls = []
        
        async def generate_compatibility_insights(self, user1_data: dict, user2_data: dict):
            """Mock async compatibility insights generation"""
            self.api_calls.append("generate_compatibility_insights")
            return {
                "insights": ["Strong emotional connection potential", "Shared values in growth and adventure"],
                "confidence": 0.85,
                "processing_time": 0.1
            }
        
        async def analyze_revelation_sentiment(self, revelation_text: str):
            """Mock async revelation sentiment analysis"""
            self.api_calls.append("analyze_revelation_sentiment")
            return {
                "sentiment": "positive",
                "emotional_depth": 0.8,
                "authenticity_score": 0.9,
                "keywords": ["growth", "connection", "authentic"]
            }
        
        async def suggest_conversation_starters(self, user1_profile: dict, user2_profile: dict):
            """Mock async conversation starter suggestions"""
            self.api_calls.append("suggest_conversation_starters")
            return {
                "suggestions": [
                    "What's been the most meaningful experience in your personal growth journey?",
                    "If you could share one value that guides your relationships, what would it be?"
                ],
                "confidence": 0.75
            }
        
        async def detect_inappropriate_content(self, content: str):
            """Mock async content moderation"""
            self.api_calls.append("detect_inappropriate_content")
            if "inappropriate" in content.lower():
                return {"flagged": True, "reason": "inappropriate_content", "confidence": 0.95}
            return {"flagged": False, "confidence": 0.98}
        
        async def process_batch_compatibility(self, user_pairs: list):
            """Mock async batch compatibility processing"""
            self.api_calls.append("process_batch_compatibility")
            results = []
            for pair in user_pairs:
                results.append({
                    "user1_id": pair[0],
                    "user2_id": pair[1],
                    "compatibility_score": 75.5,
                    "processing_time": 0.05
                })
            return results
    
    return MockAsyncAIService()


@pytest.fixture
async def async_performance_monitor():
    """Async performance monitoring fixture for load testing"""
    import time
    import asyncio
    from collections import defaultdict
    
    class AsyncPerformanceMonitor:
        def __init__(self):
            self.metrics = defaultdict(list)
            self.start_times = {}
        
        async def start_timer(self, operation: str):
            """Start timing an async operation"""
            self.start_times[operation] = time.time()
        
        async def end_timer(self, operation: str):
            """End timing and record duration"""
            if operation in self.start_times:
                duration = time.time() - self.start_times[operation]
                self.metrics[operation].append(duration)
                del self.start_times[operation]
                return duration
            return 0.0
        
        async def measure_async_operation(self, coro, operation_name: str):
            """Measure the execution time of an async operation"""
            start_time = time.time()
            result = await coro
            duration = time.time() - start_time
            self.metrics[operation_name].append(duration)
            return result, duration
        
        async def get_metrics_summary(self):
            """Get summary of recorded metrics"""
            summary = {}
            for operation, durations in self.metrics.items():
                if durations:
                    summary[operation] = {
                        "count": len(durations),
                        "avg": sum(durations) / len(durations),
                        "min": min(durations),
                        "max": max(durations),
                        "total": sum(durations)
                    }
            return summary
        
        async def simulate_concurrent_load(self, async_func, concurrent_users: int = 10, iterations: int = 5):
            """Simulate concurrent load for performance testing"""
            tasks = []
            for i in range(concurrent_users):
                for j in range(iterations):
                    tasks.append(async_func())
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            return {
                "total_operations": len(tasks),
                "successful": successful,
                "failed": failed,
                "total_time": total_time,
                "operations_per_second": len(tasks) / total_time if total_time > 0 else 0,
                "avg_time_per_operation": total_time / len(tasks) if tasks else 0
            }
    
    return AsyncPerformanceMonitor()


@pytest.fixture
async def async_test_data_generator(async_db_session):
    """Async test data generator for performance testing"""
    from tests.factories import setup_factories, UserFactory, ProfileFactory, SoulConnectionFactory
    
    class AsyncTestDataGenerator:
        def __init__(self, session):
            self.session = session
            setup_factories(session)
        
        async def create_users_batch(self, count: int = 10):
            """Create a batch of users asynchronously"""
            users = []
            for i in range(count):
                user = UserFactory(email=f"batch_user_{i}@test.com")
                users.append(user)
                # Simulate async processing delay
                if i % 5 == 0:
                    await asyncio.sleep(0.001)  # Small delay every 5 users
            return users
        
        async def create_connections_batch(self, users: list, count: int = 5):
            """Create soul connections between users asynchronously"""
            connections = []
            for i in range(min(count, len(users) // 2)):
                connection = SoulConnectionFactory(
                    user1_id=users[i * 2].id,
                    user2_id=users[i * 2 + 1].id
                )
                connections.append(connection)
                await asyncio.sleep(0.001)  # Simulate async processing
            return connections
        
        async def cleanup_test_data(self, user_ids: list = None):
            """Clean up test data asynchronously"""
            # This would contain actual cleanup logic
            await asyncio.sleep(0.01)  # Simulate cleanup time
            return True
    
    return AsyncTestDataGenerator(async_db_session)


# === ADVANCED TEST DATA SCENARIOS ===

@pytest.fixture
def high_compatibility_users(db_session):
    """Create users with high compatibility scores"""
    setup_factories(db_session)
    
    user1 = UserFactory(
        email="highcompat1@test.com",
        emotional_depth_score=9.0
    )
    user2 = UserFactory(
        email="highcompat2@test.com", 
        emotional_depth_score=8.8
    )
    
    # Similar interests and values for high compatibility
    profile1 = ProfileFactory(
        user_id=user1.id,
        interests=["cooking", "hiking", "reading", "music"],
        core_values={
            "relationship_values": "I value loyalty, commitment, and emotional growth",
            "connection_style": "I prefer deep, meaningful conversations"
        }
    )
    
    profile2 = ProfileFactory(
        user_id=user2.id,
        interests=["cooking", "travel", "reading", "art"],  # 50% overlap
        core_values={
            "relationship_values": "Loyalty and emotional connection are most important",
            "connection_style": "I love deep philosophical discussions"
        }
    )
    
    return {
        "user1": user1, "user2": user2,
        "profile1": profile1, "profile2": profile2,
        "expected_compatibility": 85.0  # High compatibility expected
    }


@pytest.fixture
def low_compatibility_users(db_session):
    """Create users with low compatibility scores"""
    setup_factories(db_session)
    
    user1 = UserFactory(
        email="lowcompat1@test.com",
        emotional_depth_score=3.0
    )
    user2 = UserFactory(
        email="lowcompat2@test.com",
        emotional_depth_score=2.5
    )
    
    # Very different interests and values
    profile1 = ProfileFactory(
        user_id=user1.id,
        interests=["extreme_sports", "partying"],
        core_values={
            "relationship_values": "I just want to have fun and keep things casual",
            "connection_style": "Light, fun conversations only"
        }
    )
    
    profile2 = ProfileFactory(
        user_id=user2.id,
        interests=["reading", "meditation"],  # No overlap
        core_values={
            "relationship_values": "Deep commitment and spiritual growth",
            "connection_style": "Soul-deep philosophical discussions"
        }
    )
    
    return {
        "user1": user1, "user2": user2,
        "profile1": profile1, "profile2": profile2,
        "expected_compatibility": 25.0  # Low compatibility expected
    }


@pytest.fixture
def complete_revelation_cycle(db_session):
    """Create a complete 7-day revelation cycle"""
    setup_factories(db_session)
    
    connection_data = create_complete_soul_connection(db_session)
    connection = connection_data["connection"]
    
    # Create revelations for all 7 days
    revelations = []
    for day in range(1, 8):
        revelation = DailyRevelationFactory(
            connection_id=connection.id,
            user_id=connection_data["users"][0].id,
            day_number=day,
            revelation_type=RevelationType(f"day_{day}"),
            content=f"Day {day} revelation: {fake.text(max_nb_chars=200)}"
        )
        revelations.append(revelation)
    
    return {
        "connection": connection,
        "users": connection_data["users"],
        "revelations": revelations,
        "total_days": 7
    }


@pytest.fixture
def multi_stage_connections(db_session):
    """Create connections at different stages for testing progression"""
    setup_factories(db_session)
    
    users = [UserFactory() for _ in range(6)]
    connections = []
    
    stages = [
        ConnectionStage.SOUL_DISCOVERY,
        ConnectionStage.REVELATION_PHASE,
        ConnectionStage.DEEPER_CONNECTION,
        ConnectionStage.PHOTO_REVEAL,
        ConnectionStage.DINNER_PLANNING,
        ConnectionStage.COMPLETED
    ]
    
    for i, stage in enumerate(stages):
        connection = SoulConnectionFactory(
            user1_id=users[i].id,
            user2_id=users[(i+1) % len(users)].id,
            connection_stage=stage.value,
            reveal_day=i + 1
        )
        connections.append(connection)
    
    return {
        "users": users,
        "connections": connections,
        "stages": stages
    }


@pytest.fixture
def websocket_test_data(db_session):
    """Create test data specifically for WebSocket testing"""
    setup_factories(db_session)
    
    # Create 3 users for multi-user WebSocket testing
    users = [UserFactory() for _ in range(3)]
    
    # Create connections between users
    connection1 = SoulConnectionFactory(
        user1_id=users[0].id,
        user2_id=users[1].id,
        connection_stage=ConnectionStage.REVELATION_PHASE.value
    )
    
    connection2 = SoulConnectionFactory(
        user1_id=users[1].id,
        user2_id=users[2].id,
        connection_stage=ConnectionStage.DEEPER_CONNECTION.value
    )
    
    return {
        "users": users,
        "connections": [connection1, connection2],
        "mock_websockets": {user.id: f"mock_ws_{user.id}" for user in users}
    }


@pytest.fixture
def security_test_data(db_session):
    """Create test data for security and authorization testing"""
    setup_factories(db_session)
    
    # Create admin user
    admin_user = UserFactory(
        email="admin@test.com",
        username="admin",
        # Add admin role if model supports it
    )
    
    # Create regular users
    regular_users = [UserFactory() for _ in range(3)]
    
    # Create some connections with different privacy levels
    private_connection = SoulConnectionFactory(
        user1_id=regular_users[0].id,
        user2_id=regular_users[1].id,
        privacy_level="private"
    )
    
    public_connection = SoulConnectionFactory(
        user1_id=regular_users[1].id,
        user2_id=regular_users[2].id,
        privacy_level="public"  
    )
    
    return {
        "admin_user": admin_user,
        "regular_users": regular_users,
        "private_connection": private_connection,
        "public_connection": public_connection
    }


@pytest.fixture
def performance_test_data(db_session):
    """Create large dataset for performance testing"""
    setup_factories(db_session)
    
    # Create many users for load testing
    users = [UserFactory() for _ in range(20)]
    profiles = [ProfileFactory(user_id=user.id) for user in users]
    
    # Create many connections for compatibility testing
    connections = []
    for i in range(0, len(users)-1, 2):
        connection = SoulConnectionFactory(
            user1_id=users[i].id,
            user2_id=users[i+1].id
        )
        connections.append(connection)
    
    return {
        "users": users,
        "profiles": profiles,
        "connections": connections,
        "total_users": len(users)
    }
