import uuid
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.adapters.gateways.audit_gateway import AuditGateway
from app.adapters.gateways.idempotency_gateway import IdempotencyGateway
from app.adapters.gateways.notification_gateway import NotificationGateway
from app.adapters.gateways.transaction_gateway import TransactionGateway
from app.application.services.financial_service import FinancialService
from app.application.services.notification_service import NotificationService
from app.application.services.plugin_service import PluginService
from app.core.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_request_id(x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> str:
    return x_request_id or str(uuid.uuid4())


def get_actor(x_actor: str | None = Header(default=None, alias="X-Actor")) -> str:
    return x_actor or "anonymous"


def get_financial_service(db: Session = Depends(get_db)) -> FinancialService:
    return FinancialService(
        tx_gateway=TransactionGateway(db),
        idem_gateway=IdempotencyGateway(db),
        audit_gateway=AuditGateway(db),
    )


def get_plugin_service(db: Session = Depends(get_db)) -> PluginService:
    return PluginService(db=db)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(
        gateway=NotificationGateway(db),
        audit_gateway=AuditGateway(db),
    )
