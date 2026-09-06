import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User

from scripts.create_admin import create_initial_admin


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