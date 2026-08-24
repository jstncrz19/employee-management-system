def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["role"] == "employee"
    assert "id" in data
    assert "password_hash" not in data

def test_register_duplicate_email(client):
    user_data = {
        "email": "duplicate@example.com",
        "password": "testpassword123"
    }

    first_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"

def test_login(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpassword123"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]

def test_login_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "invalid-login@example.com",
            "password": "correctpassword"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "invalid-login@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "doesnotexist@example.com",
            "password": "somepassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"