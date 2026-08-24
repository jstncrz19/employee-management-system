from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_user,
    get_current_employee,
    hash_password
)
from app.core.permissions import require_admin
from app.core.audit import create_audit_log

from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeUpdate,
    EmployeePatch,
    EmployeeStatus,
    EmployeeSelfUpdate
)
from app.schemas.auth import (
    EmployeeAccountCreate,
    UserResponse
)
from database import get_db
import math

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

# CREATE EMPLOYEE
@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing_employee = db.scalar(
        select(Employee).where(
            (Employee.employee_number == employee_data.employee_number)
            | (Employee.email == employee_data.email)
        )
    )

    if existing_employee:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Employee number or email already exists"
        )
    
    new_employee = Employee(
        employee_number=employee_data.employee_number,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        email=employee_data.email,
        department=employee_data.department,
        position=employee_data.position,
        date_hired=employee_data.date_hired,
        status=employee_data.status,
    )

    db.add(new_employee)
    db.flush()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="employee",
        entity_id=new_employee.id,
        details=(
            f"Created employee {new_employee.first_name} "
            f"{new_employee.last_name} "
            f"(employee number {new_employee.employee_number})"
        )
    )

    db.commit()
    db.refresh(new_employee)

    return(new_employee)

# CREATE EMPLOYEE USER ACCOUNT
@router.post(
    "/{employee_id}/account",
    response_model=UserResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_employee_account(
    employee_id: int,
    account_data: EmployeeAccountCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(
            Employee.id == employee_id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an account for an inactive employee"
        )

    if employee.user_id is not None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Employee already has a user account"
        )

    existing_user = db.scalar(
        select(User).where(
            User.email == account_data.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    new_user = User(
        email=account_data.email,
        password_hash=hash_password(account_data.password),
        role="employee"
    )

    db.add(new_user)
    db.flush()

    employee.user_id = new_user.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="user",
        entity_id=new_user.id,
        details=(
            f"Created employee account for "
            f"{employee.first_name} {employee.last_name}"
        )
    )

    db.commit()
    db.refresh(new_user)

    return new_user

# GET EMPLOYEES
@router.get(
    "",
    response_model=EmployeeListResponse
)
def get_employees(
    status: Optional[EmployeeStatus] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    # Sorting Fields and Validation
    sort_fields = {
        "id": Employee.id,
        "employee_number": Employee.employee_number,
        "first_name": Employee.first_name,
        "last_name": Employee.last_name,
        "department": Employee.department,
        "position": Employee.position,
        "date_hired": Employee.date_hired,
        "status": Employee.status,
    }

    if sort_by not in sort_fields:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field: {sort_by}"
        )
    
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'"
        )

    # Main Query
    query = select(Employee)

    if status:
        query = query.where(Employee.status == status)
    
    if department:
        query = query.where(Employee.department == department)
    
    if search:
        search_term = f"%{search}%"

        query = query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )

    # Get total number of employees matching the filters
    count_query = select(func.count()).select_from(Employee)

    if status:
        count_query = count_query.where(Employee.status == status)
    
    if department:
        count_query = count_query.where(Employee.department == department)
    
    if search:
        search_term = f"%{search}%"

        count_query = count_query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )
    
    total = db.scalar(count_query) or 0

    # Sort
    sort_column = sort_fields[sort_by]

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Calculate pagination
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 0

    # Get employees for the requested page
    employees = db.scalars(
        query
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": employees,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

# GET ME
@router.get(
    "/me",
    response_model=EmployeeResponse
)
def get_my_employee(
    current_employee: Employee = Depends(get_current_employee)
):
    return current_employee

# PATCH SELF DETAILS
@router.patch(
    "/me",
    response_model=EmployeeResponse
)
def update_my_employee(
    employee_data: EmployeeSelfUpdate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    update_data = employee_data.model_dump(
        exclude_unset=True
    )

    if "email" in update_data:
        existing_employee = db.scalar(
            select(Employee).where(
                (Employee.email == update_data["email"])
                & (Employee.id != current_employee.id)
            )
        )

        if existing_employee:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

    for field, value in update_data.items():
        setattr(current_employee, field, value)

    db.commit()
    db.refresh(current_employee)

    return current_employee

# GET EMPLOYEE (SPECIFIC)
@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if current_user.role != "admin":
        if employee.user_id != current_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="You can only access your own employee profile"
            ) 
    
    return employee

# UPDATE EMPLOYEE
@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    existing_employee = db.scalar(
        select(Employee).where(
            (
                (Employee.employee_number == employee_data.employee_number)
                | (Employee.email == employee_data.email)
            )
            & (Employee.id != employee_id)
        )
    )

    if existing_employee:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Employee number or email already exists"
        )
    
    employee.employee_number = employee_data.employee_number
    employee.first_name = employee_data.first_name
    employee.last_name = employee_data.last_name
    employee.email = employee_data.email
    employee.department = employee_data.department
    employee.position = employee_data.position
    employee.date_hired = employee_data.date_hired
    employee.status = employee_data.status

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="employee",
        entity_id=employee.id,
        details=(
            f"Updated employee {employee.first_name} "
            f"{employee.last_name}"
        )
    )

    db.commit()
    db.refresh(employee)

    return employee

# PARTIAL UPDATE EMPLOYEE
@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def patch_employee(
    employee_id: int,
    employee_data: EmployeePatch,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    update_data = employee_data.model_dump(
        exclude_unset=True
    )

    if "email" in update_data:
        existing_employee = db.scalar(
            select(Employee).where(
                (Employee.email == update_data["email"])
                & (Employee.id != employee_id)
            )
        )

        if existing_employee:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

    for field, value in update_data.items():
        setattr(employee, field, value)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="employee",
        entity_id=employee.id,
        details=(
            f"Updated employee {employee.first_name} "
            f"{employee.last_name}: "
            f"{', '.join(update_data.keys())}"
        )
    )

    db.commit()
    db.refresh(employee)

    return employee

# DELETE EMPLOYEE (Update status to 'inactive')
@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def delete_employee(
    employee_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Employee is already inactive"
        )

    employee.status = "inactive"

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="deactivate",
        entity_type="employee",
        entity_id=employee.id,
        details=(
            f"Deactivated employee {employee.first_name} "
            f"{employee.last_name}"
        )
    )

    db.commit()
    db.refresh(employee)

    return employee