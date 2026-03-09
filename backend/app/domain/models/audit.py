from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    area: Mapped[str] = mapped_column(String(50), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(100), default="anonymous")
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(50), default="backend", index=True)
    resource: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    http_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    http_path: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="INFO", index=True)
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
