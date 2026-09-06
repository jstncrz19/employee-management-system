from datetime import date

from sqlalchemy import select


def register_payload(**overrides):
    payload = {
        "email": "test@example.com",
        "password": "testpassword123",
        "employee_number": 70001,
        "first_name": "Test",
        "last_name": "User",
        "department": "IT",
        "position": "Developer",
        "date_hired": "2026-08-24"
    }
    payload.update(overrides)
    return payload


def test_register_user(client, db_session):
    from app.models.employee import Employee
    from app.models.leave_balance import LeaveBalance

    response = client.post(
        "/auth/register",
        json=register_payload()
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["role"] == "employee"
    assert "id" in data
    assert "password_hash" not in data

    employee = db_session.scalar(
        select(Employee).where(Employee.email == "test@example.com")
    )

    assert employee is not None
    assert employee.status == "active"
    assert employee.employee_number == 70001

    balances = db_session.scalars(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id
        )
    ).all()

    assert len(balances) == 4

def test_register_duplicate_email(client):
    first_response = client.post(
        "/auth/register",
        json=register_payload(email="duplicate@example.com")
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=register_payload(email="duplicate@example.com")
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"

def test_register_duplicate_employee_number(client):
    first_response = client.post(
        "/auth/register",
        json=register_payload(email="num1@example.com", employee_number=71001)
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=register_payload(email="num2@example.com", employee_number=71001)
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Employee number or email already exists"
    )

def test_register_requires_employee_profile_fields(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "incomplete@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 422

def test_registered_user_can_login_immediately(client):
    response = client.post(
        "/auth/register",
        json=register_payload(
            email="usable@example.com",
            employee_number=71002
        )
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": "usable@example.com",
            "password": "testpassword123"
        }
    )

    assert login_response.status_code == 200
    assert login_response.json()["access_token"]

    me_response = client.get(
        "/employees/me",
        headers={
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "usable@example.com"

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
        json=register_payload(
            email="invalid-login@example.com",
            employee_number=71003
        )
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
