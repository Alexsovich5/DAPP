#!/usr/bin/env python3

import os
import sys
import logging
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment exactly like conftest.py
os.environ["TESTING"] = "1"

import uuid
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.main import app

def test_mimic_pytest():
    print("=== Mimicking Exact Pytest Setup ===")
    
    # 1. Create test database exactly like conftest.py test_db fixture
    TEST_DATABASE_URL = "sqlite:///./mimic_pytest_test.db" 
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 2. Create db_session exactly like conftest.py db_session fixture
    session = TestSessionLocal()
    
    try:
        # 3. Create test_user exactly like conftest.py test_user fixture
        unique_id = str(uuid.uuid4())[:8]
        email = f"test{unique_id}@example.com"
        username = f"testuser{unique_id}"
        
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ User created: {email} (ID: {user.id})")
        
        # Verify the password hash was created correctly (like conftest.py does)
        from app.core.security import verify_password
        assert verify_password("testpassword", user.hashed_password), "Password hash verification failed in fixture"
        print("✅ Password verification works")
        
        token = create_access_token({"sub": user.email})
        test_user_data = {
            "user_id": user.id, 
            "email": user.email,
            "username": user.username,
            "password": "testpassword",  # Plain text password for testing
            "token": token,
            "access_token": token  # Add both for compatibility
        }
        
        print(f"✅ Test user data created")
        
        # 4. Create client exactly like conftest.py client fixture
        def override_get_db():
            """Return the same session instance used by the test"""
            print(f"🔧 override_get_db called - returning session {id(session)}")
            return session

        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as test_client:
            print(f"\n=== Testing Login (Mimicking pytest) ===")
            
            # 5. Test login exactly like test_auth.py::test_login_user
            response = test_client.post(
                "/api/v1/auth/login",
                data={"username": test_user_data["email"],
                      "password": test_user_data["password"]},
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ LOGIN SUCCESS!")
                data = response.json()
                print(f"Access token received: {data.get('access_token', 'None')[:20]}...")
            else:
                print("❌ LOGIN FAILED")
                # Debug what went wrong
                debug_user = session.query(User).filter(User.email == email).first()
                print(f"User still exists: {debug_user is not None}")
                if debug_user:
                    print(f"User ID: {debug_user.id}, Active: {debug_user.is_active}")
                    manual_verify = verify_password("testpassword", debug_user.hashed_password)
                    print(f"Manual password verification still works: {manual_verify}")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. Clean up exactly like conftest.py
        session.close()
        # Truncate all tables to ensure clean state for next test
        with engine.connect() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
            connection.commit()

if __name__ == "__main__":
    test_mimic_pytest()