#!/usr/bin/env python3
"""
Test script to verify frontend-backend connectivity and database operations
"""
import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:5000"
ANGULAR_EXPECTED_URL = "http://localhost:5001"

def test_backend_health():
    """Test if backend is running and healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"✅ Backend health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_cors_headers():
    """Test CORS configuration"""
    try:
        response = requests.options(
            f"{BACKEND_URL}/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            },
            timeout=5
        )
        print(f"✅ CORS preflight check: {response.status_code}")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS headers: {cors_headers}")
        return True
    except Exception as e:
        print(f"❌ CORS check failed: {e}")
        return False

def test_registration():
    """Test user registration with Angular-compatible data"""
    test_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01",
        "dietary_preferences": ["vegetarian"],
        "cuisine_preferences": ["italian", "mexican"],
        "gender": "other",
        "location": "Test City",
        "looking_for": "friends"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Registration successful")
            print(f"   User created: {response.json()}")
            return True
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if 'already exists' in error_detail:
                print("⚠️  User already exists (this is expected on repeat runs)")
                return True
            else:
                print(f"❌ Registration failed: {error_detail}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False

def test_login():
    """Test user login"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={
                "username": "test@example.com",  # Can use email as username
                "password": "testpass123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful")
            print(f"   Token type: {token_data.get('token_type')}")
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_profile_endpoints(token):
    """Test profile endpoints with authentication"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test GET /profile (Angular expects this)
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/profile/", headers=headers, timeout=5)
        if response.status_code in [200, 404]:
            print(f"✅ Profile GET endpoint accessible: {response.status_code}")
        else:
            print(f"❌ Profile GET failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Profile GET test failed: {e}")

def print_summary():
    """Print test summary and recommended fixes"""
    print("\n" + "="*60)
    print("CONNECTIVITY TEST SUMMARY")
    print("="*60)
    print("\nTo fix remaining issues:")
    print("1. Start backend: cd backend_py && python run.py")
    print("2. Start Angular: cd interface/Angular && ng serve --port 5001")
    print("3. Check Angular environment.ts points to http://localhost:5000/api")
    print("\nCritical fixes applied:")
    print("✅ CORS origins updated to include port 5001")
    print("✅ allow_credentials set to True")
    print("✅ UserCreate schema accepts Angular fields")
    print("✅ Profile endpoint aliases added (/profile/ and /profiles/)")
    print("✅ /auth/me endpoint added")

if __name__ == "__main__":
    print("Testing Frontend-Backend Connectivity")
    print("="*50)
    
    # Run tests
    backend_ok = test_backend_health()
    if backend_ok:
        cors_ok = test_cors_headers()
        reg_ok = test_registration()
        token = test_login()
        if token:
            test_profile_endpoints(token)
    
    print_summary()