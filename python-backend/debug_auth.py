#!/usr/bin/env python3

"""
Debug script to test authentication flow
"""

import os
import sys
sys.path.append('.')

# Set test environment
os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/test_dinner_app" 
os.environ["TESTING"] = "1"  # Enable testing mode

from app.core.security import get_password_hash, verify_password
from app.core.database import SessionLocal
from app.models.user import User
import uuid

def test_password_flow():
    """Test the complete password flow"""
    
    # 1. Test basic password hashing
    password = "testpassword"
    hashed = get_password_hash(password)
    
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed}")
    print(f"Verification result: {verify_password(password, hashed)}")
    print("---")
    
    # 2. Create a test user in database (like the fixture does)
    session = SessionLocal()
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        
        user = User(
            email=f"debug_test_{unique_id}@example.com",
            username=f"debug_test_{unique_id}",
            hashed_password=get_password_hash(password),
            is_active=True,
            emotional_onboarding_completed=True,
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"Created user: {user.email}")
        print(f"User ID: {user.id}")
        print(f"Stored hash: {user.hashed_password}")
        
        # 3. Test verification against stored hash
        verification_result = verify_password(password, user.hashed_password)
        print(f"Verification against stored hash: {verification_result}")
        
        # 4. Fetch user from database and test (like login does)
        db_user = session.query(User).filter(User.email == user.email).first()
        
        if db_user:
            print(f"Found user in DB: {db_user.email}")
            db_verification = verify_password(password, db_user.hashed_password)
            print(f"DB verification result: {db_verification}")
        else:
            print("User not found in database!")
            
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_password_flow()