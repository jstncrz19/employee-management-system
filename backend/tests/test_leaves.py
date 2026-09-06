from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.core.time import now
from app.models.audit_log import AuditLog
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.leave_balance import LeaveBalance
from app.models.user import User


def create_admin(db_session):
    admin = User(
        email="admin@leave.test",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def create_employee(
    db_session,
    email="employee@leave.test",
    employee_number=20001
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
        first_name="Leave",
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


def create_balance(
    db_session,
    employee_id,
    leave_type="vacation",
    total_days=20,
    used_days=0
):
    balance = LeaveBalance(
        employee_id=employee_id,
        leave_type=leave_type,
        total_days=total_days,
        used_days=used_days
    )

    db_session.add(balance)
    db_session.commit()
    db_session.refresh(balance)

    return balance


def employee_token(user):
    return create_access_token(user.id)


def admin_token(user):
    return create_access_token(user.id)


def leave_payload(
    start_date=None,
    end_date=None,
    leave_type="vacation",
    reason="Vacation"
):
    today = now().date()

    if start_date is None:
        start_date = today + timedelta(days=10)

    if end_date is None:
        end_date = start_date + timedelta(days=1)

    return {
        "leave_type": leave_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": reason
    }


# ---------------------------------------------------------
# CREATE LEAVE
# ---------------------------------------------------------

def test_create_leave(client, db_session):
    user, employee = create_employee(db_session)

    token = employee_token(user)

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload()
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"] == employee.id
    assert data["leave_type"] == "vacation"
    assert data["status"] == "pending"
    assert data["reason"] == "Vacation"


def test_create_leave_without_employee_profile(client, db_session):
    user = User(
        email="no.profile@leave.test",
        password_hash=hash_password("password"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = employee_token(user)

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload()
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee profile not found"


def test_inactive_employee_cannot_manage_own_leaves(client, db_session):
    user, employee = create_employee(
        db_session,
        email="inactive@leave.test",
        employee_number=20011
    )
    employee.status = "inactive"
    db_session.commit()

    headers = {"Authorization": f"Bearer {employee_token(user)}"}

    for method, path in [
        (client.post, "/leaves"),
        (client.get, "/leaves/me"),
        (client.get, "/leaves/balance/me"),
    ]:
        kwargs = {"headers": headers}
        if method == client.post:
            kwargs["json"] = leave_payload()

        response = method(path, **kwargs)

        assert response.status_code == 403
        assert response.json()["detail"] == "Employee account is inactive"


def test_create_leave_invalid_date_range(client, db_session):
    user, employee = create_employee(db_session)

    token = employee_token(user)

    today = now().date()

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=10)
        )
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "End date cannot be before start date"
    )


def test_create_overlapping_pending_leave(client, db_session):
    user, employee = create_employee(db_session)

    token = employee_token(user)

    first_start = now().date() + timedelta(days=10)
    first_end = first_start + timedelta(days=2)

    first_response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=first_start,
            end_date=first_end
        )
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=first_start + timedelta(days=1),
            end_date=first_end + timedelta(days=2)
        )
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Leave dates overlap with an existing leave request"
    )


def test_rejected_leave_does_not_block_overlap(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    rejected_leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=12),
        reason="Rejected",
        status=LeaveStatus.REJECTED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(rejected_leave)
    db_session.commit()

    token = employee_token(user)

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=today + timedelta(days=11),
            end_date=today + timedelta(days=13)
        )
    )

    assert response.status_code == 201


def test_cancelled_leave_does_not_block_overlap(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    cancelled_leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=12),
        reason="Cancelled",
        status=LeaveStatus.CANCELLED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(cancelled_leave)
    db_session.commit()

    token = employee_token(user)

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=today + timedelta(days=11),
            end_date=today + timedelta(days=13)
        )
    )

    assert response.status_code == 201


# ---------------------------------------------------------
# MY LEAVES / BALANCE
# ---------------------------------------------------------

def test_get_my_leaves(client, db_session):
    user, employee = create_employee(db_session)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=11),
        reason="My leave",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    token = employee_token(user)

    response = client.get(
        "/leaves/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["employee_id"] == employee.id


def test_admin_with_employee_profile_can_get_my_leaves(client, db_session):
    admin = create_admin(db_session)

    employee = Employee(
        user_id=admin.id,
        employee_number=20009,
        first_name="Admin",
        last_name="Profile",
        email="admin.profile@leave.test",
        department="IT",
        position="Manager",
        date_hired=date(2026, 8, 1),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=11),
        reason="Admin leave",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    token = admin_token(admin)

    response = client.get(
        "/leaves/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["employee_id"] == employee.id


def test_admin_without_employee_profile_gets_clear_error(client, db_session):
    admin = create_admin(db_session)

    token = admin_token(admin)

    response = client.get(
        "/leaves/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Admin account has no linked employee profile; "
        "a linked employee profile is required to use "
        "self-service features"
    )


def test_get_my_leave_balance(client, db_session):
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        leave_type="vacation",
        total_days=20,
        used_days=5
    )

    token = employee_token(user)

    response = client.get(
        "/leaves/balance/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["employee_id"] == employee.id
    assert data[0]["total_days"] == 20
    assert data[0]["used_days"] == 5
    assert data[0]["remaining_days"] == 15


# ---------------------------------------------------------
# APPROVAL
# ---------------------------------------------------------

def test_approve_leave(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=20,
        used_days=0
    )

    employee_token_value = employee_token(user)

    create_response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token_value}"
        },
        json=leave_payload(
            start_date=now().date() + timedelta(days=20),
            end_date=now().date() + timedelta(days=22)
        )
    )

    assert create_response.status_code == 201

    leave_id = create_response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "approved"

    balance = db_session.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee.id,
        LeaveBalance.leave_type == "vacation"
    ).first()

    assert balance.used_days == 3


def test_approve_leave_insufficient_balance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=2,
        used_days=0
    )

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload(
            start_date=now().date() + timedelta(days=20),
            end_date=now().date() + timedelta(days=22)
        )
    )

    assert response.status_code == 201

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert "Insufficient vacation leave balance" in (
        response.json()["detail"]
    )


def test_cannot_approve_leave_over_existing_attendance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(
        db_session,
        email="attendance.conflict@leave.test",
        employee_number=20013
    )
    create_balance(db_session, employee.id)

    leave_date = now().date() + timedelta(days=10)
    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=leave_date,
        end_date=leave_date,
        reason="Attendance conflict",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now(),
    )
    attendance = Attendance(
        employee_id=employee.id,
        date=leave_date,
        status="present",
    )
    db_session.add_all([leave, attendance])
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/approve",
        headers={"Authorization": f"Bearer {admin_token(admin)}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot approve leave that overlaps an attendance record"
    )


def test_approve_leave_without_balance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload()
    )

    assert response.status_code == 201

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave balance not found"


def test_cannot_approve_leave_for_inactive_employee(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(
        db_session,
        email="approval.inactive@leave.test",
        employee_number=20012
    )
    create_balance(db_session, employee.id)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=11),
        reason="Inactive employee leave",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now(),
    )
    employee.status = "inactive"
    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/approve",
        headers={"Authorization": f"Bearer {admin_token(admin)}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot approve leave for an inactive employee"
    )


def test_cannot_approve_non_pending_leave(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(db_session, employee.id)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=10),
        reason="Already approved",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only pending leave requests can be approved"
    )


# ---------------------------------------------------------
# REJECTION
# ---------------------------------------------------------

def test_reject_leave(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload()
    )

    assert response.status_code == 201

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/reject",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_cannot_reject_non_pending_leave(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=10),
        reason="Approved",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/reject",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only pending leave requests can be rejected"
    )


# ---------------------------------------------------------
# CANCELLATION
# ---------------------------------------------------------

def test_cancel_pending_leave(client, db_session):
    user, employee = create_employee(db_session)

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload()
    )

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/cancel",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_approved_leave_restores_balance(client, db_session):
    user, employee = create_employee(db_session)

    balance = create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=20,
        used_days=3
    )

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=12),
        reason="Approved leave",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/cancel",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    db_session.refresh(balance)

    assert balance.used_days == 0


def test_cannot_cancel_rejected_leave(client, db_session):
    user, employee = create_employee(db_session)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=10),
        reason="Rejected",
        status=LeaveStatus.REJECTED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/cancel",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only pending or approved leave requests can be cancelled"
    )


def test_employee_cannot_cancel_another_employee_leave(
    client,
    db_session
):
    user1, employee1 = create_employee(
        db_session,
        email="employee1@leave.test",
        employee_number=20002
    )

    user2, employee2 = create_employee(
        db_session,
        email="employee2@leave.test",
        employee_number=20003
    )

    leave = Leave(
        employee_id=employee1.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=10),
        reason="Private leave",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.patch(
        f"/leaves/{leave.id}/cancel",
        headers={
            "Authorization": f"Bearer {employee_token(user2)}"
        }
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# ADMIN LIST / FILTER / SORT / PAGINATION
# ---------------------------------------------------------

def test_admin_get_all_leaves(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=now().date() + timedelta(days=10),
        end_date=now().date() + timedelta(days=10),
        reason="Admin list",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/leaves",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == leave.id
    assert data["items"][0]["employee_number"] == employee.employee_number
    assert data["items"][0]["employee_name"] == "Leave Employee"


def test_employee_cannot_get_all_leaves(client, db_session):
    user, employee = create_employee(db_session)

    response = client.get(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_filter_leaves_by_status(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    db_session.add_all([
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=10),
            reason="Pending",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        ),
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.SICK,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=20),
            reason="Rejected",
            status=LeaveStatus.REJECTED,
            created_at=now(),
            updated_at=now()
        )
    ])

    db_session.commit()

    response = client.get(
        "/leaves?status=pending",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "pending"


def test_filter_leaves_by_employee(client, db_session):
    admin = create_admin(db_session)

    user1, employee1 = create_employee(
        db_session,
        email="filter1@leave.test",
        employee_number=20004
    )

    user2, employee2 = create_employee(
        db_session,
        email="filter2@leave.test",
        employee_number=20005
    )

    today = now().date()

    db_session.add_all([
        Leave(
            employee_id=employee1.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=10),
            reason="Employee 1",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        ),
        Leave(
            employee_id=employee2.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=20),
            reason="Employee 2",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        )
    ])

    db_session.commit()

    response = client.get(
        f"/leaves?employee_id={employee1.id}",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["employee_id"] == employee1.id


def test_filter_leaves_by_type(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    db_session.add_all([
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=10),
            reason="Vacation",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        ),
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.SICK,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=20),
            reason="Sick",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        )
    ])

    db_session.commit()

    response = client.get(
        "/leaves?leave_type=sick",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["leave_type"] == "sick"


def test_sort_leaves(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    first = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=10),
        reason="First",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    second = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.SICK,
        start_date=today + timedelta(days=20),
        end_date=today + timedelta(days=20),
        reason="Second",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add_all([first, second])
    db_session.commit()

    response = client.get(
        "/leaves?sort_by=start_date&sort_order=desc",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["id"] == second.id
    assert data["items"][1]["id"] == first.id


def test_invalid_sort_field(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?sort_by=invalid",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid sort field: invalid"


def test_invalid_sort_order(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?sort_by=id&sort_order=invalid",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "sort_order must be 'asc' or 'desc'"
    )


def test_leave_pagination(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    for index in range(3):
        db_session.add(
            Leave(
                employee_id=employee.id,
                leave_type=LeaveType.VACATION,
                start_date=today + timedelta(days=10 + index * 2),
                end_date=today + timedelta(days=10 + index * 2),
                reason=f"Leave {index}",
                status=LeaveStatus.PENDING,
                created_at=now(),
                updated_at=now()
            )
        )

    db_session.commit()

    response = client.get(
        "/leaves?page=1&limit=2",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 2


# ---------------------------------------------------------
# BALANCE UPDATE
# ---------------------------------------------------------

def test_update_leave_balance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=10,
        used_days=0
    )

    response = client.patch(
        f"/leaves/balance/{employee.id}/vacation",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        },
        json={
            "total_days": 20
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_days"] == 20
    assert data["used_days"] == 0
    assert data["remaining_days"] == 20


def test_update_balance_below_used_days(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=20,
        used_days=5
    )

    response = client.patch(
        f"/leaves/balance/{employee.id}/vacation",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        },
        json={
            "total_days": 3
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Total days cannot be less than used days"
    )


def test_employee_cannot_update_leave_balance(client, db_session):
    user, employee = create_employee(db_session)

    create_balance(db_session, employee.id)

    response = client.patch(
        f"/leaves/balance/{employee.id}/vacation",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json={
            "total_days": 30
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# ---------------------------------------------------------
# AUTHORIZATION / NOT FOUND
# ---------------------------------------------------------

def test_approve_leave_requires_admin(client, db_session):
    user, employee = create_employee(db_session)

    create_balance(db_session, employee.id)

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload()
    )

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/approve",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_reject_leave_requires_admin(client, db_session):
    user, employee = create_employee(db_session)

    response = client.post(
        "/leaves",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        },
        json=leave_payload()
    )

    leave_id = response.json()["id"]

    response = client.patch(
        f"/leaves/{leave_id}/reject",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_approve_nonexistent_leave(client, db_session):
    admin = create_admin(db_session)

    response = client.patch(
        "/leaves/999999/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave request not found"


# ---------------------------------------------------------
# AUDIT LOGS
# ---------------------------------------------------------

def test_leave_audit_logs(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=20,
        used_days=0
    )

    token = employee_token(user)

    create_response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json=leave_payload(
            start_date=now().date() + timedelta(days=30),
            end_date=now().date() + timedelta(days=31)
        )
    )

    assert create_response.status_code == 201

    leave_id = create_response.json()["id"]

    approve_response = client.patch(
        f"/leaves/{leave_id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert approve_response.status_code == 200

    logs = db_session.query(AuditLog).all()

    assert len(logs) == 2

    actions = {log.action for log in logs}

    assert "create" in actions
    assert "approve" in actions

    for log in logs:
        assert log.entity_type == "leave"
        assert log.entity_id == leave_id

def test_approve_leave_updates_leave_balance_and_audit_log(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.audit_log import AuditLog
    from app.models.employee import Employee
    from app.models.leave import Leave, LeaveStatus, LeaveType
    from app.models.leave_balance import LeaveBalance
    from app.models.user import User

    admin = User(
        email="transaction.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    employee_user = User(
        email="transaction.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add_all([admin, employee_user])
    db_session.commit()

    db_session.refresh(admin)
    db_session.refresh(employee_user)

    employee = Employee(
        user_id=employee_user.id,
        employee_number=92001,
        first_name="Transaction",
        last_name="Employee",
        email="transaction.employee.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    balance = LeaveBalance(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        total_days=15,
        used_days=0
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    balance.employee_id = employee.id
    db_session.add(balance)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
        reason="Transaction test",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)

    response = client.patch(
        f"/leaves/{leave.id}/approve",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }
    )

    assert response.status_code == 200

    db_session.refresh(leave)
    db_session.refresh(balance)

    assert leave.status == LeaveStatus.APPROVED
    assert balance.used_days == 3

    audit_log = db_session.scalar(
        select(AuditLog).where(
            (AuditLog.entity_type == "leave")
            & (AuditLog.entity_id == leave.id)
            & (AuditLog.action == "approve")
        )
    )

    assert audit_log is not None
    assert audit_log.user_id == admin.id


def test_cancel_approved_leave_restores_balance_and_creates_audit_log(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.audit_log import AuditLog
    from app.models.employee import Employee
    from app.models.leave import Leave, LeaveStatus, LeaveType
    from app.models.leave_balance import LeaveBalance
    from app.models.user import User

    employee_user = User(
        email="cancel.transaction@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add(employee_user)
    db_session.commit()
    db_session.refresh(employee_user)

    employee = Employee(
        user_id=employee_user.id,
        employee_number=92002,
        first_name="Cancel",
        last_name="Transaction",
        email="cancel.transaction.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    balance = LeaveBalance(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        total_days=15,
        used_days=3
    )

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
        reason="Cancellation transaction test",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add_all([balance, leave])
    db_session.commit()
    db_session.refresh(leave)
    db_session.refresh(balance)

    response = client.patch(
        f"/leaves/{leave.id}/cancel",
        headers={
            "Authorization": f"Bearer {create_access_token(employee_user.id)}"
        }
    )

    assert response.status_code == 200

    db_session.refresh(leave)
    db_session.refresh(balance)

    assert leave.status == LeaveStatus.CANCELLED
    assert balance.used_days == 0

    audit_log = db_session.scalar(
        select(AuditLog).where(
            (AuditLog.entity_type == "leave")
            & (AuditLog.entity_id == leave.id)
            & (AuditLog.action == "cancel")
        )
    )

    assert audit_log is not None
    assert audit_log.user_id == employee_user.id


def test_reject_leave_creates_audit_log_without_changing_balance(
    client,
    db_session
):
    from datetime import date

    from app.core.security import create_access_token, hash_password
    from app.models.audit_log import AuditLog
    from app.models.employee import Employee
    from app.models.leave import Leave, LeaveStatus, LeaveType
    from app.models.leave_balance import LeaveBalance
    from app.models.user import User

    admin = User(
        email="reject.transaction.admin@test.com",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    employee_user = User(
        email="reject.transaction.employee@test.com",
        password_hash=hash_password("testpassword123"),
        role="employee"
    )

    db_session.add_all([admin, employee_user])
    db_session.commit()

    db_session.refresh(admin)
    db_session.refresh(employee_user)

    employee = Employee(
        user_id=employee_user.id,
        employee_number=92003,
        first_name="Reject",
        last_name="Transaction",
        email="reject.transaction.profile@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 24),
        status="active"
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    balance = LeaveBalance(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        total_days=15,
        used_days=2
    )

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=date(2026, 9, 5),
        end_date=date(2026, 9, 6),
        reason="Reject transaction test",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add_all([balance, leave])
    db_session.commit()
    db_session.refresh(leave)

    response = client.patch(
        f"/leaves/{leave.id}/reject",
        headers={
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }
    )

    assert response.status_code == 200

    db_session.refresh(leave)
    db_session.refresh(balance)

    assert leave.status == LeaveStatus.REJECTED
    assert balance.used_days == 2

    audit_log = db_session.scalar(
        select(AuditLog).where(
            (AuditLog.entity_type == "leave")
            & (AuditLog.entity_id == leave.id)
            & (AuditLog.action == "reject")
        )
    )

    assert audit_log is not None
    assert audit_log.user_id == admin.id


# ---------------------------------------------------------
# EMPLOYEE LEAVE BALANCE (ADMIN)
# ---------------------------------------------------------

def test_admin_get_employee_leave_balance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    create_balance(
        db_session,
        employee.id,
        "vacation",
        total_days=20,
        used_days=5
    )

    create_balance(
        db_session,
        employee.id,
        "sick",
        total_days=10,
        used_days=2
    )

    response = client.get(
        f"/leaves/balance/{employee.id}",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    balances = {
        item["leave_type"]: item
        for item in data
    }

    assert balances["vacation"]["total_days"] == 20
    assert balances["vacation"]["used_days"] == 5
    assert balances["vacation"]["remaining_days"] == 15

    assert balances["sick"]["total_days"] == 10
    assert balances["sick"]["used_days"] == 2
    assert balances["sick"]["remaining_days"] == 8


def test_get_employee_leave_balance_missing_employee(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves/balance/999999",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_employee_cannot_get_other_employee_balance(client, db_session):
    user, employee = create_employee(db_session)

    response = client.get(
        f"/leaves/balance/{employee.id}",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# ---------------------------------------------------------
# ADMIN LEAVE LIST: DATE RANGE, SEARCH, VALIDATION
# ---------------------------------------------------------

def test_filter_leaves_by_date_range(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    db_session.add_all([
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=5),
            reason="Early",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        ),
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.SICK,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=20),
            reason="Late",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        )
    ])

    db_session.commit()

    start_date = today + timedelta(days=3)
    end_date = today + timedelta(days=7)

    response = client.get(
        f"/leaves?start_date={start_date.isoformat()}"
        f"&end_date={end_date.isoformat()}",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["reason"] == "Early"


def test_leaves_invalid_date_range(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?start_date=2026-09-10&end_date=2026-09-01",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "End date cannot be before start date"


def test_filter_leaves_by_search(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(
        db_session,
        email="searchleaf@leave.test",
        employee_number=20006
    )

    today = now().date()

    db_session.add(
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=10),
            reason="Searchable",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        )
    )

    db_session.commit()

    response = client.get(
        "/leaves?search=20006",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["employee_number"] == 20006


def test_leave_pagination_empty_page(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    today = now().date()

    db_session.add(
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=10),
            reason="Pager",
            status=LeaveStatus.PENDING,
            created_at=now(),
            updated_at=now()
        )
    )

    db_session.commit()

    response = client.get(
        "/leaves?page=5&limit=10",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 1
    assert data["page"] == 5


def test_leaves_unauthenticated(client):
    response = client.get("/leaves")

    assert response.status_code == 401


def test_leaves_invalid_page(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?page=0",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 422


def test_leaves_invalid_limit_above_maximum(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?limit=101",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 422


def test_leaves_invalid_status_filter(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/leaves?status=unknown",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# DEFENSIVE BRANCHES: NOT FOUND
# ---------------------------------------------------------

def test_cancel_nonexistent_leave(client, db_session):
    user, employee = create_employee(db_session)

    response = client.patch(
        "/leaves/999999/cancel",
        headers={
            "Authorization": f"Bearer {employee_token(user)}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave request not found"


def test_update_leave_balance_missing_employee(client, db_session):
    admin = create_admin(db_session)

    response = client.patch(
        "/leaves/balance/999999/vacation",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        },
        json={
            "total_days": 15
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_update_leave_balance_missing_balance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(
        db_session,
        email="nobalance@leave.test",
        employee_number=20007
    )

    response = client.patch(
        f"/leaves/balance/{employee.id}/vacation",
        headers={
            "Authorization": f"Bearer {admin_token(admin)}"
        },
        json={
            "total_days": 15
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave balance not found"
