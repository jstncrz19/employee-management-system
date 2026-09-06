"""Create the initial admin account for a fresh installation.

This script is intended to be run inside the application container after
the database migrations have been applied:

    docker compose exec backend python -m scripts.create_admin \
        --email admin@example.com \
        --password 'choose-a-strong-password'

If --password is omitted, the script prompts for it interactively.

The script refuses to run when an admin account already exists. The
regular registration endpoint only ever creates employee accounts, so
running this script is the only way to obtain an admin account.
"""

import argparse
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User

from database import SessionLocal


def create_initial_admin(db: Session, email: str, password: str) -> User:
    """Create the initial admin account.

    Refuses to run if an admin account already exists, the email is
    already in use, or the password is shorter than 8 characters.

    Raises:
        ValueError: if the password is too short.
        RuntimeError: if an admin already exists or the email is taken.
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

    admin = User(
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create the initial admin account for a fresh installation."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address for the admin account"
    )

    parser.add_argument(
        "--password",
        help="Admin password (prompted for interactively if omitted)"
    )

    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")

    db = SessionLocal()

    try:
        admin = create_initial_admin(
            db,
            email=args.email,
            password=password,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Admin account created for {admin.email}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())