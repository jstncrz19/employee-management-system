from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.core.time import now

def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    details: str | None = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        created_at=now()
    )

    db.add(audit_log)

    return audit_log