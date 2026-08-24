from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.employee import Employee

from sqlalchemy import select

from datetime import date

import pytest


def create_admin(db_session):
    admin = User(
        email="admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def test_create_employee(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10001,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.com",
            "department": "IT",
            "position": "Software Engineer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_number"] == 10001
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@test.com"
    assert data["department"] == "IT"
    assert data["position"] == "Software Engineer"
    assert data["status"] == "active"

def test_employee_cannot_create_employee(client, db_session):
    employee = User(
        email="employee@test.com",
        password_hash=hash_password("employeepassword"),
        role="employee"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    token = create_access_token(employee.id)

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10002,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert response.status_code == 403

def test_create_duplicate_employee(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    employee_data = {
        "employee_number": 10003,
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@test.com",
        "department": "IT",
        "position": "Developer",
        "date_hired": "2026-08-24",
        "status": "active"
    }

    first_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=employee_data
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=employee_data
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Employee number or email already exists"
    )

def test_create_employee_account(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    employee_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10004,
            "first_name": "Account",
            "last_name": "Test",
            "email": "account.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert employee_response.status_code == 201

    employee_id = employee_response.json()["id"]

    response = client.post(
        f"/employees/{employee_id}/account",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "account.user@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "account.user@test.com"
    assert data["role"] == "employee"
    assert "id" in data

def test_create_duplicate_employee_account(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    employee_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10005,
            "first_name": "Account",
            "last_name": "Duplicate",
            "email": "duplicate.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = employee_response.json()["id"]

    account_data = {
        "email": "duplicate.account@test.com",
        "password": "testpassword123"
    }

    first_response = client.post(
        f"/employees/{employee_id}/account",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=account_data
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/employees/{employee_id}/account",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=account_data
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Employee already has a user account"
    )

def test_get_employees(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    client.post(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_number": 10006,
            "first_name": "Get",
            "last_name": "Employee",
            "email": "get.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    response = client.get(
        "/employees",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data
    assert data["total"] >= 1

def test_get_employee_by_id(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    create_response = client.post(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_number": 10007,
            "first_name": "Specific",
            "last_name": "Employee",
            "email": "specific.employee@test.com",
            "department": "Engineering",
            "position": "Software Engineer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = create_response.json()["id"]

    response = client.get(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == employee_id
    assert response.json()["email"] == "specific.employee@test.com"

def test_get_nonexistent_employee(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    response = client.get(
        "/employees/999999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"

def test_update_employee_put(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    create_response = client.post(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_number": 10008,
            "first_name": "Before",
            "last_name": "Update",
            "email": "before.update@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = create_response.json()["id"]

    response = client.put(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_number": 10008,
            "first_name": "After",
            "last_name": "Update",
            "email": "after.update@test.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "After"
    assert data["last_name"] == "Update"
    assert data["email"] == "after.update@test.com"
    assert data["department"] == "Engineering"
    assert data["position"] == "Senior Developer"

def test_patch_employee(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    create_response = client.post(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_number": 10009,
            "first_name": "Patch",
            "last_name": "Employee",
            "email": "patch.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = create_response.json()["id"]

    response = client.patch(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "department": "Engineering"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["department"] == "Engineering"
    assert data["first_name"] == "Patch"
    assert data["last_name"] == "Employee"
    assert data["email"] == "patch.employee@test.com"

def test_get_my_employee(client, db_session):
    employee_user = User(
        email="self.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(employee_user)
    db_session.commit()
    db_session.refresh(employee_user)

    admin = create_admin(db_session)
    admin_token = create_access_token(admin.id)

    employee_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "employee_number": 10010,
            "first_name": "Self",
            "last_name": "Employee",
            "email": "self.employee.profile@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = employee_response.json()["id"]

    # Connect the employee profile to the user.
    from app.models.employee import Employee

    employee = db_session.get(Employee, employee_id)
    employee.user_id = employee_user.id
    db_session.commit()

    token = create_access_token(employee_user.id)

    response = client.get(
        "/employees/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["id"] == employee_id
    assert response.json()["email"] == "self.employee.profile@test.com"

def test_update_my_employee(client, db_session):
    admin = create_admin(db_session)

    employee_user = User(
        email="selfupdate.user@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(employee_user)
    db_session.commit()
    db_session.refresh(employee_user)

    employee = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "employee_number": 10011,
            "first_name": "Original",
            "last_name": "Name",
            "email": "selfupdate.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    from app.models.employee import Employee

    employee_record = db_session.get(
        Employee,
        employee.json()["id"]
    )

    employee_record.user_id = employee_user.id
    db_session.commit()

    token = create_access_token(employee_user.id)

    response = client.patch(
        "/employees/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "first_name": "Updated",
            "last_name": "Self"
        }
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert response.json()["last_name"] == "Self"

def test_employee_cannot_access_other_employee(client, db_session):
    admin = create_admin(db_session)

    employee_user = User(
        email="employee.access@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(employee_user)
    db_session.commit()
    db_session.refresh(employee_user)

    admin_token = create_access_token(admin.id)

    employee_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "employee_number": 10012,
            "first_name": "Other",
            "last_name": "Employee",
            "email": "other.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = employee_response.json()["id"]

    token = create_access_token(employee_user.id)

    response = client.get(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only access your own employee profile"
    )

def test_deactivate_employee(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    create_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10013,
            "first_name": "Deactivate",
            "last_name": "Employee",
            "email": "deactivate.employee@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = create_response.json()["id"]

    response = client.delete(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "inactive"

def test_deactivate_employee_twice(client, db_session):
    admin = create_admin(db_session)

    token = create_access_token(admin.id)

    create_response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "employee_number": 10014,
            "first_name": "Already",
            "last_name": "Inactive",
            "email": "already.inactive@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    employee_id = create_response.json()["id"]

    first_response = client.delete(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert first_response.status_code == 200

    second_response = client.delete(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Employee is already inactive"
    )

def test_active_employee_can_access_own_profile(
    client,
    db_session
):
    from app.core.security import hash_password, create_access_token
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="lifecycle.active@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=91001,
        first_name="Lifecycle",
        last_name="Active",
        email="lifecycle.active.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.get(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["id"] == employee.id


def test_inactive_employee_cannot_access_own_profile(
    client,
    db_session
):
    from app.core.security import hash_password, create_access_token
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="lifecycle.inactive@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=91002,
        first_name="Lifecycle",
        last_name="Inactive",
        email="lifecycle.inactive.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="inactive"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.get(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee account is inactive"


def test_inactive_employee_cannot_access_employee_me(
    client,
    db_session
):
    from app.core.security import hash_password, create_access_token
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="lifecycle.me@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=91003,
        first_name="Lifecycle",
        last_name="Me",
        email="lifecycle.me.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="inactive"
    )

    db_session.add(employee)
    db_session.commit()

    response = client.get(
        "/employees/me",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee account is inactive"


def test_admin_can_deactivate_employee_and_employee_loses_access(
    client,
    db_session
):
    from app.core.security import hash_password, create_access_token
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="lifecycle.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    employee_user = User(
        email="lifecycle.deactivate@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add_all([admin, employee_user])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(employee_user)

    employee = Employee(
        user_id=employee_user.id,
        employee_number=91004,
        first_name="Lifecycle",
        last_name="Deactivate",
        email="lifecycle.deactivate.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    employee_token = create_access_token(employee_user.id)
    admin_token = create_access_token(admin.id)

    # Employee can access profile while active.
    response = client.get(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {employee_token}"
        }
    )

    assert response.status_code == 200

    # Admin deactivates employee.
    response = client.delete(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "inactive"

    # Existing JWT must no longer provide employee access.
    response = client.get(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {employee_token}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee account is inactive"


def test_admin_can_still_access_deactivated_employee(
    client,
    db_session
):
    from app.core.security import hash_password, create_access_token
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="lifecycle.admin.access@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    employee_user = User(
        email="lifecycle.deactivated.admin@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add_all([admin, employee_user])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(employee_user)

    employee = Employee(
        user_id=employee_user.id,
        employee_number=91005,
        first_name="Deactivated",
        last_name="Employee",
        email="lifecycle.deactivated.admin.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="inactive"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.get(
        f"/employees/{employee.id}",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["id"] == employee.id
    assert response.json()["status"] == "inactive"

def test_create_employee_account_links_user_and_employee(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="account.transaction.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    employee = Employee(
        employee_number=93001,
        first_name="Account",
        last_name="Transaction",
        email="account.transaction.employee@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        f"/employees/{employee.id}/account",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "email": "account.transaction.user@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "account.transaction.user@test.com"
    assert data["role"] == "employee"

    db_session.refresh(employee)

    assert employee.user_id is not None

    linked_user = db_session.scalar(
        select(User).where(
            User.id == employee.user_id
        )
    )

    assert linked_user is not None
    assert linked_user.email == "account.transaction.user@test.com"
    assert linked_user.role == "employee"


def test_create_employee_account_creates_audit_log(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.audit_log import AuditLog
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="account.audit.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    employee = Employee(
        employee_number=93002,
        first_name="Audit",
        last_name="Account",
        email="audit.account.employee@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        f"/employees/{employee.id}/account",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "email": "audit.account.user@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    audit_log = db_session.scalar(
        select(AuditLog).where(
            (AuditLog.action == "create")
            & (AuditLog.entity_type == "user")
            & (AuditLog.entity_id == user_id)
        )
    )

    assert audit_log is not None
    assert audit_log.user_id == admin.id


def test_cannot_create_duplicate_employee_account(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="duplicate.account.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    existing_user = User(
        email="existing.account@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add_all([admin, existing_user])
    db_session.commit()

    db_session.refresh(admin)
    db_session.refresh(existing_user)

    employee = Employee(
        user_id=existing_user.id,
        employee_number=93003,
        first_name="Already",
        last_name="Linked",
        email="already.linked@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        f"/employees/{employee.id}/account",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "email": "another.account@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Employee already has a user account"
    )


def test_cannot_create_account_for_inactive_employee(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="inactive.account.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    employee = Employee(
        employee_number=93004,
        first_name="Inactive",
        last_name="Account",
        email="inactive.account.employee@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="inactive"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        f"/employees/{employee.id}/account",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "email": "inactive.account.user@test.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot create an account for an inactive employee"
    )

def test_duplicate_employee_number_rejected(
    client,
    db_session
):
    from datetime import date
    from app.core.security import create_access_token, hash_password
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="constraint.employee.number.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    first = Employee(
        employee_number=94001,
        first_name="First",
        last_name="Employee",
        email="constraint.first@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(first)
    db_session.commit()

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "employee_number": 94001,
            "first_name": "Second",
            "last_name": "Employee",
            "email": "constraint.second@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert response.status_code == 409

def test_duplicate_employee_email_rejected(
    client,
    db_session
):
    from datetime import date
    from app.core.security import create_access_token, hash_password
    from app.models.employee import Employee
    from app.models.user import User

    admin = User(
        email="constraint.employee.email.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    first = Employee(
        employee_number=94002,
        first_name="First",
        last_name="Employee",
        email="constraint.shared@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(first)
    db_session.commit()

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        },
        json={
            "employee_number": 94003,
            "first_name": "Second",
            "last_name": "Employee",
            "email": "constraint.shared@test.com",
            "department": "IT",
            "position": "Developer",
            "date_hired": "2026-08-24",
            "status": "active"
        }
    )

    assert response.status_code == 409

def test_duplicate_attendance_same_employee_and_date_rejected(
    client,
    db_session
):
    from datetime import date, time
    from app.core.security import create_access_token, hash_password
    from app.models.attendance import Attendance
    from app.models.employee import Employee
    from app.models.user import User

    user = User(
        email="constraint.attendance@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        employee_number=94004,
        first_name="Attendance",
        last_name="Constraint",
        email="constraint.attendance.employee@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    attendance = Attendance(
        employee_id=employee.id,
        date=date(2026, 8, 24),
        time_in=time(8, 0),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    duplicate = Attendance(
        employee_id=employee.id,
        date=date(2026, 8, 24),
        time_in=time(9, 0),
        status="present"
    )

    db_session.add(duplicate)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    assert duplicate.id is None

def test_duplicate_leave_balance_type_rejected(
    db_session
):
    from app.models.employee import Employee
    from app.models.leave_balance import LeaveBalance
    from app.models.leave import LeaveType
    from sqlalchemy.exc import IntegrityError

    employee = Employee(
        employee_number=94005,
        first_name="Balance",
        last_name="Constraint",
        email="constraint.balance@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    first = LeaveBalance(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        total_days=15,
        used_days=0
    )

    db_session.add(first)
    db_session.commit()

    duplicate = LeaveBalance(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        total_days=15,
        used_days=0
    )

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    assert duplicate.id is None