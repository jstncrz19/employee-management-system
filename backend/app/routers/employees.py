from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeUpdate,
    EmployeePatch,
    EmployeeStatus
)
from database import get_db
import math

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_user),
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
            status_code=status.HTTP_409_CONFLICT,
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
    db.commit()
    db.refresh(new_employee)

    return(new_employee)

@router.get(
    "",
    response_model=EmployeeListResponse
)
def get_employees(
    status: Optional[EmployeeStatus] = None,
    department: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = select(Employee)

    if status:
        query = query.where(Employee.status == status)
    
    if department:
        query = query.where(Employee.department == department)

    # Get total number of employees matching the filters
    total = db.query(Employee).filter(
        *query._where_criteria
    ).count()

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee

@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_409_CONFLICT,
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

    db.commit()
    db.refresh(employee)

    return employee

@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def patch_employee(
    employee_id: int,
    employee_data: EmployeePatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return employee

@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(Employee.id == employee_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already inactive"
        )

    employee.status = "inactive"

    db.commit()
    db.refresh(employee)

    return employee