#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/alex/Desktop/Projects/DAPP/python-backend')

# Set testing environment
os.environ["TESTING"] = "1"

from app.core.security import get_password_hash, verify_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User

# Create test database
TEST_DATABASE_URL = "sqlite:///./debug_test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_auth():
    print("Testing authentication setup...")
    
    # Test password hashing
    test_password = "testpassword"
    hashed = get_password_hash(test_password)
    print(f"Generated hash: {hashed}")
    print(f"Verification result: {verify_password(test_password, hashed)}")
    
    # Create a test user in database
    db = SessionLocal()
    try:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"Created user: {user.email}")
        print(f"Stored hash: {user.hashed_password}")
        
        # Test verification with stored hash
        verification_result = verify_password(test_password, user.hashed_password)
        print(f"Verification with stored hash: {verification_result}")
        
        # Test with wrong password
        wrong_verification = verify_password("wrongpassword", user.hashed_password)
        print(f"Verification with wrong password: {wrong_verification}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_auth()