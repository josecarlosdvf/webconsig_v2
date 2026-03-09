from __future__ import annotations

import json
from typing import Iterable

from fastapi.routing import APIRoute

from app.adapters.gateways.access_control_gateway import AccessControlGateway
from app.adapters.gateways.audit_gateway import AuditGateway
from app.core.casbin_enforcer import get_enforcer, reload_enforcer
from app.domain.models.access_control import AccessResource
from app.domain.schemas.access_control import (
    AccessResourcePayload,
    AccessResourceResponse,
    CasbinGroupingPayload,
    CasbinGroupingResponse,
    CasbinPolicyPayload,
    CasbinPolicyResponse,
)


class AccessControlService:
    def __init__(self, *, gateway: AccessControlGateway, audit_gateway: AuditGateway):
        self.gateway = gateway
        self.audit_gateway = audit_gateway

    @staticmethod
    def _resource_to_response(item: AccessResource) -> AccessResourceResponse:
        try:
            metadata = json.loads(item.metadata_json)
        except Exception:
            metadata = {}

        return AccessResourceResponse(
            id=item.id,
            resource_key=item.resource_key,
            resource_type=item.resource_type,
            name=item.name,
            path=item.path,
            http_method=item.http_method,
            parent_key=item.parent_key,
            metadata=metadata,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def list_resources(self, *, resource_type: str | None, active_only: bool) -> list[AccessResourceResponse]:
        items = self.gateway.list_resources(resource_type=resource_type, active_only=active_only)
        return [self._resource_to_response(item) for item in items]

    def upsert_resources(self, *, payloads: list[AccessResourcePayload], actor: str, request_id: str) -> list[AccessResourceResponse]:
        result: list[AccessResourceResponse] = []
        for payload in payloads:
            item = self.gateway.upsert_resource(
                resource_key=payload.resource_key,
                resource_type=payload.resource_type,
                name=payload.name,
                path=payload.path,
                http_method=payload.http_method,
                parent_key=payload.parent_key,
                metadata=payload.metadata,
                is_active=payload.is_active,
            )
            result.append(self._resource_to_response(item))

        self.audit_gateway.append(
            area="security",
            action="resource_catalog.upsert",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="access_resources",
            severity="INFO",
            detail={"count": len(result)},
        )
        return result

    def sync_api_resources(self, *, routes: Iterable, actor: str, request_id: str) -> dict:
        payloads: list[AccessResourcePayload] = []

        for route in routes:
            if not isinstance(route, APIRoute):
                continue

            path = route.path
            if not path.startswith("/api/"):
                continue
            if path.startswith("/api/v1/health"):
                continue

            methods = sorted(method for method in route.methods if method in {"GET", "POST", "PUT", "PATCH", "DELETE"})
            for method in methods:
                payloads.append(
                    AccessResourcePayload(
                        resource_key=f"api:{path}:{method}",
                        resource_type="api",
                        name=route.name,
                        path=path,
                        http_method=method,
                        metadata={"tags": route.tags},
                    )
                )

        items = self.upsert_resources(payloads=payloads, actor=actor, request_id=request_id)
        return {"total": len(items)}

    def list_policies(self) -> list[CasbinPolicyResponse]:
        enforcer = get_enforcer()
        policies = enforcer.get_policy()
        return [
            CasbinPolicyResponse(
                priority=item[0],
                subject=item[1],
                resource_regex=item[2],
                action_regex=item[3],
                effect=item[4],
            )
            for item in policies
        ]

    def add_policy(self, *, payload: CasbinPolicyPayload, actor: str, request_id: str) -> bool:
        enforcer = get_enforcer()
        added = enforcer.add_policy(
            payload.priority,
            payload.subject,
            payload.resource_regex,
            payload.action_regex,
            payload.effect,
        )
        reload_enforcer()

        self.audit_gateway.append(
            area="security",
            action="casbin.policy.add",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="casbin_policy",
            severity="INFO",
            detail=payload.model_dump(),
        )
        return bool(added)

    def remove_policy(self, *, payload: CasbinPolicyPayload, actor: str, request_id: str) -> bool:
        enforcer = get_enforcer()
        removed = enforcer.remove_policy(
            payload.priority,
            payload.subject,
            payload.resource_regex,
            payload.action_regex,
            payload.effect,
        )
        reload_enforcer()

        self.audit_gateway.append(
            area="security",
            action="casbin.policy.remove",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="casbin_policy",
            severity="INFO",
            detail=payload.model_dump(),
        )
        return bool(removed)

    def list_grouping(self) -> list[CasbinGroupingResponse]:
        enforcer = get_enforcer()
        groups = enforcer.get_grouping_policy()
        return [CasbinGroupingResponse(subject=item[0], role=item[1]) for item in groups]

    def add_grouping(self, *, payload: CasbinGroupingPayload, actor: str, request_id: str) -> bool:
        enforcer = get_enforcer()
        added = enforcer.add_grouping_policy(payload.subject, payload.role)
        reload_enforcer()

        self.audit_gateway.append(
            area="security",
            action="casbin.grouping.add",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="casbin_grouping",
            severity="INFO",
            detail=payload.model_dump(),
        )
        return bool(added)

    def remove_grouping(self, *, payload: CasbinGroupingPayload, actor: str, request_id: str) -> bool:
        enforcer = get_enforcer()
        removed = enforcer.remove_grouping_policy(payload.subject, payload.role)
        reload_enforcer()

        self.audit_gateway.append(
            area="security",
            action="casbin.grouping.remove",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="casbin_grouping",
            severity="INFO",
            detail=payload.model_dump(),
        )
        return bool(removed)

    def check(self, *, subjects: str, resource: str, action: str) -> bool:
        enforcer = get_enforcer()
        return bool(enforcer.enforce(subjects, resource, action))
