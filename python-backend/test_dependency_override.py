#!/usr/bin/env python3

import os
import sys
import logging
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base, get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.main import app

# Create test database exactly like conftest.py
TEST_DATABASE_URL = "sqlite:///./dependency_override_test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_dependency_override():
    print("=== Testing Dependency Override Mechanics ===")
    
    # Create session like conftest.py
    db_session = TestSessionLocal()
    
    try:
        # Create user
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
        print(f"Session ID: {id(db_session)}")
        
        # Let's inspect the app's dependency overrides
        print(f"App dependency overrides before: {app.dependency_overrides}")
        print(f"get_db function: {get_db}")
        
        # Track how many times get_db override is called
        call_count = 0
        session_ids_seen = []
        
        def override_get_db():
            """Return the same session instance used by the test"""
            nonlocal call_count, session_ids_seen
            call_count += 1
            session_ids_seen.append(id(db_session))
            print(f"🔧 override_get_db called #{call_count} - returning session {id(db_session)}")
            return db_session
        
        # Set the override
        app.dependency_overrides[get_db] = override_get_db
        print(f"App dependency overrides after setting: {list(app.dependency_overrides.keys())}")
        
        # Create client and test
        with TestClient(app) as client:
            print(f"\n=== Testing with Client ===")
            
            # Make the login request
            print("Making POST request to /api/v1/auth/login...")
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": password}
            )
            
            print(f"\nResults:")
            print(f"- Response status: {response.status_code}")
            print(f"- get_db override called {call_count} times")
            print(f"- Session IDs seen: {session_ids_seen}")
            print(f"- Response body: {response.text}")
        
        # Clear the override
        app.dependency_overrides.clear()
        print(f"App dependency overrides after clearing: {app.dependency_overrides}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_dependency_override()