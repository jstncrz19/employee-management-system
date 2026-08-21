from datetime import date

from typing import Optional
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.time import now
from app.core.security import get_current_employee
from app.core.permissions import require_admin

from app.models.user import User
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus

from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceListResponse
)
from database import get_db

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)

# FOR CHECK-IN
@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED
)
def check_in(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    current_datetime = now()
    today = current_datetime.date()

    approved_leave = db.scalar(
        select(Leave).where(
            (Leave.employee_id == current_employee.id)
            & (Leave.status == LeaveStatus.APPROVED.value)
            & (Leave.start_date <= today)
            & (Leave.end_date >= today)
        )
    )

    if approved_leave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are on approved leave today"
        )

    existing_attendance = db.scalar(
        select(Attendance).where(
            (Attendance.employee_id == current_employee.id)
            & (Attendance.date == today)
        )
    )

    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in today"
        )
    
    attendance = Attendance(
        employee_id=current_employee.id,
        date=today,
        time_in=current_datetime.time(),
        status="present"
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance

# FOR CHECK-OUT
@router.post(
    "/check-out",
    response_model=AttendanceResponse
)
def check_out(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    current_datetime = now()
    today = current_datetime.date()

    approved_leave = db.scalar(
        select(Leave).where(
            (Leave.employee_id == current_employee.id)
            & (Leave.status == LeaveStatus.APPROVED.value)
            & (Leave.start_date <= today)
            & (Leave.end_date >= today)
        )
    )

    if approved_leave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are on approved leave today"
        )

    attendance = db.scalar(
        select(Attendance).where(
            (Attendance.employee_id == current_employee.id)
            & (Attendance.date == today)
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not checked in today"
        )

    if attendance.time_out is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked out today"
        )

    attendance.time_out = current_datetime.time()

    db.commit()
    db.refresh(attendance)

    return attendance

# GET ALL ATTENDANCE (Admin)
@router.get(
    "",
    response_model=AttendanceListResponse
)
def get_all_attendance(
    employee_id: Optional[int] = None,
    date: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = select(Attendance)

    if employee_id:
        query = query.where(
            Attendance.employee_id == employee_id
        )
    if date:
        query = query.where(
            Attendance.date == date
        )

    count_query = select(func.count()).select_from(Attendance)

    if employee_id:
        count_query = count_query.where(
            Attendance.employee_id == employee_id
        )

    if date:
        count_query = count_query.where(
            Attendance.date == date
        )

    total = db.scalar(count_query) or 0

    pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit

    attendance_records = db.scalars(
        query
        .order_by(Attendance.date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": attendance_records,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

# GET RECORDS
@router.get(
    "/me",
    response_model=list[AttendanceResponse]
)
def get_my_attendance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    attendance_records = db.scalars(
        select(Attendance)
        .where(Attendance.employee_id == current_employee.id)
        .order_by(Attendance.date.desc())
    ).all()

    return attendance_records