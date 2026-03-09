from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    get_access_control_service,
    get_principal,
    get_request_id,
    require_security_admin,
)
from app.application.services.access_control_service import AccessControlService
from app.core.config import settings
from app.core.security import Principal, principal_subjects
from app.domain.schemas.access_control import (
    AccessResourceListResponse,
    AccessResourcePayload,
    AuthorizePayload,
    AuthorizeResponse,
    BatchAuthorizePayload,
    BatchAuthorizeResponse,
    BatchAuthorizeResult,
    CasbinGroupingListResponse,
    CasbinGroupingPayload,
    CasbinPolicyListResponse,
    CasbinPolicyPayload,
    EnforceCheckPayload,
    EnforceCheckResponse,
)
from app.core.casbin_enforcer import enforce

router = APIRouter(prefix="/access-control", tags=["access-control"])


@router.get("/whoami", summary="Identidade do usuário autenticado")
def whoami(principal: Principal = Depends(get_principal)) -> dict:
    return {
        "authenticated": principal.authenticated,
        "username": principal.username,
        "subject": principal.subject,
        "roles": list(principal.roles),
        "groups": list(principal.groups),
        "subjects": principal_subjects(principal),
        "auth_enabled": settings.auth_enabled,
        "authz_enabled": settings.authz_enabled,
    }


@router.post("/authorize", response_model=AuthorizeResponse, summary="Validar autorização do usuário atual")
def authorize_current_user(
    payload: AuthorizePayload,
    principal: Principal = Depends(get_principal),
) -> AuthorizeResponse:
    allowed = enforce(principal=principal, resource=payload.resource, action=payload.action)
    return AuthorizeResponse(allowed=allowed, resource=payload.resource, action=payload.action)


@router.post("/authorize/batch", response_model=BatchAuthorizeResponse, summary="Validar autorização em lote")
def authorize_batch(
    payload: BatchAuthorizePayload,
    principal: Principal = Depends(get_principal),
) -> BatchAuthorizeResponse:
    items = [
        BatchAuthorizeResult(
            resource=item.resource,
            action=item.action,
            allowed=enforce(principal=principal, resource=item.resource, action=item.action),
        )
        for item in payload.items
    ]
    return BatchAuthorizeResponse(items=items, total=len(items))


@router.get("/resources", response_model=AccessResourceListResponse, summary="Listar catálogo de recursos")
def list_resources(
    resource_type: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    _: Principal = Depends(require_security_admin),
    service: AccessControlService = Depends(get_access_control_service),
) -> AccessResourceListResponse:
    items = service.list_resources(resource_type=resource_type, active_only=active_only)
    return AccessResourceListResponse(items=items, total=len(items))


@router.post("/resources/upsert", response_model=AccessResourceListResponse, summary="Upsert de recursos")
def upsert_resources(
    payload: list[AccessResourcePayload],
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> AccessResourceListResponse:
    items = service.upsert_resources(payloads=payload, actor=principal.actor, request_id=request_id)
    return AccessResourceListResponse(items=items, total=len(items))


@router.post("/resources/sync-api", summary="Sincronizar catálogo de APIs com rotas FastAPI")
def sync_api_resources(
    request: Request,
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> dict:
    return service.sync_api_resources(routes=request.app.routes, actor=principal.actor, request_id=request_id)


@router.get("/policies", response_model=CasbinPolicyListResponse, summary="Listar políticas Casbin")
def list_policies(
    _: Principal = Depends(require_security_admin),
    service: AccessControlService = Depends(get_access_control_service),
) -> CasbinPolicyListResponse:
    items = service.list_policies()
    return CasbinPolicyListResponse(items=items, total=len(items))


@router.post("/policies", summary="Adicionar política Casbin")
def add_policy(
    payload: CasbinPolicyPayload,
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> dict:
    return {"added": service.add_policy(payload=payload, actor=principal.actor, request_id=request_id)}


@router.delete("/policies", summary="Remover política Casbin")
def remove_policy(
    payload: CasbinPolicyPayload,
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> dict:
    return {"removed": service.remove_policy(payload=payload, actor=principal.actor, request_id=request_id)}


@router.get("/grouping", response_model=CasbinGroupingListResponse, summary="Listar agrupamentos Casbin")
def list_grouping(
    _: Principal = Depends(require_security_admin),
    service: AccessControlService = Depends(get_access_control_service),
) -> CasbinGroupingListResponse:
    items = service.list_grouping()
    return CasbinGroupingListResponse(items=items, total=len(items))


@router.post("/grouping", summary="Adicionar agrupamento Casbin")
def add_grouping(
    payload: CasbinGroupingPayload,
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> dict:
    return {"added": service.add_grouping(payload=payload, actor=principal.actor, request_id=request_id)}


@router.delete("/grouping", summary="Remover agrupamento Casbin")
def remove_grouping(
    payload: CasbinGroupingPayload,
    principal: Principal = Depends(require_security_admin),
    request_id: str = Depends(get_request_id),
    service: AccessControlService = Depends(get_access_control_service),
) -> dict:
    return {"removed": service.remove_grouping(payload=payload, actor=principal.actor, request_id=request_id)}


@router.post("/check", response_model=EnforceCheckResponse, summary="Simular decisão de autorização")
def check(
    payload: EnforceCheckPayload,
    _: Principal = Depends(require_security_admin),
    service: AccessControlService = Depends(get_access_control_service),
) -> EnforceCheckResponse:
    return EnforceCheckResponse(allowed=service.check(subjects=payload.subjects, resource=payload.resource, action=payload.action))
