from datetime import datetime, timedelta

from app.core.security import create_access_token, hash_password
from app.core.time import now
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.user import User


def create_admin(db_session):
    admin = User(
        email="admin@audit.test",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def create_employee(
    db_session,
    email="employee@audit.test",
    employee_number=40001
):
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
        employee_number=employee_number,
        first_name="Audit",
        last_name="Employee",
        email=f"profile.{email}",
        department="IT",
        position="Developer",
        date_hired=datetime(2026, 8, 1).date(),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return user, employee


def create_audit_log(
    db_session,
    user_id,
    action="create",
    entity_type="employee",
    entity_id=1,
    details="Test audit log",
    created_at=None
):
    if created_at is None:
        created_at = now()

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        created_at=created_at
    )

    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    return log


def token(user):
    return create_access_token(user.id)


# =========================================================
# BASIC ACCESS
# =========================================================

def test_get_audit_logs_empty(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["pages"] == 0


def test_employee_cannot_access_audit_logs(
    client,
    db_session
):
    user, employee = create_employee(db_session)

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_audit_log_requires_authentication(client):
    response = client.get("/audit-logs")

    assert response.status_code == 401


# =========================================================
# RESPONSE CONTENT
# =========================================================

def test_audit_log_response_contains_user_information(
    client,
    db_session
):
    admin = create_admin(db_session)

    log = create_audit_log(
        db_session,
        user_id=admin.id,
        action="create",
        entity_type="employee",
        entity_id=10,
        details="Created employee"
    )

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["id"] == log.id
    assert item["user_id"] == admin.id
    assert item["user_email"] == admin.email
    assert item["employee_id"] is None
    assert item["employee_name"] is None
    assert item["action"] == "create"
    assert item["entity_type"] == "employee"
    assert item["entity_id"] == 10
    assert item["details"] == "Created employee"


def test_audit_log_returns_employee_information(
    client,
    db_session
):
    user, employee = create_employee(db_session)

    log = create_audit_log(
        db_session,
        user_id=user.id,
        action="check_in",
        entity_type="attendance",
        entity_id=5,
        details="Checked in"
    )

    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    item = next(
        item for item in data["items"]
        if item["id"] == log.id
    )

    assert item["user_email"] == user.email
    assert item["employee_id"] == employee.id
    assert item["employee_name"] == "Audit Employee"


# =========================================================
# FILTERS
# =========================================================

def test_filter_by_user_id(client, db_session):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="filter.user@audit.test",
        employee_number=40002
    )

    create_audit_log(
        db_session,
        user_id=admin.id,
        action="create",
        entity_type="employee",
        entity_id=1
    )

    target_log = create_audit_log(
        db_session,
        user_id=user.id,
        action="check_in",
        entity_type="attendance",
        entity_id=2
    )

    response = client.get(
        f"/audit-logs?user_id={user.id}",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == target_log.id
    assert data["items"][0]["user_id"] == user.id


def test_filter_by_action(client, db_session):
    admin = create_admin(db_session)

    create_audit_log(
        db_session,
        admin.id,
        action="create",
        entity_type="employee"
    )

    target_log = create_audit_log(
        db_session,
        admin.id,
        action="approve",
        entity_type="leave"
    )

    response = client.get(
        "/audit-logs?action=approve",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == target_log.id
    assert data["items"][0]["action"] == "approve"


def test_filter_by_entity_type(client, db_session):
    admin = create_admin(db_session)

    create_audit_log(
        db_session,
        admin.id,
        action="create",
        entity_type="employee"
    )

    target_log = create_audit_log(
        db_session,
        admin.id,
        action="approve",
        entity_type="leave"
    )

    response = client.get(
        "/audit-logs?entity_type=leave",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == target_log.id
    assert data["items"][0]["entity_type"] == "leave"


def test_filter_by_start_date(client, db_session):
    admin = create_admin(db_session)

    today = now()

    old_log = create_audit_log(
        db_session,
        admin.id,
        action="old",
        created_at=today - timedelta(days=5)
    )

    new_log = create_audit_log(
        db_session,
        admin.id,
        action="new",
        created_at=today
    )

    start_date = today.date() - timedelta(days=1)

    response = client.get(
        f"/audit-logs?start_date={start_date.isoformat()}",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    ids = [item["id"] for item in data["items"]]

    assert new_log.id in ids
    assert old_log.id not in ids


def test_filter_by_end_date(client, db_session):
    admin = create_admin(db_session)

    today = now()

    old_log = create_audit_log(
        db_session,
        admin.id,
        action="old",
        created_at=today - timedelta(days=5)
    )

    new_log = create_audit_log(
        db_session,
        admin.id,
        action="new",
        created_at=today
    )

    end_date = today.date() - timedelta(days=1)

    response = client.get(
        f"/audit-logs?end_date={end_date.isoformat()}",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    ids = [item["id"] for item in data["items"]]

    assert old_log.id in ids
    assert new_log.id not in ids


def test_combined_filters(client, db_session):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="combined@audit.test",
        employee_number=40003
    )

    create_audit_log(
        db_session,
        user.id,
        action="create",
        entity_type="employee"
    )

    target_log = create_audit_log(
        db_session,
        user.id,
        action="approve",
        entity_type="leave"
    )

    create_audit_log(
        db_session,
        admin.id,
        action="approve",
        entity_type="leave"
    )

    response = client.get(
        f"/audit-logs?user_id={user.id}"
        f"&action=approve"
        f"&entity_type=leave",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == target_log.id


# =========================================================
# SORTING
# =========================================================

def test_sort_by_created_at_desc(client, db_session):
    admin = create_admin(db_session)

    first = create_audit_log(
        db_session,
        admin.id,
        action="first",
        created_at=now() - timedelta(minutes=2)
    )

    second = create_audit_log(
        db_session,
        admin.id,
        action="second",
        created_at=now()
    )

    response = client.get(
        "/audit-logs?sort_by=created_at&sort_order=desc",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["id"] == second.id
    assert data["items"][1]["id"] == first.id


def test_sort_by_created_at_asc(client, db_session):
    admin = create_admin(db_session)

    first = create_audit_log(
        db_session,
        admin.id,
        action="first",
        created_at=now() - timedelta(minutes=2)
    )

    second = create_audit_log(
        db_session,
        admin.id,
        action="second",
        created_at=now()
    )

    response = client.get(
        "/audit-logs?sort_by=created_at&sort_order=asc",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["id"] == first.id
    assert data["items"][1]["id"] == second.id


def test_sort_by_action_asc(client, db_session):
    admin = create_admin(db_session)

    approve = create_audit_log(
        db_session,
        admin.id,
        action="approve"
    )

    create = create_audit_log(
        db_session,
        admin.id,
        action="create"
    )

    response = client.get(
        "/audit-logs?sort_by=action&sort_order=asc",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["action"] == "approve"
    assert data["items"][1]["action"] == "create"


def test_sort_by_action_desc(client, db_session):
    admin = create_admin(db_session)

    approve = create_audit_log(
        db_session,
        admin.id,
        action="approve"
    )

    create = create_audit_log(
        db_session,
        admin.id,
        action="create"
    )

    response = client.get(
        "/audit-logs?sort_by=action&sort_order=desc",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["action"] == "create"
    assert data["items"][1]["action"] == "approve"


# =========================================================
# PAGINATION
# =========================================================

def test_audit_log_pagination(client, db_session):
    admin = create_admin(db_session)

    for index in range(5):
        create_audit_log(
            db_session,
            admin.id,
            action=f"action{index}"
        )

    response = client.get(
        "/audit-logs?page=1&limit=2",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 3


def test_audit_log_second_page(client, db_session):
    admin = create_admin(db_session)

    for index in range(5):
        create_audit_log(
            db_session,
            admin.id,
            action=f"action{index}"
        )

    response = client.get(
        "/audit-logs?page=2&limit=2",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2
    assert data["pages"] == 3


def test_audit_log_last_page(client, db_session):
    admin = create_admin(db_session)

    for index in range(5):
        create_audit_log(
            db_session,
            admin.id,
            action=f"action{index}"
        )

    response = client.get(
        "/audit-logs?page=3&limit=2",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 1
    assert data["page"] == 3
    assert data["pages"] == 3


# =========================================================
# VALIDATION
# =========================================================

def test_invalid_sort_by(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs?sort_by=invalid",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 422


def test_invalid_sort_order(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs?sort_order=invalid",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 422


def test_invalid_page(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs?page=0",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 422


def test_invalid_limit_zero(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs?limit=0",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 422


def test_limit_above_maximum(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/audit-logs?limit=101",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 422