from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_UPLOAD = "data_upload"
    DATA_DELETE = "data_delete"
    REPORT_GENERATE = "report_generate"
    REPORT_EXPORT = "report_export"
    QUERY_EXECUTE = "query_execute"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    resource = Column(String(255))
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
