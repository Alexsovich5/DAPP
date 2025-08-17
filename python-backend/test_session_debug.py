#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.main import app

# Create test database exactly like conftest.py
TEST_DATABASE_URL = "sqlite:///./session_debug_test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_session_isolation():
    print("=== Testing Session Isolation ===")
    
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
        
        # Verify user exists in this session
        found_user = db_session.query(User).filter(User.email == email).first()
        print(f"User found in same session: {found_user is not None}")
        
        # Now test with FastAPI client like conftest.py
        def override_get_db():
            """Return the same session instance used by the test"""
            print("override_get_db called - returning same session")
            return db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            print(f"\n=== Testing FastAPI Login with Session Override ===")
            
            # Test login exactly like the failing test
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": password}
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                print("✅ LOGIN SUCCESS!")
            else:
                print("❌ LOGIN FAILED")
                
                # Debug: Check if user still exists after login attempt
                debug_user = db_session.query(User).filter(User.email == email).first()
                print(f"User still exists after login attempt: {debug_user is not None}")
                if debug_user:
                    print(f"User details: ID={debug_user.id}, active={debug_user.is_active}")
                    
                    # Test password verification manually
                    manual_verify = verify_password(password, debug_user.hashed_password)
                    print(f"Manual password verification: {manual_verify}")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_session_isolation()