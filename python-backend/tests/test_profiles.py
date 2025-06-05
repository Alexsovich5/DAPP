import pytest  # noqa: F401
from fastapi import status


def test_create_profile(client, test_user):
    """Test profile creation"""
    response = client.post(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
        json={
            "full_name": "New Test User",
            "bio": "I love food and meeting new people",
            "cuisine_preferences": "Italian, French",
            "dietary_restrictions": "Vegetarian",
            "location": "New York",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "New Test User"
    assert data["bio"] == "I love food and meeting new people"
    assert data["cuisine_preferences"] == "Italian, French"


def test_get_my_profile(client, test_user):
    """Test getting user's own profile"""
    response = client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Test User"
    assert data["bio"] == "Test bio"
    assert data["cuisine_preferences"] == "Italian, Japanese"


def test_update_profile(client, test_user):
    """Test profile update"""
    response = client.put(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
        json={
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "cuisine_preferences": "Mexican, Thai",
            "dietary_restrictions": "None",
            "location": "Updated City",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["bio"] == "Updated bio"
    assert data["cuisine_preferences"] == "Mexican, Thai"


def test_get_profile_unauthorized(client):
    """Test accessing profile without authentication"""
    response = client.get("/api/v1/profiles/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
