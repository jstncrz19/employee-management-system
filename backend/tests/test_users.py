from datetime import datetime, timedelta, timezone

import jwt

from app.core.security import create_access_token, hash_password
from app.models.user import User

from config import JWT_ALGORITHM, JWT_SECRET_KEY


def create_user(db_session, email="me@easyeasy.com", role="employee"):
    user = User(
        email=email,
        password_hash=hash_password("testpassword123"),
        role=role
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_get_current_user(client, db_session):
    user = create_user(db_session, role="admin")

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "me@easyeasy.com"
    assert data["role"] == "admin"
    assert "id" in data
    assert "password_hash" not in data


def test_get_current_user_employee(client, db_session):
    user = create_user(db_session, role="employee")

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["role"] == "employee"
    assert response.json()["email"] == "me@easyeasy.com"


def test_get_current_user_requires_authentication(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_current_user_rejects_invalid_token(client):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer not-a-valid-token"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_rejects_expired_token(client):
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5)
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {expired_token}"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_rejects_token_for_deleted_user(client, db_session):
    user = User(
        email="deleted.user@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)

    db_session.delete(user)
    db_session.commit()

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"