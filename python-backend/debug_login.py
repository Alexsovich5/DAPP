#!/usr/bin/env python3

"""
Debug script to understand login failures
"""

import os
import sys
sys.path.append('.')

# Set test environment  
os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/test_dinner_app"
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.core.database import SessionLocal
from app.core.security import get_password_hash, verify_password
import uuid

def debug_login():
    """Debug login process step by step"""
    
    # Create a user manually
    session = SessionLocal()
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Create user
        test_email = f"debug_{unique_id}@example.com"
        test_password = "testpassword"
        
        user = User(
            email=test_email,
            username=f"debug_{unique_id}",
            hashed_password=get_password_hash(test_password),
            is_active=True,
            emotional_onboarding_completed=True,
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"Created user: {user.email}")
        print(f"Password hash: {user.hashed_password}")
        
        # Verify password works
        print(f"Password verification: {verify_password(test_password, user.hashed_password)}")
        
        # Test the actual API endpoint
        client = TestClient(app)
        
        print(f"\\nTesting login with email: {test_email}")
        print(f"Testing login with password: {test_password}")
        
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_email, "password": test_password},
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Query the user to check it exists
        found_user = session.query(User).filter(User.email == test_email).first()
        if found_user:
            print(f"\\nFound user in DB: {found_user.email}")
            print(f"User active: {found_user.is_active}")
            print(f"Hash matches: {found_user.hashed_password == user.hashed_password}")
        else:
            print("\\nUser not found in database!")
            
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    debug_login()