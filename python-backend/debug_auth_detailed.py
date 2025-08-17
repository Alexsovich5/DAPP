#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment exactly like pytest does
os.environ["TESTING"] = "1"

from app.core.security import get_password_hash, verify_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User
from fastapi.testclient import TestClient
from app.main import app
import uuid

# Create test database exactly like conftest.py
TEST_DATABASE_URL = "sqlite:///./test_auth_debug.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_auth_detailed():
    print("=== Detailed Auth Debug ===")
    
    # Create test user exactly like the test fixture
    db_session = TestSessionLocal()
    
    try:
        # Generate unique identifiers like the fixture
        unique_id = str(uuid.uuid4())[:8]
        email = f"test{unique_id}@example.com"
        username = f"testuser{unique_id}"
        plain_password = "testpassword"
        
        print(f"Creating user with email: {email}")
        print(f"Plain password: {plain_password}")
        
        # Hash password exactly like the fixture
        hashed_password = get_password_hash(plain_password)
        print(f"Generated hash: {hashed_password}")
        
        # Create user exactly like the fixture
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        print(f"User created with ID: {user.id}")
        print(f"Stored hash: {user.hashed_password}")
        
        # Test verification like the fixture does
        verification_result = verify_password(plain_password, user.hashed_password)
        print(f"Direct verification: {verification_result}")
        
        # Now test with FastAPI client like the actual test
        def override_get_db():
            return db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            print(f"\n=== Testing FastAPI Login ===")
            print(f"Login data: username={email}, password={plain_password}")
            
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": plain_password}
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code != 200:
                # Check if user still exists
                db_user = db_session.query(User).filter(User.email == email).first()
                if db_user:
                    print(f"User found in DB: {db_user.email}")
                    print(f"User active: {db_user.is_active}")
                    print(f"Hash verification: {verify_password(plain_password, db_user.hashed_password)}")
                else:
                    print("User not found in database!")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    debug_auth_detailed()