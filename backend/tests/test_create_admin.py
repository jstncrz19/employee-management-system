import pytest
from datetime import date

from sqlalchemy import func, select

from app.core.security import verify_password
from app.models.user import User
from app.models.employee import Employee
from app.models.leave_balance import LeaveBalance

from scripts.create_admin import create_initial_admin, link_admin_profile


EMPLOYEE_DATA = {
    "employee_number": 12345,
    "first_name": "Jane",
    "last_name": "Doe",
    "department": "Administration",
    "position": "Administrator",
    "date_hired": date(2026, 9, 1),
}


def _add_user(db_session, email="admin@example.com", role="admin"):
    user = User(
        email=email,
        password_hash="hashed",
        role=role,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def _add_employee(db_session, employee_number, email):
    employee = Employee(
        employee_number=employee_number,
        first_name="First",
        last_name="Last",
        email=email,
        department="IT",
        position="Staff",
        date_hired=date(2026, 1, 1),
        status="active",
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


def test_create_initial_admin_creates_account(client, db_session):
    admin = create_initial_admin(
        db_session,
        email="root.admin@example.com",
        password="StrongAdminPass1",
    )

    db_session.refresh(admin)

    assert admin.id is not None
    assert admin.role == "admin"
    assert admin.email == "root.admin@example.com"
    assert verify_password("StrongAdminPass1", admin.password_hash)

    created = db_session.scalar(
        select(User).where(User.email == "root.admin@example.com")
    )

    assert created is not None
    assert created.role == "admin"


def test_create_initial_admin_normalizes_email(client, db_session):
    admin = create_initial_admin(
        db_session,
        email="  ROOT.ADMIN@Example.COM  ",
        password="StrongAdminPass1",
    )

    assert admin.email == "root.admin@example.com"


def test_create_initial_admin_rejects_second_admin(client, db_session):
    create_initial_admin(
        db_session,
        email="first.admin@example.com",
        password="StrongAdminPass1",
    )

    with pytest.raises(RuntimeError, match="admin account already exists"):
        create_initial_admin(
            db_session,
            email="second.admin@example.com",
            password="StrongAdminPass1",
        )


def test_create_initial_admin_rejects_existing_email(client, db_session):
    user = User(
        email="existing.user@example.com",
        password_hash="hashed",
        role="employee",
    )

    db_session.add(user)
    db_session.commit()

    with pytest.raises(RuntimeError, match="already in use"):
        create_initial_admin(
            db_session,
            email="existing.user@example.com",
            password="StrongAdminPass1",
        )


def test_create_initial_admin_rejects_short_password(client, db_session):
    with pytest.raises(ValueError, match="at least 8 characters"):
        create_initial_admin(
            db_session,
            email="root.admin@example.com",
            password="short",
        )


def test_create_initial_admin_without_profile_does_not_create_employee(
    client, db_session
):
    admin = create_initial_admin(
        db_session,
        email="root.admin@example.com",
        password="StrongAdminPass1",
    )

    employee = db_session.scalar(
        select(Employee).where(Employee.user_id == admin.id)
    )

    assert employee is None


def test_create_initial_admin_with_profile_links_employee(client, db_session):
    admin = create_initial_admin(
        db_session,
        email="root.admin@example.com",
        password="StrongAdminPass1",
        employee_data=EMPLOYEE_DATA,
    )

    employee = db_session.scalar(
        select(Employee).where(Employee.user_id == admin.id)
    )

    assert employee is not None
    assert employee.email == admin.email
    assert employee.first_name == "Jane"
    assert employee.last_name == "Doe"
    assert employee.department == "Administration"
    assert employee.position == "Administrator"
    assert employee.date_hired == date(2026, 9, 1)
    assert employee.status == "active"

    balances = db_session.scalars(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id
        )
    ).all()

    assert len(balances) == 4
    assert {balance.leave_type: balance.total_days for balance in balances} == {
        "vacation": 15,
        "sick": 15,
        "emergency": 5,
        "other": 0,
    }


def test_create_initial_admin_requires_employee_fields(client, db_session):
    with pytest.raises(ValueError, match="Missing employee profile fields"):
        create_initial_admin(
            db_session,
            email="root.admin@example.com",
            password="StrongAdminPass1",
            employee_data={"employee_number": 12345},
        )


def test_create_initial_admin_rejects_invalid_employee_number(
    client, db_session
):
    with pytest.raises(ValueError, match="positive integer"):
        create_initial_admin(
            db_session,
            email="root.admin@example.com",
            password="StrongAdminPass1",
            employee_data={**EMPLOYEE_DATA, "employee_number": 0},
        )


def test_create_initial_admin_rejects_duplicate_employee_number(
    client, db_session
):
    _add_employee(
        db_session,
        employee_number=EMPLOYEE_DATA["employee_number"],
        email="other@example.com",
    )

    with pytest.raises(RuntimeError, match="already in use"):
        create_initial_admin(
            db_session,
            email="root.admin@example.com",
            password="StrongAdminPass1",
            employee_data=EMPLOYEE_DATA,
        )

    assert db_session.scalar(
        select(User).where(User.email == "root.admin@example.com")
    ) is None

    employees = db_session.scalars(select(Employee)).all()
    assert len(employees) == 1


def test_link_admin_profile_links_existing_admin_without_new_user(
    client, db_session
):
    _add_user(db_session, email="admin@example.com")

    employee = link_admin_profile(
        db_session,
        email="admin@example.com",
        employee_data=EMPLOYEE_DATA,
    )

    user_count = db_session.scalar(
        select(func.count())
        .select_from(User)
        .where(User.email == "admin@example.com")
    )

    assert user_count == 1

    admin = db_session.scalar(
        select(User).where(User.email == "admin@example.com")
    )

    assert admin.role == "admin"

    employee_loaded = db_session.scalar(
        select(Employee).where(Employee.user_id == admin.id)
    )

    assert employee_loaded.id == employee.id
    assert employee_loaded.email == admin.email
    assert employee_loaded.status == "active"

    balances = db_session.scalars(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id
        )
    ).all()

    assert len(balances) == 4


def test_link_admin_profile_rejects_when_already_linked(client, db_session):
    admin = _add_user(db_session, email="admin@example.com")

    employee = _add_employee(
        db_session,
        employee_number=EMPLOYEE_DATA["employee_number"],
        email="admin@example.com",
    )

    employee.user_id = admin.id
    db_session.commit()

    with pytest.raises(
        RuntimeError, match="already has a linked employee profile"
    ):
        link_admin_profile(
            db_session,
            email="admin@example.com",
            employee_data=EMPLOYEE_DATA,
        )


def test_link_admin_profile_rejects_duplicate_employee_number(
    client, db_session
):
    _add_user(db_session, email="admin@example.com")

    _add_employee(
        db_session,
        employee_number=EMPLOYEE_DATA["employee_number"],
        email="other@example.com",
    )

    with pytest.raises(RuntimeError, match="already in use"):
        link_admin_profile(
            db_session,
            email="admin@example.com",
            employee_data=EMPLOYEE_DATA,
        )

    employees = db_session.scalars(select(Employee)).all()
    assert len(employees) == 1


def test_link_admin_profile_rejects_duplicate_email(client, db_session):
    _add_user(db_session, email="admin@example.com")

    _add_employee(
        db_session,
        employee_number=99999,
        email="admin@example.com",
    )

    with pytest.raises(RuntimeError, match="already in use"):
        link_admin_profile(
            db_session,
            email="admin@example.com",
            employee_data={**EMPLOYEE_DATA, "employee_number": 99998},
        )

    employees = db_session.scalars(select(Employee)).all()
    assert len(employees) == 1


def test_link_admin_profile_rejects_missing_admin(client, db_session):
    with pytest.raises(RuntimeError, match="No user found"):
        link_admin_profile(
            db_session,
            email="missing@example.com",
            employee_data=EMPLOYEE_DATA,
        )


def test_link_admin_profile_rejects_non_admin_user(client, db_session):
    _add_user(db_session, email="employee@example.com", role="employee")

    with pytest.raises(RuntimeError, match="not an admin"):
        link_admin_profile(
            db_session,
            email="employee@example.com",
            employee_data=EMPLOYEE_DATA,
        )


def test_link_admin_profile_requires_employee_fields(client, db_session):
    _add_user(db_session, email="admin@example.com")

    with pytest.raises(ValueError, match="Missing employee profile fields"):
        link_admin_profile(
            db_session,
            email="admin@example.com",
            employee_data={"employee_number": 12345},
        )