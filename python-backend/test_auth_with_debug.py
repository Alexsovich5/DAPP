#!/usr/bin/env python3

import os
import sys
import logging
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.api.v1.routers.auth")
logger.setLevel(logging.DEBUG)

from app.core.security import get_password_hash, verify_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User
from fastapi.testclient import TestClient
from app.main import app
import uuid

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_auth_debug2.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_auth_with_debug():
    print("=== Testing Auth with Debug Logging ===")
    
    db_session = TestSessionLocal()
    
    try:
        # Create user
        unique_id = str(uuid.uuid4())[:8]
        email = f"test{unique_id}@example.com"
        plain_password = "testpassword"
        
        hashed_password = get_password_hash(plain_password)
        
        user = User(
            email=email,
            username=f"testuser{unique_id}",
            hashed_password=hashed_password,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        print(f"Created user: {email}")
        print(f"Password hash: {hashed_password}")
        
        # Override database dependency
        def override_get_db():
            return db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            print(f"\n=== Making login request ===")
            response = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": plain_password}
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response: {response.text}")
        
        app.dependency_overrides.clear()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_auth_with_debug()