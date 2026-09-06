from datetime import date

import pytest

from app.core.security import create_access_token, hash_password
from app.models.employee import Employee
from app.models.user import User


def create_admin(db_session):
    admin = User(
        email="authz.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def create_employee(db_session, email="authz.employee@test.com"):
    user = User(
        email=email,
        password_hash=hash_password("employeepassword"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=50001,
        first_name="Authz",
        last_name="Employee",
        email=f"profile.{email}",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 1),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return user, employee


EMPLOYEE_PAYLOAD = {
    "employee_number": 50002,
    "first_name": "Authz",
    "last_name": "Newbie",
    "email": "authz.newbie@test.com",
    "department": "IT",
    "position": "Developer",
    "date_hired": "2026-08-24",
    "status": "active"
}


# (method, path). All requests carry no token and no body, so a 401 from
# the security dependency is the only valid outcome.
UNAUTHENTICATED_REQUESTS = [
    ("GET", "/users/me"),
    ("GET", "/employees"),
    ("GET", "/employees/1"),
    ("GET", "/attendance"),
    ("POST", "/attendance/check-in"),
    ("GET", "/attendance/me"),
    ("GET", "/leaves"),
    ("GET", "/leaves/me"),
    ("GET", "/leaves/balance/1"),
    ("GET", "/leaves/balance/me"),
    ("PATCH", "/leaves/1/approve"),
    ("PATCH", "/leaves/1/reject"),
    ("PATCH", "/leaves/1/cancel"),
    ("GET", "/dashboard/summary"),
    ("GET", "/audit-logs"),
]


@pytest.mark.parametrize(
    "method,path",
    UNAUTHENTICATED_REQUESTS
)
def test_unauthenticated_requests_return_401(client, method, path):
    response = client.request(method, path)

    assert response.status_code == 401


# (method, path, body). An authenticated employee is denied by require_admin
# before any resource lookup happens, so these return 403 regardless of
# whether the target resource exists.
EMPLOYEE_ADMIN_ONLY_REQUESTS = [
    ("GET", "/employees", None),
    ("POST", "/employees", EMPLOYEE_PAYLOAD),
    ("POST", "/employees/1/account", {
        "email": "account@test.com",
        "password": "testpassword123"
    }),
    ("GET", "/attendance", None),
    ("GET", "/leaves", None),
    ("GET", "/leaves/balance/1", None),
    ("PATCH", "/leaves/balance/1/vacation", {"total_days": 15}),
    ("PATCH", "/leaves/1/approve", None),
    ("PATCH", "/leaves/1/reject", None),
    ("GET", "/dashboard/summary", None),
    ("GET", "/audit-logs", None),
]


@pytest.mark.parametrize(
    "method,path,body",
    EMPLOYEE_ADMIN_ONLY_REQUESTS
)
def test_employee_gets_403_on_admin_endpoints(
    client,
    db_session,
    method,
    path,
    body
):
    user, employee = create_employee(db_session)

    response = client.request(
        method,
        path,
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        },
        json=body if body is not None else None
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# An admin user is rejected by get_current_employee_user on employee-only
# endpoints even when an employee profile exists.
ADMIN_EMPLOYEE_ONLY_REQUESTS = [
    ("GET", "/attendance/me"),
    ("POST", "/attendance/check-in"),
    ("POST", "/attendance/check-out"),
]


@pytest.mark.parametrize(
    "method,path",
    ADMIN_EMPLOYEE_ONLY_REQUESTS
)
def test_admin_gets_403_on_employee_only_endpoints(
    client,
    db_session,
    method,
    path
):
    admin = create_admin(db_session)

    response = client.request(
        method,
        path,
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee access required"


def test_missing_token_vs_invalid_token_both_401(client):
    missing_response = client.get("/users/me")
    invalid_response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer garbage.token.here"}
    )

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401


def test_authenticated_admin_can_access_admin_endpoint(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }
    )

    assert response.status_code == 200


def test_authenticated_employee_can_access_self_service_endpoint(
    client,
    db_session
):
    user, employee = create_employee(db_session)

    response = client.get(
        "/leaves/me",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 200