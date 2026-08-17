from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr

from enum import Enum

from typing import Optional

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESIGNED = "resigned"
    TERMINATED = "terminated"

class EmployeeCreate(BaseModel):
    employee_number: int
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    position: str
    date_hired: date
    status: EmployeeStatus = EmployeeStatus.ACTIVE

class EmployeeUpdate(BaseModel):
    employee_number: int
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    position: str
    date_hired: date
    status: str

class EmployeePatch(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    department: str | None = None
    position: str | None = None
    status: EmployeeStatus | None = None

class EmployeeSelfUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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