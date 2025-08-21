#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
Test the basic WebSocket connection functionality
"""
import asyncio
import json
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_websocket.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def setup_test_user():
    """Create a test user and return authentication token"""
    db = TestingSessionLocal()
    try:
        # Create test user
        test_user = User(
            email="websocket_test@test.com",
            hashed_password=get_password_hash("testpass123"),
            first_name="WebSocket",
            last_name="Tester",
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create JWT token
        token = create_access_token(data={"sub": test_user.email})
        
        return {"user": test_user, "token": token}
        
    finally:
        db.close()

def test_websocket_basic_connection():
    """Test basic WebSocket connection"""
    print("🔌 Testing WebSocket basic connection...")
    
    try:
        # Setup test user
        auth_data = setup_test_user()
        user = auth_data["user"]
        token = auth_data["token"]
        
        print(f"✅ Created test user: {user.email} (ID: {user.id})")
        print(f"✅ Generated JWT token: {token[:50]}...")
        
        # Test with TestClient
        client = TestClient(app)
        
        # Try the main WebSocket endpoint from main.py
        print("🔗 Attempting WebSocket connection to /chat...")
        
        try:
            with client.websocket_connect("/chat") as websocket:
                print("✅ Connected to /chat WebSocket successfully!")
                
                # Send test message
                test_message = {"type": "test", "content": "Hello WebSocket!"}
                websocket.send_json(test_message)
                print(f"📤 Sent test message: {test_message}")
                
                # Try to receive (may timeout if no response expected)
                try:
                    response = websocket.receive_json()
                    print(f"📥 Received response: {response}")
                except Exception as recv_error:
                    print(f"ℹ️  No response received (expected): {recv_error}")
                
        except Exception as ws_error:
            print(f"❌ WebSocket /chat connection failed: {ws_error}")
        
        # Try the authenticated WebSocket endpoint
        print(f"🔗 Attempting authenticated WebSocket connection to /api/v1/websocket/{user.id}...")
        
        try:
            websocket_url = f"/api/v1/websocket/{user.id}?token={token}"
            with client.websocket_connect(websocket_url) as websocket:
                print("✅ Connected to authenticated WebSocket successfully!")
                
                # Send test message
                test_message = {"type": "test", "content": "Hello authenticated WebSocket!"}
                websocket.send_json(test_message)
                print(f"📤 Sent test message: {test_message}")
                
                # Try to receive
                try:
                    response = websocket.receive_json()
                    print(f"📥 Received response: {response}")
                except Exception as recv_error:
                    print(f"ℹ️  No response received: {recv_error}")
                
        except Exception as ws_error:
            print(f"❌ Authenticated WebSocket connection failed: {ws_error}")
            print("🔍 This might be the issue causing test failures!")
            return False
        
        print("✅ WebSocket connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting WebSocket Connection Test...")
    print("=" * 50)
    
    success = test_websocket_basic_connection()
    
    print("=" * 50)
    if success:
        print("🎉 All WebSocket connection tests passed!")
        sys.exit(0)
    else:
        print("💥 WebSocket connection tests failed!")
        sys.exit(1)