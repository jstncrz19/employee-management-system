from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from enum import Enum

from typing import Optional

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESIGNED = "resigned"
    TERMINATED = "terminated"

class EmployeeCreate(BaseModel):
    employee_number: int = Field(gt=0)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department: str = Field(min_length=1, max_length=100)
    position: str = Field(min_length=1, max_length=100)
    date_hired: date
    status: EmployeeStatus = EmployeeStatus.ACTIVE

class EmployeeUpdate(BaseModel):
    employee_number: int = Field(gt=0)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department: str = Field(min_length=1, max_length=100)
    position: str = Field(min_length=1, max_length=100)
    date_hired: date
    status: EmployeeStatus

class EmployeePatch(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    department: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, min_length=1, max_length=100)
    status: EmployeeStatus | None = None

class EmployeeSelfUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

class EmployeeResponse(BaseModel):
    id: int
    employee_number: int
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    position: str
    date_hired: date
    status: EmployeeStatus
    
    model_config = ConfigDict(from_attributes=True)

class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    page: int
    limit: int
    pages: int
