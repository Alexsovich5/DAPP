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
from app.main import app

def test_user_search_debug():
    print("=== Debugging User Search Validation Error ===")
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./user_search_debug.db"
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
            print(f"\n=== Testing User Search ===")
            
            # Test the exact same request as the failing test
            response = client.get(
                "/api/v1/users/search",
                params={"q": "test"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 422:
                print("\n=== 422 Validation Error Details ===")
                try:
                    error_data = response.json()
                    print(f"Error JSON: {error_data}")
                except:
                    print("Could not parse error as JSON")
            
            # Let's also test without the query parameter to see what happens
            print(f"\n=== Testing without query parameter ===")
            response2 = client.get(
                "/api/v1/users/search",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"No params - Status: {response2.status_code}")
            print(f"No params - Body: {response2.text}")
            
            # Test with different parameter name
            print(f"\n=== Testing with different parameter ===")
            response3 = client.get(
                "/api/v1/users/search?query=test",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Different param - Status: {response3.status_code}")
            print(f"Different param - Body: {response3.text}")
        
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
    test_user_search_debug()