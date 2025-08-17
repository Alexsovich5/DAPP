#!/usr/bin/env python3

import os
import sys
import logging
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

# Enable debug logging specifically for auth router
logging.basicConfig(level=logging.DEBUG)
auth_logger = logging.getLogger("app.api.v1.routers.auth")
auth_logger.setLevel(logging.DEBUG)

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.main import app

# Create test database exactly like conftest.py
TEST_DATABASE_URL = "sqlite:///./session_debug_test_v2.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_session_with_debug_logging():
    print("=== Testing Session with Debug Logging ===")
    
    # Create session like conftest.py
    db_session = TestSessionLocal()
    
    try:
        # Create user like test_user fixture
        unique_id = str(uuid.uuid4())[:8]
        email = f"test{unique_id}@example.com"
        username = f"testuser{unique_id}"
        password = "testpassword"
        
        print(f"Creating user: {email}")
        
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        print(f"User created with ID: {user.id}")
        
        # Track how many times get_db override is called
        call_count = 0
        
        def override_get_db():
            """Return the same session instance used by the test"""
            nonlocal call_count
            call_count += 1
            print(f"override_get_db called #{call_count} - returning session {id(db_session)}")
            return db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            print(f"\n=== Testing FastAPI Login with Debug ===")
            
            # Test login exactly like the failing test
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": password}
            )
            
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {response.text}")
            print(f"get_db override called {call_count} times")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_session_with_debug_logging()