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
from starlette.routing import Mount
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.profile import Profile
from app.main import app

def test_profile_debug():
    print("=== Debugging Profile API 404 Errors ===")
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./profile_debug.db"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestSessionLocal()
    
    try:
        # Create test user
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
        
        print(f"✅ User created: {email}")
        
        # Create test profile (like the test_profile fixture should do)
        profile = Profile(
            user_id=user.id,
            full_name="Test User",
            bio="Test bio",
            cuisine_preferences="Italian, Japanese",
            dietary_restrictions="None",
            location="Test City"
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        
        print(f"✅ Profile created for user: {profile.full_name}")
        
        # Create access token
        token = create_access_token({"sub": user.email})
        print(f"✅ Token created")
        
        # Set up dependency override like the working conftest.py
        def override_get_db():
            return session

        # Override on main app and sub-apps
        app.dependency_overrides[get_db] = override_get_db
        for route in app.routes:
            if isinstance(route, Mount) and hasattr(route.app, 'dependency_overrides'):
                route.app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            print(f"\n=== Testing Profile Routes ===")
            
            # Test GET /api/v1/profiles/me
            print("1. Testing GET /api/v1/profiles/me")
            response = client.get(
                "/api/v1/profiles/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Body: {response.text}")
            
            # Test POST /api/v1/profiles (create profile)
            print("\n2. Testing POST /api/v1/profiles")
            response2 = client.post(
                "/api/v1/profiles",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "full_name": "New Test User",
                    "bio": "I love food and meeting new people",
                    "cuisine_preferences": "Italian, French",
                    "dietary_restrictions": "Vegetarian",
                    "location": "New York",
                }
            )
            
            print(f"   Status: {response2.status_code}")
            print(f"   Body: {response2.text}")
            
            # Test PUT /api/v1/profiles/me
            print("\n3. Testing PUT /api/v1/profiles/me")
            response3 = client.put(
                "/api/v1/profiles/me",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "full_name": "Updated Name",
                    "bio": "Updated bio",
                    "cuisine_preferences": "Mexican, Thai",
                    "dietary_restrictions": "None",
                    "location": "Updated City",
                }
            )
            
            print(f"   Status: {response3.status_code}")
            print(f"   Body: {response3.text}")
            
            # Check the app routes to see if profiles are registered
            print(f"\n=== Checking Route Registration ===")
            for route in app.routes:
                if isinstance(route, Mount):
                    print(f"Mount: {route.path} -> {route.app}")
                    if hasattr(route.app, 'routes'):
                        for sub_route in route.app.routes:
                            if 'profile' in str(sub_route):
                                print(f"  Profile route: {sub_route}")
        
        # Clear overrides
        app.dependency_overrides.clear()
        for route in app.routes:
            if isinstance(route, Mount) and hasattr(route.app, 'dependency_overrides'):
                route.app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_profile_debug()