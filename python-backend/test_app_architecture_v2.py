#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

import uuid
from fastapi.testclient import TestClient
from fastapi.routing import Mount
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.main import app

def test_app_architecture_v2():
    print("=== Testing App Architecture Issue V2 ===")
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./app_architecture_test_v2.db"
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
        
        # Test the app structure more carefully
        print(f"\nApp structure:")
        print(f"Main app: {app}")
        print(f"Main app dependency overrides: {app.dependency_overrides}")
        
        # Look for Mount routes specifically
        print(f"\nRoutes:")
        for route in app.routes:
            print(f"Route: {route}")
            print(f"Route type: {type(route)}")
            if isinstance(route, Mount):
                print(f"Mount path: {route.path}")
                print(f"Mount app: {route.app}")
                print(f"Mount app type: {type(route.app)}")
                if hasattr(route.app, 'dependency_overrides'):
                    print(f"Mount app dependency overrides: {route.app.dependency_overrides}")
        
        # Override function
        def override_get_db():
            print(f"🔧 Override called - returning session {id(session)}")
            return session
        
        print(f"\n=== Setting overrides ===")
        
        # Override on main app
        app.dependency_overrides[get_db] = override_get_db
        print("✅ Set override on main app")
        
        # Override on mounted FastAPI sub-apps
        for route in app.routes:
            if isinstance(route, Mount) and hasattr(route.app, 'dependency_overrides'):
                route.app.dependency_overrides[get_db] = override_get_db
                print(f"✅ Set override on mounted app: {route.path}")
        
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
                
                # Let's also test the other mount point
                print("\n=== Testing alternative mount point ===")
                response2 = client.post(
                    "/api/auth/login",
                    data={"username": email, "password": "testpassword"}
                )
                print(f"Alternative mount Status: {response2.status_code}")
                print(f"Alternative mount Body: {response2.text}")
        
        # Clear all overrides
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
    test_app_architecture_v2()