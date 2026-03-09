from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.domain.models.access_control import AccessResource


class AccessControlGateway:
    def __init__(self, db: Session):
        self.db = db

    def list_resources(self, *, resource_type: str | None = None, active_only: bool = True) -> list[AccessResource]:
        query = self.db.query(AccessResource)
        if resource_type:
            query = query.filter(AccessResource.resource_type == resource_type)
        if active_only:
            query = query.filter(AccessResource.is_active.is_(True))
        return query.order_by(AccessResource.resource_type.asc(), AccessResource.resource_key.asc()).all()

    def upsert_resource(
        self,
        *,
        resource_key: str,
        resource_type: str,
        name: str,
        path: str | None,
        http_method: str | None,
        parent_key: str | None,
        metadata: dict,
        is_active: bool,
    ) -> AccessResource:
        existing = self.db.query(AccessResource).filter(AccessResource.resource_key == resource_key).first()
        if existing:
            existing.resource_type = resource_type
            existing.name = name
            existing.path = path
            existing.http_method = http_method
            existing.parent_key = parent_key
            existing.metadata_json = json.dumps(metadata, default=str)
            existing.is_active = is_active
            self.db.flush()
            return existing

        item = AccessResource(
            resource_key=resource_key,
            resource_type=resource_type,
            name=name,
            path=path,
            http_method=http_method,
            parent_key=parent_key,
            metadata_json=json.dumps(metadata, default=str),
            is_active=is_active,
        )
        self.db.add(item)
        self.db.flush()
        return item
