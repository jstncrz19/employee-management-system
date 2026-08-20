from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datetime import date
import math

from app.core.security import get_current_user
from app.core.permissions import require_admin
from app.core.time import now

from app.models.employee import Employee
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
    status_code=status.HTTP_201_CREATED
)
def create_leave(
    leave_data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
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
    db.commit()
    db.refresh(new_leave)

    return new_leave

# GET ALL LEAVE REQUEST (Admin)
@router.get(
    "",
    response_model=LeaveListResponse
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

    query = select(Leave)

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
    
    count_query = select(
    func.count()
    ).select_from(Leave)

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

    total = db.scalar(count_query) or 0

    sort_column = sort_fields[sort_by]

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 0

    leaves = db.scalars(
        query
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": leaves,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

# GET MY LEAVES
@router.get(
    "/me",
    response_model=list[LeaveResponse]
)
def get_my_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    leaves = db.scalars(
        select(Leave)
        .where(Leave.employee_id == employee.id)
        .order_by(Leave.start_date.desc())
    ).all()

    return leaves

# GET MY LEAVE BALANCE
@router.get(
    "/balance/me",
    response_model=list[LeaveBalanceResponse]
)
def get_my_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

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

# UPDATE BALANCE (Admin)
@router.patch(
    "/balance/{employee_id}/{leave_type}",
    response_model=LeaveBalanceResponse
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
        select(LeaveBalance).where(
            (LeaveBalance.employee_id == employee_id)
            & (LeaveBalance.leave_type == leave_type.value)
        )
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
    response_model=LeaveResponse
)
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    leave = db.scalar(
        select(Leave).where(
            (Leave.id == leave_id)
            & (Leave.employee_id == employee.id)
        )
    )

    if leave is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if employee.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own leave requests"
        )
    
    if leave.status not in {
        LeaveStatus.PENDING,
        LeaveStatus.APPROVED
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or approved leave requests can be cancelled"
        )

    # if leave.status != LeaveStatus.PENDING:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Only pending leave requests can be cancelled"
    #     )

    if leave.status == LeaveStatus.APPROVED:
        balance = db.scalar(
            select(LeaveBalance).where(
                (LeaveBalance.employee_id == leave.employee_id)
                & (LeaveBalance.leave_type == leave.leave_type)
            )
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

    db.commit()
    db.refresh(leave)

    return leave

# APPROVE LEAVE (Admin)
@router.patch(
    "/{leave_id}/approve",
    response_model=LeaveResponse
)
def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    leave = db.scalar(
        select(Leave).where(
            Leave.id == leave_id
        )
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

    balance = db.scalar(
        select(LeaveBalance).where(
            (LeaveBalance.employee_id == leave.employee_id)
            & (LeaveBalance.leave_type == leave.leave_type)
        )
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

    db.commit()
    db.refresh(leave)

    return leave

# REJECT LEAVE (Admin)
@router.patch(
    "/{leave_id}/reject",
    response_model=LeaveResponse
)
def reject_leave(
    leave_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    leave = db.scalar(
        select(Leave).where(
            Leave.id == leave_id
        )
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

    leave.status = LeaveStatus.REJECTED
    leave.updated_at = now()

    db.commit()
    db.refresh(leave)

    return leave