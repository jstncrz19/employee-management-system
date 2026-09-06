from datetime import date

from typing import Optional
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import now
from app.core.security import get_current_employee_user
from app.core.permissions import require_admin
from app.core.audit import create_audit_log

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
    status_code=status.HTTP_201_CREATED,
    summary="Check in",
    description=(
        "Employee only. Records today's attendance with status `present`. "
        "Blocked with 400 while on approved leave or if already checked in today."
    ),
    responses={
        400: {"description": "On approved leave today, or already checked in"},
        409: {"description": "Already checked in today (concurrent request)"}
    }
)
def check_in(
    current_employee: Employee = Depends(get_current_employee_user),
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

    try:
        db.add(attendance)
        db.flush()

        create_audit_log(
            db=db,
            user_id=current_employee.user_id,
            action="check_in",
            entity_type="attendance",
            entity_id=attendance.id,
            details=(
                f"Checked in {current_employee.first_name} "
                f"{current_employee.last_name} "
                f"(Employee #{current_employee.employee_number}) "
                f"on {attendance.date} at {attendance.time_in}"
            )
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already checked in today"
        )

    db.refresh(attendance)

    return attendance

# FOR CHECK-OUT
@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    summary="Check out",
    description=(
        "Employee only. Records today's check-out time. Requires a check-in "
        "earlier today and is blocked while on approved leave."
    ),
    responses={
        400: {"description": "Not checked in, already checked out, or on approved leave"}
    }
)
def check_out(
    current_employee: Employee = Depends(get_current_employee_user),
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

    create_audit_log(
        db=db,
        user_id=current_employee.user_id,
        action="check_out",
        entity_type="attendance",
        entity_id=attendance.id,
        details=(
            f"Checked out {current_employee.first_name} "
            f"{current_employee.last_name} "
            f"(Employee #{current_employee.employee_number}) "
            f"on {attendance.date} at {attendance.time_out}"
        )
    )

    db.commit()
    db.refresh(attendance)

    return attendance

# GET ALL ATTENDANCE (Admin)
@router.get(
    "",
    response_model=AttendanceListResponse,
    summary="Get attendance records",
    description=(
        "Admin only. Paginated attendance list with filters: `employee_id`, "
        "`date`, `start_date`/`end_date`, and `search` (employee number, name, "
        "email)."
    ),
    responses={
        400: {"description": "End date before start date"}
    }
)
def get_all_attendance(
    employee_id: Optional[int] = None,
    date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )

    query = select(
        Attendance,
        Employee.employee_number,
        (Employee.first_name + " " + Employee.last_name).label("employee_name")
    ).join(Employee, Attendance.employee_id == Employee.id)

    if employee_id:
        query = query.where(
            Attendance.employee_id == employee_id
        )
    if date:
        query = query.where(
            Attendance.date == date
        )
    if start_date:
        query = query.where(Attendance.date >= start_date)
    if end_date:
        query = query.where(Attendance.date <= end_date)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )

    count_query = (
        select(func.count())
        .select_from(Attendance)
        .join(Employee, Attendance.employee_id == Employee.id)
    )

    if employee_id:
        count_query = count_query.where(
            Attendance.employee_id == employee_id
        )

    if date:
        count_query = count_query.where(
            Attendance.date == date
        )
    if start_date:
        count_query = count_query.where(Attendance.date >= start_date)
    if end_date:
        count_query = count_query.where(Attendance.date <= end_date)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        count_query = count_query.where(
            (Employee.employee_number.cast(String).ilike(search_term))
            | Employee.first_name.ilike(search_term)
            | Employee.last_name.ilike(search_term)
            | Employee.email.ilike(search_term)
        )

    total = db.scalar(count_query) or 0

    pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit

    attendance_records = db.execute(
        query
        .order_by(Attendance.date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        {
            "id": attendance.id,
            "employee_id": attendance.employee_id,
            "employee_number": employee_number,
            "employee_name": employee_name,
            "date": attendance.date,
            "time_in": attendance.time_in,
            "time_out": attendance.time_out,
            "status": attendance.status,
        }
        for attendance, employee_number, employee_name in attendance_records
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

# GET RECORDS
@router.get(
    "/me",
    response_model=list[AttendanceResponse],
    summary="Get my attendance history",
    description=(
        "Employee only. Attendance history for the current employee, "
        "newest first."
    )
)
def get_my_attendance(
    current_employee: Employee = Depends(get_current_employee_user),
    db: Session = Depends(get_db)
):
    attendance_records = db.scalars(
        select(Attendance)
        .where(Attendance.employee_id == current_employee.id)
        .order_by(Attendance.date.desc())
    ).all()

    return attendance_records
