import math

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.permissions import require_admin

from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.employee import Employee
from app.schemas.audit import AuditLogListResponse

from database import get_db

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)

# GET AUDIT_LOGS
@router.get(
    "",
    response_model=AuditLogListResponse
)
def get_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|action)$"
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    
    query = (
        select(
            AuditLog,
            User.email.label("user_email"),
            Employee.id.label("employee_id"),
            (Employee.first_name + " " + Employee.last_name).label(
                "employee_name"
            )
        )
        .join(
            User,
            AuditLog.user_id == User.id
        )
        .outerjoin(
            Employee,
            Employee.user_id == User.id
        )
    )

    if action:
        query = query.where(
            AuditLog.action == action
        )

    if entity_type:
        query = query.where(
            AuditLog.entity_type == entity_type
        )
    
    if user_id:
        query = query.where(
            AuditLog.user_id == user_id
        )
    
    if start_date:
        start_datetime = datetime.combine(
            start_date,
            time.min
        )

        query = query.where(
            AuditLog.created_at >= start_datetime
        )

    if end_date:
        end_datetime = datetime.combine(
            end_date,
            time.max
        )

        query = query.where(
            AuditLog.created_at <= end_datetime
        )
    
    if sort_by == "created_at":
        sort_column = AuditLog.created_at
    else:
        sort_column = AuditLog.action

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = db.scalar(
        select(func.count()).select_from(
            query.subquery()
        )
    ) or 0

    pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit

    results = db.execute(
        query
        .offset(offset)
        .limit(limit)
    ).all()

    audit_logs = []

    for audit_log, user_email, employee_id, employee_name in results:
        audit_logs.append(
            {
                "id": audit_log.id,
                "user_id": audit_log.user_id,
                "user_email": user_email,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "action": audit_log.action,
                "entity_type": audit_log.entity_type,
                "entity_id": audit_log.entity_id,
                "details": audit_log.details,
                "created_at": audit_log.created_at
            }
        )

    return {
        "items": audit_logs,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }