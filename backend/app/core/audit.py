from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog, AuditAction
from typing import Optional


async def log_audit(
    db: AsyncSession,
    user_id: int,
    action: AuditAction,
    resource: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit_log)
    await db.commit()
    return audit_log
