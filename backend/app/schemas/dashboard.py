from datetime import date, time

from pydantic import BaseModel

from app.models.leave import LeaveStatus, LeaveType

class DashboardSummaryResponse(BaseModel):
    total_employees: int
    active_employees: int
    present_today: int
    absent_today: int
    on_leave_today: int
    pending_leave_requests: int

class DashboardAttendanceResponse(BaseModel):
    date: date
    time_in: time | None
    time_out: time | None
    status: str

class DashboardLeaveResponse(BaseModel):
    id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus

class DashboardLeaveBalanceResponse(BaseModel):
    leave_type: str
    total_days: int
    used_days: int
    remaining_days: int

class EmployeeDashboardResponse(BaseModel):
    attendance_today: DashboardAttendanceResponse | None
    leave_balances: list[DashboardLeaveBalanceResponse]
    pending_leaves: list[DashboardLeaveResponse]
    upcoming_leaves: list[DashboardLeaveResponse]
    recent_attendance: list[DashboardAttendanceResponse]