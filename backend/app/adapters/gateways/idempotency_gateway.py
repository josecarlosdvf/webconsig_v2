import hashlib
import json
from sqlalchemy.orm import Session

from app.domain.models.idempotency import IdempotencyRecord


class IdempotencyGateway:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def request_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get_exact(self, *, key: str, endpoint: str, request_hash: str) -> IdempotencyRecord | None:
        return (
            self.db.query(IdempotencyRecord)
            .filter_by(key=key, endpoint=endpoint, request_hash=request_hash)
            .first()
        )

    def get_by_key_endpoint(self, *, key: str, endpoint: str) -> IdempotencyRecord | None:
        return self.db.query(IdempotencyRecord).filter_by(key=key, endpoint=endpoint).first()

    def save(
        self,
        *,
        key: str,
        endpoint: str,
        request_hash: str,
        status_code: int,
        response_body: str,
    ) -> None:
        record = IdempotencyRecord(
            key=key,
            endpoint=endpoint,
            request_hash=request_hash,
            status_code=status_code,
            response_body=response_body,
        )
        self.db.add(record)
        self.db.flush()
