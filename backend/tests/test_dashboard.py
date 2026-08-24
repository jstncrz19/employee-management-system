from datetime import date, timedelta, time

from app.core.security import create_access_token, hash_password
from app.core.time import now
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.leave_balance import LeaveBalance
from app.models.user import User


def create_admin(db_session):
    admin = User(
        email="admin@dashboard.test",
        password_hash=hash_password("adminpassword"),
        role="admin"
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin


def create_employee(
    db_session,
    email="employee@dashboard.test",
    employee_number=30001,
    status="active"
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
        first_name="Dashboard",
        last_name="Employee",
        email=f"profile.{email}",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 1),
        status=status
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return user, employee


def token(user):
    return create_access_token(user.id)


def create_balance(
    db_session,
    employee_id,
    leave_type="vacation",
    total_days=20,
    used_days=5
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


# =========================================================
# ADMIN SUMMARY
# =========================================================

def test_dashboard_summary_empty(client, db_session):
    admin = create_admin(db_session)

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_employees"] == 0
    assert data["active_employees"] == 0
    assert data["present_today"] == 0
    assert data["absent_today"] == 0
    assert data["on_leave_today"] == 0
    assert data["pending_leave_requests"] == 0


def test_dashboard_summary_counts_active_and_inactive(
    client,
    db_session
):
    admin = create_admin(db_session)

    create_employee(
        db_session,
        email="active1@dashboard.test",
        employee_number=30002,
        status="active"
    )

    create_employee(
        db_session,
        email="active2@dashboard.test",
        employee_number=30003,
        status="active"
    )

    create_employee(
        db_session,
        email="inactive@dashboard.test",
        employee_number=30004,
        status="inactive"
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_employees"] == 3
    assert data["active_employees"] == 2


def test_dashboard_summary_present_today(client, db_session):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="present@dashboard.test",
        employee_number=30005
    )

    attendance = Attendance(
        employee_id=employee.id,
        date=now().date(),
        time_in=time(8, 0),
        time_out=time(17, 0),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["present_today"] == 1
    assert data["on_leave_today"] == 0
    assert data["absent_today"] == 0


def test_dashboard_summary_on_leave_today(client, db_session):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="leave@dashboard.test",
        employee_number=30006
    )

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="On leave",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["on_leave_today"] == 1
    assert data["present_today"] == 0
    assert data["absent_today"] == 0


def test_dashboard_summary_absent_today(client, db_session):
    admin = create_admin(db_session)

    create_employee(
        db_session,
        email="absent@dashboard.test",
        employee_number=30007
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["active_employees"] == 1
    assert data["present_today"] == 0
    assert data["on_leave_today"] == 0
    assert data["absent_today"] == 1


def test_dashboard_summary_pending_leaves(client, db_session):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="pending@dashboard.test",
        employee_number=30008
    )

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=5),
        end_date=today + timedelta(days=6),
        reason="Pending",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200
    assert response.json()["pending_leave_requests"] == 1


def test_dashboard_ignores_inactive_employee_attendance(
    client,
    db_session
):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="inactive.attendance@dashboard.test",
        employee_number=30009,
        status="inactive"
    )

    attendance = Attendance(
        employee_id=employee.id,
        date=now().date(),
        time_in=time(8, 0),
        time_out=time(17, 0),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_employees"] == 1
    assert data["active_employees"] == 0
    assert data["present_today"] == 0
    assert data["absent_today"] == 0


def test_dashboard_ignores_inactive_employee_leave(
    client,
    db_session
):
    admin = create_admin(db_session)

    user, employee = create_employee(
        db_session,
        email="inactive.leave@dashboard.test",
        employee_number=30010,
        status="inactive"
    )

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Inactive leave",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["active_employees"] == 0
    assert data["on_leave_today"] == 0
    assert data["absent_today"] == 0


def test_dashboard_summary_mixed_attendance_and_leave(
    client,
    db_session
):
    admin = create_admin(db_session)

    # Present employee
    _, present_employee = create_employee(
        db_session,
        email="mixed.present@dashboard.test",
        employee_number=30011
    )

    db_session.add(
        Attendance(
            employee_id=present_employee.id,
            date=now().date(),
            time_in=time(8, 0),
            time_out=time(17, 0),
            status="present"
        )
    )

    # Employee on approved leave
    _, leave_employee = create_employee(
        db_session,
        email="mixed.leave@dashboard.test",
        employee_number=30012
    )

    today = now().date()

    db_session.add(
        Leave(
            employee_id=leave_employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today,
            end_date=today,
            reason="Leave",
            status=LeaveStatus.APPROVED,
            created_at=now(),
            updated_at=now()
        )
    )

    # Absent employee
    create_employee(
        db_session,
        email="mixed.absent@dashboard.test",
        employee_number=30013
    )

    db_session.commit()

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["active_employees"] == 3
    assert data["present_today"] == 1
    assert data["on_leave_today"] == 1
    assert data["absent_today"] == 1


def test_employee_cannot_access_dashboard_summary(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="employee.summary@dashboard.test",
        employee_number=30014
    )

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

def test_employee_dashboard_empty(client, db_session):
    user, employee = create_employee(
        db_session,
        email="empty.dashboard@dashboard.test",
        employee_number=30015
    )

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["attendance_today"] is None
    assert data["leave_balances"] == []
    assert data["pending_leaves"] == []
    assert data["upcoming_leaves"] == []
    assert data["recent_attendance"] == []


def test_employee_dashboard_attendance_today(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="attendance.dashboard@dashboard.test",
        employee_number=30016
    )

    today = now().date()

    db_session.add(
        Attendance(
            employee_id=employee.id,
            date=today,
            time_in=time(8, 15),
            time_out=time(17, 5),
            status="present"
        )
    )

    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["attendance_today"] is not None
    assert data["attendance_today"]["date"] == today.isoformat()
    assert data["attendance_today"]["time_in"] == "08:15:00"
    assert data["attendance_today"]["time_out"] == "17:05:00"
    assert data["attendance_today"]["status"] == "present"


def test_employee_dashboard_leave_balances(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="balance.dashboard@dashboard.test",
        employee_number=30017
    )

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
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["leave_balances"]) == 2

    balances = {
        item["leave_type"]: item
        for item in data["leave_balances"]
    }

    assert balances["vacation"]["total_days"] == 20
    assert balances["vacation"]["used_days"] == 5
    assert balances["vacation"]["remaining_days"] == 15

    assert balances["sick"]["total_days"] == 10
    assert balances["sick"]["used_days"] == 2
    assert balances["sick"]["remaining_days"] == 8


def test_employee_dashboard_pending_leaves(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="pending.dashboard@dashboard.test",
        employee_number=30018
    )

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=5),
        end_date=today + timedelta(days=7),
        reason="Pending dashboard leave",
        status=LeaveStatus.PENDING,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["pending_leaves"]) == 1
    assert data["pending_leaves"][0]["id"] == leave.id
    assert data["pending_leaves"][0]["status"] == "pending"


def test_employee_dashboard_upcoming_approved_leave(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="upcoming.dashboard@dashboard.test",
        employee_number=30019
    )

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=12),
        reason="Upcoming",
        status=LeaveStatus.APPROVED,
        created_at=now(),
        updated_at=now()
    )

    db_session.add(leave)
    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["upcoming_leaves"]) == 1
    assert data["upcoming_leaves"][0]["id"] == leave.id
    assert data["upcoming_leaves"][0]["status"] == "approved"


def test_employee_dashboard_does_not_show_rejected_or_cancelled_leaves(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="excluded.leaves@dashboard.test",
        employee_number=30020
    )

    today = now().date()

    db_session.add_all([
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.VACATION,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=6),
            reason="Rejected",
            status=LeaveStatus.REJECTED,
            created_at=now(),
            updated_at=now()
        ),
        Leave(
            employee_id=employee.id,
            leave_type=LeaveType.SICK,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=11),
            reason="Cancelled",
            status=LeaveStatus.CANCELLED,
            created_at=now(),
            updated_at=now()
        )
    ])

    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pending_leaves"] == []
    assert data["upcoming_leaves"] == []


def test_employee_dashboard_recent_attendance(
    client,
    db_session
):
    user, employee = create_employee(
        db_session,
        email="recent.attendance@dashboard.test",
        employee_number=30021
    )

    today = now().date()

    for index in range(7):
        attendance_date = today - timedelta(days=index)

        db_session.add(
            Attendance(
                employee_id=employee.id,
                date=attendance_date,
                time_in=time(8, 0),
                time_out=time(17, 0),
                status="present"
            )
        )

    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["recent_attendance"]) == 5

    dates = [
        item["date"]
        for item in data["recent_attendance"]
    ]

    assert dates == sorted(dates, reverse=True)


def test_employee_dashboard_only_returns_own_data(
    client,
    db_session
):
    user1, employee1 = create_employee(
        db_session,
        email="own.dashboard@dashboard.test",
        employee_number=30022
    )

    user2, employee2 = create_employee(
        db_session,
        email="other.dashboard@dashboard.test",
        employee_number=30023
    )

    create_balance(
        db_session,
        employee2.id,
        "vacation",
        total_days=30,
        used_days=10
    )

    db_session.add(
        Attendance(
            employee_id=employee2.id,
            date=now().date(),
            time_in=time(8, 0),
            time_out=time(17, 0),
            status="present"
        )
    )

    db_session.commit()

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user1)}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["attendance_today"] is None
    assert data["leave_balances"] == []
    assert data["pending_leaves"] == []
    assert data["upcoming_leaves"] == []
    assert data["recent_attendance"] == []


def test_admin_can_access_employee_dashboard(
    client,
    db_session
):
    admin = create_admin(db_session)

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(admin)}"
        }
    )

    assert response.status_code == 404


def test_employee_dashboard_requires_employee_profile(
    client,
    db_session
):
    user = User(
        email="no.profile.dashboard@dashboard.test",
        password_hash=hash_password("password"),
        role="employee"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.get(
        "/dashboard/me",
        headers={
            "Authorization": f"Bearer {token(user)}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee profile not found"