from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password
)
from app.models.user import User
from app.models.employee import Employee
from app.models.leave_balance import LeaveBalance
from app.schemas.auth import Token, UserRegister, UserResponse
from database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    existing_employee = db.scalar(
        select(Employee).where(
            (Employee.employee_number == user_data.employee_number)
            | (Employee.email == user_data.email)
        )
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number or email already exists"
        )

    try:
        # Register creates the user account, the employee profile, and the
        # default leave balances atomically so self-registered accounts are
        # immediately usable (login + self-service features).
        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role="employee"
        )
        db.add(new_user)
        db.flush()

        new_employee = Employee(
            user_id=new_user.id,
            employee_number=user_data.employee_number,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            department=user_data.department,
            position=user_data.position,
            date_hired=user_data.date_hired,
            status="active",
        )

        db.add(new_employee)
        db.flush()

        default_balances = [
            LeaveBalance(
                employee_id=new_employee.id,
                leave_type="vacation",
                total_days=15,
                used_days=0,
            ),
            LeaveBalance(
                employee_id=new_employee.id,
                leave_type="sick",
                total_days=15,
                used_days=0,
            ),
            LeaveBalance(
                employee_id=new_employee.id,
                leave_type="emergency",
                total_days=5,
                used_days=0,
            ),
            LeaveBalance(
                employee_id=new_employee.id,
                leave_type="other",
                total_days=0,
                used_days=0,
            ),
        ]

        db.add_all(default_balances)

        create_audit_log(
            db=db,
            user_id=new_user.id,
            action="register",
            entity_type="employee",
            entity_id=new_employee.id,
            details=(
                f"Self-registered employee {new_employee.first_name} "
                f"{new_employee.last_name} "
                f"(Employee #{new_employee.employee_number})"
            )
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number or email already exists"
        )

    db.refresh(new_user)

    return new_user

@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(User.email == form_data.username)
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Admin accounts are not required to have an employee profile.
    if user.role == "employee":
        employee = db.scalar(
            select(Employee).where(
                Employee.user_id == user.id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee profile not found"
            )

        if employee.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee account is inactive"
            )
    
    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }