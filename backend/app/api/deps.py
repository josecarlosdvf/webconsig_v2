import uuid
from typing import Callable

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.adapters.gateways.audit_gateway import AuditGateway
from app.adapters.gateways.access_control_gateway import AccessControlGateway
from app.adapters.gateways.idempotency_gateway import IdempotencyGateway
from app.adapters.gateways.notification_gateway import NotificationGateway
from app.adapters.gateways.transaction_gateway import TransactionGateway
from app.application.services.access_control_service import AccessControlService
from app.application.services.financial_service import FinancialService
from app.application.services.notification_service import NotificationService
from app.application.services.plugin_service import PluginService
from app.core.casbin_enforcer import enforce
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.keycloak import decode_keycloak_token, principal_from_claims
from app.core.security import Principal, anonymous_principal

_bearer = HTTPBearer(auto_error=False)


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


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_actor: str | None = Header(default=None, alias="X-Actor"),
) -> Principal:
    if settings.auth_enabled:
        if not credentials or not credentials.credentials:
            if settings.auth_allow_dev_header_fallback and x_actor:
                roles = ("admin",) if x_actor == "admin" else tuple()
                return Principal(
                    subject=f"dev:{x_actor}",
                    username=x_actor,
                    email=None,
                    roles=roles,
                    groups=tuple(),
                    authenticated=True,
                )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token obrigatório")

        claims = decode_keycloak_token(credentials.credentials)
        return principal_from_claims(claims)

    return anonymous_principal(actor=x_actor or "anonymous")


def get_actor(principal: Principal = Depends(get_principal)) -> str:
    return principal.actor


def require_security_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if not principal.authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")
    if "admin" not in principal.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão administrativa necessária")
    return principal


def require_permission(resource: str, action: str) -> Callable:
    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not settings.authz_enabled:
            return principal

        if enforce(principal=principal, resource=resource, action=action):
            return principal

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado pela política")

    return _dependency


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


def get_access_control_service(db: Session = Depends(get_db)) -> AccessControlService:
    return AccessControlService(
        gateway=AccessControlGateway(db),
        audit_gateway=AuditGateway(db),
    )
