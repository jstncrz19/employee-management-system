from datetime import date, timedelta

from app.core.security import create_access_token, hash_password
from app.core.time import now
from app.models.audit_log import AuditLog
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