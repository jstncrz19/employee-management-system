"""Create the initial admin account and, optionally, a linked employee profile.

This script is intended to be run inside the application container after
the database migrations have been applied.

Create a fresh admin account (optionally with a linked employee profile so
the admin can use self-service features such as "My Leaves"):

    docker compose exec backend python -m scripts.create_admin \
        --email admin@example.com \
        --password 'choose-a-strong-password' \
        --employee-number 10000 \
        --first-name Jane \
        --last-name Doe \
        --department Administration \
        --position Administrator \
        --date-hired 2026-09-01

If --password is omitted, the script prompts for it interactively.

Link an employee profile to an EXISTING admin account that has none (for
example, an admin created before this option existed):

    docker compose exec backend python -m scripts.create_admin \
        --link-existing \
        --email admin@example.com \
        --employee-number 10000 \
        --first-name Jane \
        --last-name Doe \
        --department Administration \
        --position Administrator \
        --date-hired 2026-09-01

--link-existing never creates or modifies the user account; --password is
not used in that mode. Employee information must always be provided
explicitly -- the script never invents a name, department, position, or
employee number from the admin's email address. The admin's email is reused
as the employee email, matching the self-registration flow.

The script refuses to create a second admin account. The regular
registration endpoint only ever creates employee accounts, so running this
script is the only way to obtain an admin account.
"""

import argparse
import getpass
import sys
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.employee import Employee
from app.models.leave_balance import LeaveBalance
from app.models.user import User

from database import SessionLocal

EMPLOYEE_FIELDS = (
    "employee_number",
    "first_name",
    "last_name",
    "department",
    "position",
    "date_hired",
)


def _validate_employee_data(employee_data: dict | None) -> None:
    if employee_data is None:
        return

    missing = [
        field for field in EMPLOYEE_FIELDS
        if employee_data.get(field) in (None, "")
    ]

    if missing:
        raise ValueError(
            "Missing employee profile fields: " + ", ".join(missing)
        )

    if not (
        isinstance(employee_data["employee_number"], int)
        and employee_data["employee_number"] > 0
    ):
        raise ValueError("employee_number must be a positive integer")

    if not isinstance(employee_data["date_hired"], date):
        raise ValueError("date_hired must be a valid date (YYYY-MM-DD)")

    for field in ("first_name", "last_name", "department", "position"):
        if not str(employee_data[field]).strip():
            raise ValueError(f"{field} must not be empty")


def _create_employee_with_balances(
    db: Session,
    *,
    user_id: int,
    email: str,
    employee_number: int,
    first_name: str,
    last_name: str,
    department: str,
    position: str,
    date_hired: date,
) -> Employee:
    employee = Employee(
        user_id=user_id,
        employee_number=employee_number,
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=department,
        position=position,
        date_hired=date_hired,
        status="active",
    )

    db.add(employee)
    db.flush()

    default_balances = [
        LeaveBalance(
            employee_id=employee.id,
            leave_type="vacation",
            total_days=15,
            used_days=0,
        ),
        LeaveBalance(
            employee_id=employee.id,
            leave_type="sick",
            total_days=15,
            used_days=0,
        ),
        LeaveBalance(
            employee_id=employee.id,
            leave_type="emergency",
            total_days=5,
            used_days=0,
        ),
        LeaveBalance(
            employee_id=employee.id,
            leave_type="other",
            total_days=0,
            used_days=0,
        ),
    ]

    db.add_all(default_balances)

    return employee


def create_initial_admin(
    db: Session,
    email: str,
    password: str,
    employee_data: dict | None = None,
) -> User:
    """Create the initial admin account.

    Refuses to run if an admin account already exists, the email is
    already in use, or the password is shorter than 8 characters.

    When ``employee_data`` is provided it must contain ``employee_number``,
    ``first_name``, ``last_name``, ``department``, ``position`` and
    ``date_hired``. A linked employee profile with default leave balances is
    then created in the same transaction; the admin's email is reused as the
    employee email.

    Raises:
        ValueError: if the password is too short or employee fields are missing/invalid.
        RuntimeError: if an admin already exists or the email / employee number is taken.
    """

    email = email.strip().lower()

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    existing_admin = db.scalar(
        select(User).where(User.role == "admin")
    )

    if existing_admin:
        raise RuntimeError(
            "An admin account already exists. "
            "This script only creates the first admin account."
        )

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise RuntimeError(
            f"Email is already in use: {email}"
        )

    _validate_employee_data(employee_data)

    if employee_data:
        existing_employee = db.scalar(
            select(Employee).where(
                (Employee.employee_number == employee_data["employee_number"])
                | (Employee.email == email)
            )
        )

        if existing_employee:
            raise RuntimeError(
                "Employee number or email already in use"
            )

    admin = User(
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )

    db.add(admin)

    try:
        db.flush()

        if employee_data:
            _create_employee_with_balances(
                db,
                user_id=admin.id,
                email=email,
                **employee_data,
            )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise RuntimeError("Email or employee number already in use")
    db.refresh(admin)

    return admin


def link_admin_profile(
    db: Session,
    email: str,
    employee_data: dict,
) -> Employee:
    """Link a new employee profile to an existing admin account.

    The admin user is never modified and no new user account is created.
    The admin's email is reused as the employee email.

    Raises:
        ValueError: if employee fields are missing or invalid.
        RuntimeError: if the user is not found / not an admin, if the admin
            already has a linked employee profile, or if the employee number
            or employee email is already in use.
    """
    email = email.strip().lower()

    _validate_employee_data(employee_data)

    admin = db.scalar(
        select(User).where(User.email == email)
    )

    if admin is None:
        raise RuntimeError(
            f"No user found for email: {email}"
        )

    if admin.role != "admin":
        raise RuntimeError(
            f"User {email} is not an admin account"
        )

    existing_profile = db.scalar(
        select(Employee).where(Employee.user_id == admin.id)
    )

    if existing_profile:
        raise RuntimeError(
            f"Admin account {email} already has a linked employee profile"
        )

    existing_employee = db.scalar(
        select(Employee).where(
            (Employee.employee_number == employee_data["employee_number"])
            | (Employee.email == email)
        )
    )

    if existing_employee:
        raise RuntimeError(
            "Employee number or email already in use"
        )

    employee = _create_employee_with_balances(
        db,
        user_id=admin.id,
        email=email,
        **employee_data,
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise RuntimeError("Employee number or email already in use")

    db.refresh(employee)

    return employee


def _build_employee_data(args) -> dict | None:
    values = {
        "employee_number": args.employee_number,
        "first_name": args.first_name,
        "last_name": args.last_name,
        "department": args.department,
        "position": args.position,
        "date_hired": args.date_hired,
    }

    if all(value is None for value in values.values()):
        return None

    return values


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create the initial admin account and, optionally, a linked "
            "employee profile, or link an employee profile to an existing "
            "admin account."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address for the admin account"
    )

    parser.add_argument(
        "--password",
        help=(
            "Admin password (prompted for interactively if omitted; "
            "not used with --link-existing)"
        )
    )

    parser.add_argument(
        "--link-existing",
        action="store_true",
        help=(
            "Link a new employee profile to the existing admin account "
            "with this email instead of creating a new admin account"
        )
    )

    parser.add_argument(
        "--employee-number",
        type=int,
        help="Employee number for the linked employee profile"
    )

    parser.add_argument(
        "--first-name",
        help="First name for the linked employee profile"
    )

    parser.add_argument(
        "--last-name",
        help="Last name for the linked employee profile"
    )

    parser.add_argument(
        "--department",
        help="Department for the linked employee profile"
    )

    parser.add_argument(
        "--position",
        help="Position for the linked employee profile"
    )

    parser.add_argument(
        "--date-hired",
        type=date.fromisoformat,
        help="Hire date for the linked employee profile (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    employee_data = _build_employee_data(args)

    db = SessionLocal()

    try:
        if args.link_existing:
            if employee_data is None:
                raise ValueError(
                    "--link-existing requires the employee profile fields"
                )

            employee = link_admin_profile(
                db,
                email=args.email,
                employee_data=employee_data,
            )

            print(
                f"Linked employee profile (Employee #{employee.employee_number}) "
                f"to admin account {args.email}"
            )
        else:
            password = args.password or getpass.getpass("Admin password: ")

            admin = create_initial_admin(
                db,
                email=args.email,
                password=password,
                employee_data=employee_data,
            )

            if employee_data:
                employee = db.scalar(
                    select(Employee).where(Employee.user_id == admin.id)
                )

                print(
                    f"Admin account created for {admin.email} with linked "
                    f"employee profile (Employee #{employee.employee_number})"
                )
            else:
                print(f"Admin account created for {admin.email}")
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())