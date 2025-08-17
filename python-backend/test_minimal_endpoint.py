#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base, get_db
from app.models.user import User

def test_minimal_endpoint():
    print("=== Testing Minimal Endpoint with Dependency Override ===")
    
    # Create minimal app to test dependency injection
    test_app = FastAPI()
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./minimal_endpoint_test.db"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestSessionLocal()
    
    # Add a test endpoint that uses get_db
    @test_app.get("/test-db")
    def test_endpoint(db: Session = Depends(get_db)):
        count = db.query(User).count()
        return {"user_count": count, "session_id": id(db)}
    
    # Create a user in our test session
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="dummy",
        is_active=True,
    )
    session.add(user)
    session.commit()
    
    print(f"Created user in session {id(session)}")
    
    # Test without override first
    with TestClient(test_app) as client:
        response = client.get("/test-db")
        data = response.json()
        print(f"Without override - Users: {data['user_count']}, Session: {data['session_id']}")
    
    # Now test with override
    def override_get_db():
        print(f"🔧 Override called - returning session {id(session)}")
        return session
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as client:
        response = client.get("/test-db")
        data = response.json()
        print(f"With override - Users: {data['user_count']}, Session: {data['session_id']}")
        
        if data['user_count'] == 1 and data['session_id'] == id(session):
            print("✅ Dependency override works!")
        else:
            print("❌ Dependency override failed!")
    
    session.close()

if __name__ == "__main__":
    test_minimal_endpoint()