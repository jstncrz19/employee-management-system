from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.leave import LeaveStatus, LeaveType

class LeaveCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str | None = Field(
        default=None,
        max_length=1000
    )

class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class LeaveListResponse(BaseModel):
    items: list[LeaveResponse]
    total: int
    page: int
    limit: int
    pages: int