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
import inspect

def test_get_db_introspection():
    print("=== Introspecting get_db Function ===")
    
    # Let's inspect the get_db function
    print(f"get_db function: {get_db}")
    print(f"get_db module: {get_db.__module__}")
    print(f"get_db file: {inspect.getfile(get_db)}")
    print(f"get_db code: {inspect.getsource(get_db)}")
    
    # Let's see all get_db related imports in the auth router
    from app.api.v1.routers import auth
    print(f"\nAuth router get_db: {auth.get_db}")
    print(f"Auth router get_db same as core: {auth.get_db is get_db}")
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./get_db_introspection_test.db" 
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestSessionLocal()
    
    try:
        # Create user
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
        
        print(f"\n✅ User created: {email}")
        
        # Override BOTH get_db references
        def override_get_db():
            print(f"🔧 override_get_db called!")
            return session

        # Set override on the app
        app.dependency_overrides[get_db] = override_get_db
        print(f"\nDependency overrides set: {list(app.dependency_overrides.keys())}")
        
        # Also try overriding the imported reference in auth router
        auth.get_db = override_get_db
        print(f"Also overrode auth.get_db directly")
        
        with TestClient(app) as client:
            print(f"\n=== Testing Login ===")
            
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": "testpassword"}
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
            else:
                print("❌ FAILED")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_get_db_introspection()