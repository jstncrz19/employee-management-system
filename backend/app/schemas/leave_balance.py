from pydantic import BaseModel, ConfigDict, Field

class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    total_days: int
    used_days: int
    remaining_days: int

    model_config = ConfigDict(
        from_attributes=True
    )

class LeaveBalanceUpdate(BaseModel):
    total_days: int = Field(
        ge=0,
        le=365
    )