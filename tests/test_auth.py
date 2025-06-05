from fastapi import status


def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "testpassword123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data


def test_login_user(client, test_user):
    """Test user login"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"],
              "password": test_user["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_existing_email(client, test_user):
    """Test registration with existing email"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user["email"],
            "username": "differentuser",
            "password": "testpassword123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
