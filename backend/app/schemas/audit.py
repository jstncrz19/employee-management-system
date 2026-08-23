from datetime import datetime

from pydantic import BaseModel, ConfigDict

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    employee_id: int | None
    employee_name: str | None
    action: str
    entity_type: str
    entity_id: int
    details: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    limit: int
    pages: int