from datetime import date

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

def test_login(client, db_session):
    from app.core.security import hash_password
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="login@example.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=90000,
        first_name="Login",
        last_name="Employee",
        email="login.profile@example.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()

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

def test_active_employee_can_login(client, db_session):
    from app.core.security import hash_password
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="active.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=90001,
        first_name="Active",
        last_name="Employee",
        email="active.employee.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "active.employee@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_inactive_employee_cannot_login(client, db_session):
    from app.core.security import hash_password
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="inactive.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=90002,
        first_name="Inactive",
        last_name="Employee",
        email="inactive.employee.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="inactive"
    )

    db_session.add(employee)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "inactive.employee@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee account is inactive"


def test_employee_without_profile_cannot_login(
    client,
    db_session
):
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email="orphan.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "orphan.employee@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee profile not found"
