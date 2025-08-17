#!/usr/bin/env python3
"""
Create dummy data for Dinner First application testing
"""

import requests
import json
import random
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Dummy user data
DUMMY_USERS = [
    {
        "username": "sarah_artist",
        "email": "sarah@example.com",
        "password": "password123",
        "first_name": "Sarah",
        "last_name": "Chen",
        "date_of_birth": "1992-08-15",
        "gender": "female",
        "interests": ["art", "photography", "hiking", "cooking", "wine"],
        "bio": "Creative soul looking for meaningful connections. I believe in soul before skin.",
        "values": ["authenticity", "creativity", "growth", "adventure"]
    },
    {
        "username": "james_writer",
        "email": "james@example.com", 
        "password": "password123",
        "first_name": "James",
        "last_name": "Rodriguez",
        "date_of_birth": "1988-03-22",
        "gender": "male",
        "interests": ["writing", "literature", "coffee", "travel", "music"],
        "bio": "Writer seeking deep conversations and shared adventures. Connection over appearances.",
        "values": ["intellectual_growth", "empathy", "honesty", "exploration"]
    },
    {
        "username": "mia_teacher",
        "email": "mia@example.com",
        "password": "password123", 
        "first_name": "Mia",
        "last_name": "Johnson",
        "date_of_birth": "1990-11-08",
        "gender": "female",
        "interests": ["education", "yoga", "reading", "gardening", "sustainability"],
        "bio": "Educator passionate about growth and learning. Looking for someone who values inner beauty.",
        "values": ["compassion", "sustainability", "learning", "mindfulness"]
    },
    {
        "username": "alex_developer",
        "email": "alex@example.com",
        "password": "password123",
        "first_name": "Alex",
        "last_name": "Kim",
        "date_of_birth": "1994-06-12",
        "gender": "non-binary",
        "interests": ["technology", "gaming", "meditation", "fitness", "cooking"],
        "bio": "Tech enthusiast who believes true connection transcends the physical. Let's connect souls first.",
        "values": ["innovation", "mindfulness", "equality", "authenticity"]
    },
    {
        "username": "emma_nurse",
        "email": "emma@example.com",
        "password": "password123",
        "first_name": "Emma",
        "last_name": "Williams",
        "date_of_birth": "1991-09-30",
        "gender": "female", 
        "interests": ["healthcare", "dancing", "volunteering", "animals", "nature"],
        "bio": "Healthcare worker with a big heart. Seeking someone who values kindness and emotional depth.",
        "values": ["compassion", "service", "health", "family"]
    }
]

def create_user(user_data):
    """Create a new user via API"""
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 201:
            logger.info(f"Created user: {user_data['username']}")
            return response.json()
        elif response.status_code == 400 and "already exists" in response.text:
            logger.info(f"User {user_data['username']} already exists")
            return {"message": "User already exists"}
        else:
            logger.error(f"Failed to create user {user_data['username']}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating user {user_data['username']}: {str(e)}")
        return None

def login_user(username, password):
    """Login user and get token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Logged in user: {username}")
            return data.get("access_token")
        else:
            logger.error(f"Failed to login user {username}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error logging in user {username}: {str(e)}")
        return None

def create_profile(token, profile_data):
    """Create user profile"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/profiles", json=profile_data, headers=headers)
        if response.status_code == 201:
            logger.info(f"Created profile for user")
            return response.json()
        else:
            logger.error(f"Failed to create profile: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        return None

def test_api_health():
    """Test if API is healthy and accessible"""
    try:
        response = requests.get(f"http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend API is healthy and accessible")
            return True
        else:
            logger.error(f"❌ Backend API health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to backend API: {str(e)}")
        return False

def main():
    """Main function to create dummy data"""
    logger.info("🚀 Starting dummy data creation for Dinner First")
    
    # Test API health first
    if not test_api_health():
        logger.error("Cannot proceed without healthy backend API")
        return
    
    logger.info("📝 Creating dummy users and profiles...")
    
    created_users = []
    user_tokens = {}
    
    # Create users
    for user_data in DUMMY_USERS:
        result = create_user(user_data)
        if result:
            created_users.append(user_data)
            
            # Login to get token
            token = login_user(user_data["username"], user_data["password"])
            if token:
                user_tokens[user_data["username"]] = token
                
                # Create profile
                profile_data = {
                    "bio": user_data["bio"],
                    "interests": user_data["interests"],
                    "preferences": {
                        "age_range": {"min": 25, "max": 40},
                        "distance_range": 50,
                        "looking_for": ["long_term", "friendship"]
                    },
                    "values": user_data["values"],
                    "location": {
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "USA"
                    }
                }
                
                create_profile(token, profile_data)
    
    logger.info(f"✅ Created {len(created_users)} users with profiles")
    logger.info(f"🔑 Generated {len(user_tokens)} authentication tokens")
    
    # Save tokens for testing
    with open("test_tokens.json", "w") as f:
        json.dump(user_tokens, f, indent=2)
    
    logger.info("💾 Saved authentication tokens to test_tokens.json")
    logger.info("🎉 Dummy data creation completed successfully!")
    
    print("\n" + "="*60)
    print("🌟 DUMMY DATA CREATION SUMMARY 🌟")
    print("="*60)
    print(f"✅ Users Created: {len(created_users)}")
    print(f"🔐 Tokens Generated: {len(user_tokens)}")
    print(f"🌐 Backend URL: {BASE_URL}")
    print(f"💻 Frontend URL: http://localhost:4200")
    print("="*60)
    print("\n📋 Test Users:")
    for user in created_users:
        print(f"  • {user['first_name']} {user['last_name']} (@{user['username']})")
        print(f"    Email: {user['email']} | Password: {user['password']}")
    print("\n🚀 Ready for testing with Playwright!")

if __name__ == "__main__":
    main()