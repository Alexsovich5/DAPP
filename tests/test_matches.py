from fastapi import status
from datetime import datetime


def test_create_match(client, test_user, auth_headers):
    """Test creating a new match"""
    data = {
        "recipient_id": 2,
        "restaurant_preference": "Italian",
        "proposed_date": datetime.utcnow().isoformat(),
    }

    response = client.post("/api/v1/matches/", json=data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["restaurant_preference"] == "Italian"
    assert response.json()["status"] == "pending"


def test_create_invalid_match(client, test_user, auth_headers):
    """Test creating a match with invalid data"""
    # Test self-match
    data = {"recipient_id": test_user["user_id"],
            "restaurant_preference": "Italian"}
    response = client.post("/api/v1/matches/", json=data, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cannot create a match with yourself"


def test_get_matches(client, test_user, test_match, auth_headers):
    """Test retrieving matches"""
    # Test getting sent matches
    response = client.get("/api/v1/matches/sent", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1

    # Test getting received matches
    response = client.get("/api/v1/matches/received", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


def test_update_match(client, test_user, test_match, auth_headers):
    """Test updating a match status"""
    data = {"status": "accepted", "restaurant_preference": "Japanese"}
    response = client.put(
        f"/api/v1/matches/{test_match.id}", json=data, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "accepted"
    assert response.json()["restaurant_preference"] == "Japanese"


def test_update_invalid_match(client, test_user, test_match, auth_headers):
    """Test updating a match with invalid data"""
    data = {"status": "invalid_status"}
    response = client.put(
        f"/api/v1/matches/{test_match.id}", json=data, headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
