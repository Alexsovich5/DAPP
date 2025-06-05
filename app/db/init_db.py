from sqlalchemy.orm import Session
from typing import List

from app.core.security import get_password_hash
from app.models.user import User
from app.models.profile import Profile


def create_test_users(db: Session) -> List[User]:
    test_users = [
        {
            "email": "test1@example.com",
            "username": "testuser1",
            "password": "password123",
            "profile": {
                "full_name": "Test User 1",
                "bio": "I love trying new restaurants and cuisines!",
                "cuisine_preferences": "Italian, Japanese, Thai",
                "dietary_restrictions": "None",
                "location": "New York",
            },
        },
        {
            "email": "test2@example.com",
            "username": "testuser2",
            "password": "password123",
            "profile": {
                "full_name": "Test User 2",
                "bio": "Foodie looking for dinner companions",
                "cuisine_preferences": "Mexican, Indian, French",
                "dietary_restrictions": "Vegetarian",
                "location": "New York",
            },
        },
        {
            "email": "test3@example.com",
            "username": "testuser3",
            "password": "password123",
            "profile": {
                "full_name": "Test User 3",
                "bio": "Chef who loves to explore new restaurants",
                "cuisine_preferences": "French, Mediterranean, Korean",
                "dietary_restrictions": "None",
                "location": "New York",
            },
        },
    ]

    created_users = []
    for user_data in test_users:
        # Check if user exists
        user = db.query(User).filter(User.email == user_data["email"]).first()
        if not user:
            # Create user
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"]),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create profile
            profile = Profile(user_id=user.id, **user_data["profile"])
            db.add(profile)
            db.commit()
            db.refresh(profile)

            created_users.append(user)

    return created_users


def init_db(db: Session) -> None:
    """Initialize the database with test data"""
    # Create test users with profiles
    create_test_users(db)
