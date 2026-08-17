from datetime import date, time

from pydantic import BaseModel, ConfigDict


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    time_in: time | None
    time_out: time | None
    status: str

    model_config = ConfigDict(
        from_attributes=True
    )

class AttendanceListResponse(BaseModel):
    items: list[AttendanceResponse]
    total: int
    page: int
    limit: int
    pages: int

    model_config = {
        "from_attributes": True
    }