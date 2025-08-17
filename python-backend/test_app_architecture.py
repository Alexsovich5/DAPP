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
from app.core.security import get_password_hash
from app.models.user import User
from app.main import app

def test_app_architecture():
    print("=== Testing App Architecture Issue ===")
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./app_architecture_test.db"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestSessionLocal()
    
    try:
        # Create user
        unique_id = str(uuid.uuid4())[:8]
        email = f"test{unique_id}@example.com"
        
        user = User(
            email=email,
            username=f"testuser{unique_id}",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ User created: {email}")
        
        # Test the app structure
        print(f"\nApp structure:")
        print(f"Main app: {app}")
        print(f"Main app dependency overrides: {app.dependency_overrides}")
        
        # Check if there's a sub-app
        for route in app.routes:
            if hasattr(route, 'app'):
                print(f"Sub-app found: {route}")
                print(f"Sub-app path: {getattr(route, 'path', 'unknown')}")
                print(f"Sub-app instance: {route.app}")
                print(f"Sub-app dependency overrides: {route.app.dependency_overrides}")
        
        # Now let's try overriding on BOTH the main app and sub-apps
        def override_get_db():
            print(f"🔧 Override called - returning session {id(session)}")
            return session
        
        print(f"\n=== Setting overrides on all apps ===")
        
        # Override on main app
        app.dependency_overrides[get_db] = override_get_db
        print("✅ Set override on main app")
        
        # Override on sub-apps
        for route in app.routes:
            if hasattr(route, 'app') and hasattr(route.app, 'dependency_overrides'):
                route.app.dependency_overrides[get_db] = override_get_db
                print(f"✅ Set override on sub-app: {getattr(route, 'path', 'unknown')}")
        
        # Test login now
        with TestClient(app) as client:
            print(f"\n=== Testing Login After Setting All Overrides ===")
            
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": "testpassword"}
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ LOGIN SUCCESS!")
            else:
                print("❌ LOGIN STILL FAILED")
        
        # Clear all overrides
        app.dependency_overrides.clear()
        for route in app.routes:
            if hasattr(route, 'app') and hasattr(route.app, 'dependency_overrides'):
                route.app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_app_architecture()