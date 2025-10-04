import os
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

# Set test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = (
    "postgresql://postgres:postgres@localhost:5433/test_dinner_app"
)

# === ENGINE-LEVEL DATABASE OVERRIDE ===
# Create test database engine and session BEFORE importing app modules
# This ensures both test fixtures and API endpoints use the same session

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/test_dinner_app"

# Create test engine with same configuration as production
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_size=5,  # Increased pool size for test compatibility
    max_overflow=10,  # Allow some overflow for test scenarios
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 10,
        "application_name": "dinner_app_test",
    },
    echo=False,  # Set to True for SQL debugging
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Global test session that will be shared between fixtures and API
_test_db_session = None


def get_test_db():
    """Test database session that returns the same session for fixtures and API"""
    global _test_db_session
    if _test_db_session is None:
        _test_db_session = TestSessionLocal()
    return _test_db_session


# === PATCH DATABASE MODULE ===
# Import and patch the database module before importing app components
import app.core.database as db_module  # noqa: E402

# Replace production engine and session with test versions
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal


# Override get_db to use our shared test session
def patched_get_db():
    """Patched get_db that yields the shared test session"""
    global _test_db_session
    if _test_db_session is None:
        _test_db_session = TestSessionLocal()

    # Always yield the same session object
    yield _test_db_session


db_module.get_db = patched_get_db

# Now import app components - they will use our patched database
from app.core.database import Base  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.main import app  # noqa: E402
from app.models.match import Match, MatchStatus  # noqa: E402
from app.models.profile import Profile  # noqa: E402
from app.models.user import User  # noqa: E402

# Import test factories
from tests.factories import DailyRevelationFactory  # noqa: E402
from tests.factories import (  # noqa: E402
    MessageFactory,
    PhotoRevealFactory,
    ProfileFactory,
    SoulConnectionFactory,
    UserFactory,
    create_complete_soul_connection,
    setup_factories,
)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables using our test engine"""
    if database_exists(TEST_DATABASE_URL):
        drop_database(TEST_DATABASE_URL)

    create_database(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    drop_database(TEST_DATABASE_URL)


@pytest.fixture
def db_session(test_db):
    """Return the shared test database session used by both fixtures and API"""
    global _test_db_session

    # Initialize the shared session if not already created
    if _test_db_session is None:
        _test_db_session = TestSessionLocal()

    # Setup factories with the shared session
    setup_factories(_test_db_session)

    yield _test_db_session

    # Clean up test data but keep the session alive for API calls
    try:
        from sqlalchemy import text

        # Clean up in proper foreign key order to prevent constraint violations
        # 1. Delete dependent tables first
        _test_db_session.execute(
            text(
                "DELETE FROM photo_reveal_events WHERE timeline_id IN (SELECT id FROM photo_reveal_timelines WHERE connection_id IN (SELECT id FROM soul_connections WHERE user1_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR user2_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com')))"
            )
        )
        _test_db_session.execute(
            text(
                "DELETE FROM photo_reveal_timelines WHERE connection_id IN (SELECT id FROM soul_connections WHERE user1_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR user2_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com'))"
            )
        )
        _test_db_session.execute(
            text(
                "DELETE FROM daily_revelations WHERE connection_id IN (SELECT id FROM soul_connections WHERE user1_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR user2_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com'))"
            )
        )
        _test_db_session.execute(
            text(
                "DELETE FROM messages WHERE connection_id IN (SELECT id FROM soul_connections WHERE user1_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR user2_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com'))"
            )
        )

        # 2. Delete connection-related tables
        _test_db_session.execute(
            text(
                "DELETE FROM soul_connections WHERE user1_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR user2_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com')"
            )
        )
        _test_db_session.execute(
            text(
                "DELETE FROM matches WHERE sender_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com') OR receiver_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com')"
            )
        )

        # 3. Delete user-specific tables
        _test_db_session.execute(
            text(
                "DELETE FROM profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com')"
            )
        )

        # 4. Finally delete users
        _test_db_session.execute(
            text(
                "DELETE FROM users WHERE email LIKE '%example.com' OR email LIKE '%test.com' OR username LIKE 'souluser%' OR username LIKE 'test_%'"
            )
        )

        _test_db_session.commit()
        # DON'T close the session - it needs to stay alive for API calls
    except Exception as e:
        print(f"Cleanup error: {e}")
        try:
            _test_db_session.rollback()
        except Exception:
            pass


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client that uses the patched database session"""
    # No need for dependency overrides - the database module is already patched
    # Both this client and the db_session fixture use the same shared session

    with TestClient(app) as test_client:
        yield test_client

    # No cleanup needed - session sharing is handled at the engine level


@pytest.fixture
def test_user(db_session) -> Dict[str, str]:
    """Create a test user and return credentials"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
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
        "username": user.username,
        "password": "testpassword",  # Store the original password for tests
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
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    recipient = User(
        email=f"recipient_{unique_id}@example.com",
        username=f"recipient_{unique_id}",
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
        "user": UserFactory,
        "profile": ProfileFactory,
        "soul_connection": SoulConnectionFactory,
        "revelation": DailyRevelationFactory,
        "message": MessageFactory,
        "photo_reveal": PhotoRevealFactory,
    }


@pytest.fixture
def soul_connection_data(db_session):
    """Create complete soul connection test data"""
    return create_complete_soul_connection(db_session)


@pytest.fixture
def authenticated_user(db_session) -> Dict[str, Any]:
    """CREATE → TEST → DELETE: Create real authenticated user for testing"""
    import uuid

    # Generate unique identifier to prevent constraint violations
    unique_id = str(uuid.uuid4())[:8]

    # CREATE: Create real user that authentication system can find
    user = User(
        email=f"souluser_{unique_id}@test.com",
        username=f"souluser_{unique_id}",
        hashed_password=get_password_hash("testpass123"),
        first_name="Soul",
        last_name="User",
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=8.5,
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
        cuisine_preferences="All cuisines",
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
        "headers": {"Authorization": f"Bearer {token}"},
    }
    # DELETE: Cleanup handled by db_session fixture


@pytest.fixture
def authenticated_user_connection(db_session, authenticated_user) -> Dict[str, Any]:
    """Create a soul connection that includes the authenticated user"""
    import uuid

    from app.models.soul_connection import ConnectionEnergyLevel, SoulConnection

    # Generate unique identifier to prevent constraint violations
    unique_id = str(uuid.uuid4())[:8]

    # Create a second user for the connection
    partner_user = User(
        email=f"partner_{unique_id}@test.com",
        username=f"partner_{unique_id}",
        hashed_password=get_password_hash("testpass123"),
        first_name="Partner",
        last_name="User",
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=7.8,
    )

    # Commit partner user to database
    db_session.add(partner_user)
    db_session.commit()
    db_session.refresh(partner_user)

    # Create profile for partner
    partner_profile = Profile(
        user_id=partner_user.id,
        full_name="Partner User",
        bio="Soul connection partner for testing",
        location="Test City, TC",
        cuisine_preferences="All cuisines",
    )
    db_session.add(partner_profile)
    db_session.commit()
    db_session.refresh(partner_profile)

    # Create soul connection between authenticated user and partner
    connection = SoulConnection(
        user1_id=authenticated_user["user"].id,
        user2_id=partner_user.id,
        initiated_by=authenticated_user["user"].id,
        compatibility_score=85.5,
        compatibility_breakdown={
            "interests": 80.0,
            "values": 90.0,
            "demographics": 85.0,
        },
        connection_stage="active_connection",
        current_energy_level=ConnectionEnergyLevel.HIGH.value,
        status="active",
    )

    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)

    return {
        "connection": connection,
        "authenticated_user": authenticated_user["user"],
        "partner_user": partner_user,
        "partner_profile": partner_profile,
    }


@pytest.fixture
def matching_users(db_session) -> Dict[str, Any]:
    """Create two users ready for soul connection matching"""
    import uuid
    from datetime import date

    # Generate unique identifiers to prevent constraint violations
    unique_id = str(uuid.uuid4())[:8]

    user1 = User(
        email=f"match1_{unique_id}@test.com",
        username=f"match1_{unique_id}",
        hashed_password=get_password_hash("testpass123"),
        first_name="Match",
        last_name="One",
        date_of_birth=date(1990, 5, 15),
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=7.5,
    )
    user2 = User(
        email=f"match2_{unique_id}@test.com",
        username=f"match2_{unique_id}",
        hashed_password=get_password_hash("testpass123"),
        first_name="Match",
        last_name="Two",
        date_of_birth=date(1992, 8, 20),
        is_active=True,
        emotional_onboarding_completed=True,
        emotional_depth_score=8.0,
    )

    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    return {"user1": user1, "user2": user2}


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTP client for testing async endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def photo_reveal_service(db_session):
    """Photo Reveal Service instance for testing"""
    from app.services.photo_reveal_service import PhotoRevealService

    service = PhotoRevealService()
    service.db = db_session  # Inject the test database session
    return service


@pytest.fixture
def realtime_service(db_session):
    """Real-time service instance for testing WebSocket functionality"""
    from app.services.realtime import ConnectionManager

    service = ConnectionManager(db_session)
    return service


@pytest.fixture
def connection_manager(db_session):
    """Connection manager instance for testing (alias for realtime_service)"""
    from app.services.realtime_connection_manager import RealtimeConnectionManager

    manager = RealtimeConnectionManager()
    return manager


@pytest.fixture
def performance_config():
    """Configuration for performance testing"""
    return {
        "matching_algorithm_max_time": 0.5,  # 500ms max
        "database_query_max_time": 0.1,  # 100ms max
        "api_response_max_time": 2.0,  # 2s max
        "concurrent_users": 50,  # Load testing
    }
