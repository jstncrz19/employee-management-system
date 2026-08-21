from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.core.security import get_current_employee
from app.core.time import now

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus
from app.models.leave_balance import LeaveBalance
from app.models.user import User

from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardAttendanceResponse,
    DashboardLeaveResponse,
    DashboardLeaveBalanceResponse,
    EmployeeDashboardResponse
)

from database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

# SUMMARY DASHBOARD (Admin)
@router.get(
    "/summary",
    response_model=DashboardSummaryResponse
)
def get_dashboard_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    today = now().date()

    total_employees = db.scalar(
        select(func.count()).select_from(Employee)
    ) or 0

    active_employees = db.scalar(
        select(func.count())
        .select_from(Employee)
        .where(Employee.status == "active")
    ) or 0

    present_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .join(
            Employee,
            Attendance.employee_id == Employee.id
        )
        .where(
            (Attendance.date == today)
            & (Employee.status == "active")
        )
    ) or 0

    on_leave_today = db.scalar(
        select(func.count())
        .select_from(Leave)
        .join(
            Employee,
            Leave.employee_id == Employee.id
        )
        .where(
            (Leave.status == LeaveStatus.APPROVED.value)
            & (Leave.start_date <= today)
            & (Leave.end_date >= today)
            & (Employee.status == "active")
        )
    ) or 0

    pending_leave_requests = db.scalar(
        select(func.count())
        .select_from(Leave)
        .where(
            Leave.status == LeaveStatus.PENDING
        )
    ) or 0

    absent_today = active_employees - present_today - on_leave_today

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "on_leave_today": on_leave_today,
        "pending_leave_requests": pending_leave_requests
    }

# DASHBOARD (EMPLOYEE)
@router.get(
    "/me",
    response_model=EmployeeDashboardResponse
)
def get_employee_dashboard(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    today = now().date()

    attendance_today = db.scalar(
        select(Attendance)
        .where(
            (Attendance.employee_id == current_employee.id)
            & (Attendance.date == today)
        )
    )

    balances = db.scalars(
        select(LeaveBalance)
        .where(
            LeaveBalance.employee_id == current_employee.id
        )
        .order_by(LeaveBalance.leave_type)
    ).all()

    pending_leaves = db.scalars(
        select(Leave)
        .where(
            (Leave.employee_id == current_employee.id)
            & (Leave.status == LeaveStatus.PENDING)
        )
        .order_by(Leave.start_date.asc())
    ).all()

    upcoming_leaves = db.scalars(
        select(Leave)
        .where(
            (Leave.employee_id == current_employee.id)
            & (Leave.status == LeaveStatus.APPROVED)
            & (Leave.start_date > today)
        )
        .order_by(Leave.start_date.asc())
    ).all()

    recent_attendance = db.scalars(
        select(Attendance)
        .where(
            Attendance.employee_id == current_employee.id
        )
        .order_by(
            Attendance.date.desc()
        )
        .limit(5)
    ).all()

    attendance_today_response = None

    if attendance_today:
        attendance_today_response = {
            "date": attendance_today.date,
            "time_in": attendance_today.time_in,
            "time_out": attendance_today.time_out,
            "status": attendance_today.status
        }

    balance_response = [
        {
            "leave_type": balance.leave_type,
            "total_days": balance.total_days,
            "used_days": balance.used_days,
            "remaining_days": (
                balance.total_days - balance.used_days
            )
        }
        for balance in balances
    ]

    pending_leave_response = [
        {
            "id": leave.id,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "status": leave.status
        }
        for leave in pending_leaves
    ]

    upcoming_leave_response = [
        {
            "id": leave.id,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "status": leave.status
        }
        for leave in upcoming_leaves
    ]

    recent_attendance_response = [
        {
            "date": attendance.date,
            "time_in": attendance.time_in,
            "time_out": attendance.time_out,
            "status": attendance.status
        }
        for attendance in recent_attendance
    ]

    return {
        "attendance_today": attendance_today_response,
        "leave_balances": balance_response,
        "pending_leaves": pending_leave_response,
        "upcoming_leaves": upcoming_leave_response,
        "recent_attendance": recent_attendance_response
    }