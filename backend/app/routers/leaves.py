from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from datetime import date
import math

from app.core.security import get_current_user, get_current_employee
from app.core.permissions import require_admin
from app.core.audit import create_audit_log
from app.core.time import now

from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.user import User
from app.models.leave_balance import LeaveBalance

from app.schemas.leave import (
    LeaveCreate,
    LeaveResponse,
    LeaveListResponse
)
from app.schemas.leave_balance import (
    LeaveBalanceResponse,
    LeaveBalanceUpdate
)

from database import get_db

from typing import Optional


router = APIRouter(
    prefix="/leaves",
    tags=["Leaves"]
)

# CREATE LEAVE REQUEST
@router.post(
    "",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit leave request",
    description=(
        "Creates a pending leave request for the current employee. Requests "
        "that overlap an existing pending or approved request for the same "
        "employee are rejected with 409."
    ),
    responses={
        400: {"description": "End date before start date"},
        409: {"description": "Dates overlap an existing leave request"}
    }
)
def create_leave(
    leave_data: LeaveCreate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    # Lock the employee row so concurrent submissions can't race the overlap check.
    employee = db.scalar(
        select(Employee)
        .where(Employee.id == current_employee.id)
        .with_for_update()
    )

    if leave_data.end_date < leave_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )
    
    overlapping_leave = db.scalar(
        select(Leave).where(
            (Leave.employee_id == employee.id)
            & (Leave.status.in_([
                LeaveStatus.PENDING,
                LeaveStatus.APPROVED
            ]))
            & (Leave.start_date <= leave_data.end_date)
            & (Leave.end_date >= leave_data.start_date)
        )
    )

    if overlapping_leave:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave dates overlap with an existing leave request"
        )

    current_datetime = now()

    new_leave = Leave(
        employee_id=employee.id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        reason=leave_data.reason,
        status=LeaveStatus.PENDING,
        created_at=current_datetime,
        updated_at=current_datetime
    )

    db.add(new_leave)
    db.flush()

    create_audit_log(
        db=db,
        user_id=employee.user_id,
        action="create",
        entity_type="leave",
        entity_id=new_leave.id,
        details=(
            f"Submitted {new_leave.leave_type} leave "
            f"for {employee.first_name} {employee.last_name} "
            f"(Employee #{employee.employee_number}) "
            f"from {new_leave.start_date} to {new_leave.end_date}"
        )
    )

    db.commit()
    db.refresh(new_leave)

    return new_leave

# GET ALL LEAVE REQUESTS (Admin)
@router.get(
    "",
    response_model=LeaveListResponse,
    summary="List leave requests",
    description=(
        "Admin only. Paginated leave list with filters: `status`, "
        "`employee_id`, `leave_type`, `start_date`/`end_date`, and `search` "
        "(employee number, name, email). Sortable via `sort_by` and "
        "`sort_order`."
    ),
    responses={
        400: {"description": "Invalid sort field/order or date range"}
    }
)
def get_all_leaves(
    leave_status: Optional[LeaveStatus] = Query(
        default=None,
        alias="status"
    ),
    employee_id: Optional[int] = None,
    leave_type: Optional[LeaveType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = Query(default=None, max_length=255),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    sort_fields = {
    "id": Leave.id,
    "employee_id": Leave.employee_id,
    "leave_type": Leave.leave_type,
    "start_date": Leave.start_date,
    "end_date": Leave.end_date,
    "status": Leave.status,
    "created_at": Leave.created_at,
    "updated_at": Leave.updated_at
    }

    if sort_by not in sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field: {sort_by}"
        )

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'"
        )

    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )

    query = select(
        Leave,
        Employee.employee_number,
        (Employee.first_name + " " + Employee.last_name).label("employee_name")
    ).join(Employee, Leave.employee_id == Employee.id)

    if leave_status:
        query = query.where(
            Leave.status == leave_status
        )
    
    if employee_id:
        query = query.where(
            Leave.employee_id == employee_id
        )

    if leave_type:
        query = query.where(
            Leave.leave_type == leave_type
        )

    if start_date:
        query = query.where(
            Leave.start_date >= start_date
        )

    if end_date:
        query = query.where(
            Leave.end_date <= end_date
        )
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )
    
    count_query = select(
    func.count()
    ).select_from(Leave).join(Employee, Leave.employee_id == Employee.id)

    if leave_status:
        count_query = count_query.where(
            Leave.status == leave_status
        )

    if employee_id:
        count_query = count_query.where(
            Leave.employee_id == employee_id
        )

    if leave_type:
        count_query = count_query.where(
            Leave.leave_type == leave_type
        )

    if start_date:
        count_query = count_query.where(
            Leave.start_date >= start_date
        )

    if end_date:
        count_query = count_query.where(
            Leave.end_date <= end_date
        )
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        count_query = count_query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )

    total = db.scalar(count_query) or 0

    sort_column = sort_fields[sort_by]

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 0

    rows = db.execute(
        query
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        {
            "id": leave.id,
            "employee_id": leave.employee_id,
            "employee_number": employee_number,
            "employee_name": employee_name,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "reason": leave.reason,
            "status": leave.status,
            "created_at": leave.created_at,
            "updated_at": leave.updated_at,
        }
        for leave, employee_number, employee_name in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

# GET MY LEAVES
@router.get(
    "/me",
    response_model=list[LeaveResponse],
    summary="Get my leave requests",
    description=(
        "Returns the current employee's leave requests, newest start date first."
    )
)
def get_my_leaves(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    employee = current_employee

    leaves = db.scalars(
        select(Leave)
        .where(Leave.employee_id == employee.id)
        .order_by(Leave.start_date.desc())
    ).all()

    return leaves

# GET MY LEAVE BALANCE
@router.get(
    "/balance/me",
    response_model=list[LeaveBalanceResponse],
    summary="Get my leave balances",
    description=(
        "Returns the current employee's leave balances per leave type, "
        "including computed `remaining_days`."
    )
)
def get_my_leave_balance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    employee = current_employee

    balances = db.scalars(
        select(LeaveBalance)
        .where(
            LeaveBalance.employee_id == employee.id
        )
        .order_by(LeaveBalance.leave_type)
    ).all()

    return [
        {
            "id": balance.id,
            "employee_id": balance.employee_id,
            "leave_type": balance.leave_type,
            "total_days": balance.total_days,
            "used_days": balance.used_days,
            "remaining_days": (
                balance.total_days - balance.used_days
            )
        }
        for balance in balances
    ]

# GET EMPLOYEE LEAVE BALANCE (Admin)
@router.get(
    "/balance/{employee_id}",
    response_model=list[LeaveBalanceResponse],
    summary="Get employee leave balances",
    description=(
        "Admin only. Leave balances per leave type for a specific employee."
    ),
    responses={
        404: {"description": "Employee not found"}
    }
)
def get_employee_leave_balance(
    employee_id: int,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    balances = db.scalars(
        select(LeaveBalance)
        .where(
            LeaveBalance.employee_id == employee_id
        )
        .order_by(LeaveBalance.leave_type)
    ).all()

    return [
        {
            "id": balance.id,
            "employee_id": balance.employee_id,
            "leave_type": balance.leave_type,
            "total_days": balance.total_days,
            "used_days": balance.used_days,
            "remaining_days": (
                balance.total_days - balance.used_days
            )
        }
        for balance in balances
    ]

# UPDATE BALANCE (Admin)
@router.patch(
    "/balance/{employee_id}/{leave_type}",
    response_model=LeaveBalanceResponse,
    summary="Update leave balance",
    description=(
        "Admin only. Sets the `total_days` for an employee's leave type. "
        "The new total cannot be lower than the days already used."
    ),
    responses={
        400: {"description": "Total days cannot be lower than used days"},
        404: {"description": "Employee or leave balance not found"}
    }
)
def update_leave_balance(
    employee_id: int,
    leave_type: LeaveType,
    balance_data: LeaveBalanceUpdate,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    balance = db.scalar(
        select(LeaveBalance)
        .where(
            (LeaveBalance.employee_id == employee_id)
            & (LeaveBalance.leave_type == leave_type.value)
        )
        .with_for_update()
    )

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave balance not found"
        )

    if balance_data.total_days < balance.used_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Total days cannot be less than "
                "used days"
            )
        )

    balance.total_days = balance_data.total_days

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="leave_balance",
        entity_id=balance.id,
        details=(
            f"Updated {leave_type.value} leave balance "
            f"for {employee.first_name} {employee.last_name} "
            f"(Employee #{employee.employee_number}): "
            f"total days set to {balance.total_days}"
        )
    )

    db.commit()
    db.refresh(balance)

    return {
        "id": balance.id,
        "employee_id": balance.employee_id,
        "leave_type": balance.leave_type,
        "total_days": balance.total_days,
        "used_days": balance.used_days,
        "remaining_days": (
            balance.total_days - balance.used_days
        )
    }

# CANCEL LEAVE REQUEST
@router.patch(
    "/{leave_id}/cancel",
    response_model=LeaveResponse,
    summary="Cancel leave request",
    description=(
        "Cancels one of the current employee's requests. Only pending or "
        "approved requests can be cancelled; cancelling an approved request "
        "restores the days deducted from the leave balance."
    ),
    responses={
        400: {"description": "Request is not pending/approved, or balance is inconsistent"},
        404: {"description": "Leave request or leave balance not found"}
    }
)
def cancel_leave(
    leave_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    employee = current_employee

    leave = db.scalar(
        select(Leave)
        .where(
            (Leave.id == leave_id)
            & (Leave.employee_id == employee.id)
        )
        .with_for_update()
    )

    if leave is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave.status not in {
        LeaveStatus.PENDING,
        LeaveStatus.APPROVED
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or approved leave requests can be cancelled"
        )

    if leave.status == LeaveStatus.APPROVED:
        balance = db.scalar(
            select(LeaveBalance)
            .where(
                (LeaveBalance.employee_id == leave.employee_id)
                & (LeaveBalance.leave_type == leave.leave_type)
            )
            .with_for_update()
        )
        if balance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave balance not found"
            )
        leave_days = (
            leave.end_date - leave.start_date
        ).days + 1

        if balance.used_days < leave_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave balance is inconsistent"
            )
        balance.used_days -= leave_days

    leave.status = LeaveStatus.CANCELLED
    leave.updated_at = now()

    create_audit_log(
        db=db,
        user_id=employee.user_id,
        action="cancel",
        entity_type="leave",
        entity_id=leave.id,
        details=(
            f"Cancelled {leave.leave_type} leave "
            f"for {employee.first_name} {employee.last_name} "
            f"(Employee #{employee.employee_number}) "
            f"from {leave.start_date} to {leave.end_date}"
        )
    )

    db.commit()
    db.refresh(leave)

    return leave

# APPROVE LEAVE (Admin)
@router.patch(
    "/{leave_id}/approve",
    response_model=LeaveResponse,
    summary="Approve leave request",
    description=(
        "Admin only. Approves a pending request and deducts the requested days "
        "from the employee's leave balance. Rejected when the employee is "
        "inactive, the request overlaps an existing attendance record, or the "
        "balance is insufficient."
    ),
    responses={
        400: {"description": "Request is not pending, employee inactive, or insufficient balance"},
        404: {"description": "Leave request, employee, or leave balance not found"},
        409: {"description": "Request overlaps an attendance record"}
    }
)
def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    leave = db.scalar(
        select(Leave)
        .where(Leave.id == leave_id)
        .with_for_update()
    )

    if leave is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leave requests can be approved"
        )

    employee = db.scalar(
        select(Employee).where(
            Employee.id == leave.employee_id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve leave for an inactive employee"
        )

    conflicting_attendance = db.scalar(
        select(Attendance).where(
            (Attendance.employee_id == leave.employee_id)
            & (Attendance.date >= leave.start_date)
            & (Attendance.date <= leave.end_date)
        )
    )

    if conflicting_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot approve leave that overlaps an attendance record"
        )

    balance = db.scalar(
        select(LeaveBalance)
        .where(
            (LeaveBalance.employee_id == leave.employee_id)
            & (LeaveBalance.leave_type == leave.leave_type)
        )
        .with_for_update()
    )

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave balance not found"
        )
    
    requested_days = (
        leave.end_date - leave.start_date
    ).days + 1

    remaining_days = (
        balance.total_days - balance.used_days
    )

    if requested_days > remaining_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient {leave.leave_type} leave balance. "
                f"Requested: {requested_days} days, "
                f"Remaining: {remaining_days} days"
            )
        )

    leave.status = LeaveStatus.APPROVED
    leave.updated_at = now()

    balance.used_days += requested_days

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="approve",
        entity_type="leave",
        entity_id=leave.id,
        details=(
            f"Approved {leave.leave_type} leave "
            f"for {employee.first_name} {employee.last_name} "
            f"(Employee #{employee.employee_number}) "
            f"from {leave.start_date} to {leave.end_date} "
            f"({requested_days} days)"
        )
    )

    db.commit()
    db.refresh(leave)

    return leave

# REJECT LEAVE (Admin)
@router.patch(
    "/{leave_id}/reject",
    response_model=LeaveResponse,
    summary="Reject leave request",
    description=(
        "Admin only. Rejects a pending request without changing the leave balance."
    ),
    responses={
        400: {"description": "Request is not pending"},
        404: {"description": "Leave request or employee not found"}
    }
)
def reject_leave(
    leave_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    leave = db.scalar(
        select(Leave)
        .where(Leave.id == leave_id)
        .with_for_update()
    )

    if leave is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leave requests can be rejected"
        )

    employee = db.scalar(
        select(Employee).where(
            Employee.id == leave.employee_id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    leave.status = LeaveStatus.REJECTED
    leave.updated_at = now()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="reject",
        entity_type="leave",
        entity_id=leave.id,
        details=(
            f"Rejected {leave.leave_type} leave "
            f"for {employee.first_name} {employee.last_name} "
            f"(Employee #{employee.employee_number}) "
            f"from {leave.start_date} to {leave.end_date}"
        )
    )

    db.commit()
    db.refresh(leave)

    return leave
