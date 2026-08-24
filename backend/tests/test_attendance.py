from datetime import date, timedelta
from app.core.time import now

from app.core.security import create_access_token, hash_password
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.user import User



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


def create_employee(db_session, email="employee@test.com"):
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
        employee_number=10001,
        first_name="Test",
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


def create_employee_token(user):
    return create_access_token(user.id)


def test_check_in(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"] == employee.id
    assert data["date"] == now().date().isoformat()
    assert data["time_in"] is not None
    assert data["time_out"] is None
    assert data["status"] == "present"


def test_duplicate_check_in(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    first_response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Already checked in today"


def test_check_out(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    check_in_response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert check_in_response.status_code == 201

    response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == employee.id
    assert data["time_in"] is not None
    assert data["time_out"] is not None
    assert data["status"] == "present"


def test_check_out_without_check_in(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You have not checked in today"


def test_duplicate_check_out(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    first_response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Already checked out today"


def test_check_in_on_approved_leave(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Vacation",
        status=LeaveStatus.APPROVED,
        created_at=__import__("app.core.time", fromlist=["now"]).now(),
        updated_at=__import__("app.core.time", fromlist=["now"]).now()
    )

    db_session.add(leave)
    db_session.commit()

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You are on approved leave today"


def test_check_out_on_approved_leave(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    attendance = Attendance(
        employee_id=employee.id,
        date=today,
        time_in=__import__("datetime").datetime.now().time(),
        status="present"
    )

    db_session.add(attendance)

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Vacation",
        status=LeaveStatus.APPROVED,
        created_at=__import__("app.core.time", fromlist=["now"]).now(),
        updated_at=__import__("app.core.time", fromlist=["now"]).now()
    )

    db_session.add(leave)
    db_session.commit()

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You are on approved leave today"


def test_check_in_with_pending_leave(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Pending vacation",
        status=LeaveStatus.PENDING,
        created_at=__import__("app.core.time", fromlist=["now"]).now(),
        updated_at=__import__("app.core.time", fromlist=["now"]).now()
    )

    db_session.add(leave)
    db_session.commit()

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201


def test_check_in_with_rejected_leave(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Rejected vacation",
        status=LeaveStatus.REJECTED,
        created_at=__import__("app.core.time", fromlist=["now"]).now(),
        updated_at=__import__("app.core.time", fromlist=["now"]).now()
    )

    db_session.add(leave)
    db_session.commit()

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201


def test_check_in_with_cancelled_leave(client, db_session):
    user, employee = create_employee(db_session)

    today = now().date()

    leave = Leave(
        employee_id=employee.id,
        leave_type=LeaveType.VACATION,
        start_date=today,
        end_date=today,
        reason="Cancelled vacation",
        status=LeaveStatus.CANCELLED,
        created_at=__import__("app.core.time", fromlist=["now"]).now(),
        updated_at=__import__("app.core.time", fromlist=["now"]).now()
    )

    db_session.add(leave)
    db_session.commit()

    token = create_employee_token(user)

    response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201


def test_get_my_attendance(client, db_session):
    user, employee = create_employee(db_session)

    attendance = Attendance(
        employee_id=employee.id,
        date=now().date(),
        time_in=__import__("datetime").datetime.now().time(),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    token = create_employee_token(user)

    response = client.get(
        "/attendance/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["employee_id"] == employee.id


def test_employee_cannot_access_admin_attendance(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    response = client.get(
        "/attendance",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_get_all_attendance(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    attendance = Attendance(
        employee_id=employee.id,
        date=now().date(),
        time_in=__import__("datetime").datetime.now().time(),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    token = create_access_token(admin.id)

    response = client.get(
        "/attendance",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["employee_id"] == employee.id


def test_admin_filter_attendance_by_employee(client, db_session):
    admin = create_admin(db_session)

    user1, employee1 = create_employee(
        db_session,
        email="employee1@test.com"
    )

    user2 = User(
        email="employee2@test.com",
        password_hash=hash_password("employeepassword"),
        role="employee"
    )

    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user2)

    employee2 = Employee(
        user_id=user2.id,
        employee_number=10002,
        first_name="Second",
        last_name="Employee",
        email="profile.employee2@test.com",
        department="IT",
        position="Developer",
        date_hired=date(2026, 8, 1),
        status="active"
    )

    db_session.add(employee2)
    db_session.commit()

    db_session.add_all([
        Attendance(
            employee_id=employee1.id,
            date=now().date(),
            time_in=__import__("datetime").datetime.now().time(),
            status="present"
        ),
        Attendance(
            employee_id=employee2.id,
            date=now().date() - timedelta(days=1),
            time_in=__import__("datetime").datetime.now().time(),
            status="present"
        )
    ])

    db_session.commit()

    token = create_access_token(admin.id)

    response = client.get(
        f"/attendance?employee_id={employee1.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["employee_id"] == employee1.id


def test_admin_filter_attendance_by_date(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    target_date = now().date() - timedelta(days=1)

    attendance = Attendance(
        employee_id=employee.id,
        date=target_date,
        time_in=__import__("datetime").datetime.now().time(),
        status="present"
    )

    db_session.add(attendance)
    db_session.commit()

    token = create_access_token(admin.id)

    response = client.get(
        f"/attendance?date={target_date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["date"] == target_date.isoformat()


def test_admin_attendance_pagination(client, db_session):
    admin = create_admin(db_session)
    user, employee = create_employee(db_session)

    for days_ago in range(3):
        db_session.add(
            Attendance(
                employee_id=employee.id,
                date=now().date() - timedelta(days=days_ago),
                time_in=__import__("datetime").datetime.now().time(),
                status="present"
            )
        )

    db_session.commit()

    token = create_access_token(admin.id)

    response = client.get(
        "/attendance?page=1&limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 2


def test_attendance_audit_logs(client, db_session):
    user, employee = create_employee(db_session)

    token = create_employee_token(user)

    check_in_response = client.post(
        "/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert check_in_response.status_code == 201

    check_out_response = client.post(
        "/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert check_out_response.status_code == 200

    from app.models.audit_log import AuditLog

    logs = db_session.query(AuditLog).all()

    assert len(logs) == 2

    actions = {log.action for log in logs}

    assert "check_in" in actions
    assert "check_out" in actions

    for log in logs:
        assert log.user_id == user.id
        assert log.entity_type == "attendance"
        assert log.entity_id == check_in_response.json()["id"]

