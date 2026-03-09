import json
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.adapters.gateways.audit_gateway import AuditGateway
from app.adapters.gateways.idempotency_gateway import IdempotencyGateway
from app.adapters.gateways.transaction_gateway import TransactionGateway
from app.domain.schemas.finance import FinancialCreateRequest, FinancialCreateResponse
from app.events.publisher import EventPublisher


class FinancialService:
    def __init__(
        self,
        *,
        tx_gateway: TransactionGateway,
        idem_gateway: IdempotencyGateway,
        audit_gateway: AuditGateway,
    ):
        self.tx_gateway = tx_gateway
        self.idem_gateway = idem_gateway
        self.audit_gateway = audit_gateway

    def create_transaction(
        self,
        *,
        payload: FinancialCreateRequest,
        idempotency_key: str,
        endpoint: str,
        actor: str,
        request_id: str,
    ) -> FinancialCreateResponse:
        if not idempotency_key or len(idempotency_key) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key inválido")

        req_hash = self.idem_gateway.request_hash(payload.model_dump(mode="json"))
        cached_for_key = self.idem_gateway.get_by_key_endpoint(key=idempotency_key, endpoint=endpoint)
        if cached_for_key:
            if cached_for_key.request_hash != req_hash:
                self.audit_gateway.append(
                    area="financeiro",
                    action="transaction.idempotency_conflict",
                    actor=actor,
                    request_id=request_id,
                    detail={
                        "idempotency_key": idempotency_key,
                        "endpoint": endpoint,
                        "reason": "same_key_different_payload",
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency-Key já utilizada com payload diferente",
                )

            parsed_response = FinancialCreateResponse.model_validate_json(cached_for_key.response_body)
            replayed_response = parsed_response.model_copy(update={"replayed": True})
            self.audit_gateway.append(
                area="financeiro",
                action="transaction.replayed",
                actor=actor,
                request_id=request_id,
                detail={
                    "idempotency_key": idempotency_key,
                    "endpoint": endpoint,
                    "response": replayed_response.model_dump(mode="json"),
                },
            )
            return replayed_response

        try:
            txn = self.tx_gateway.create(
                external_ref=payload.external_ref,
                customer_document=payload.customer_document,
                amount=Decimal(str(payload.amount)),
                currency=payload.currency,
            )
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="external_ref já existe para outra operação",
            ) from exc

        response = FinancialCreateResponse(
            id=txn.id,
            external_ref=txn.external_ref,
            status=txn.status,
            amount=txn.amount,
            currency=txn.currency,
            created_at=txn.created_at,
        )
        try:
            self.idem_gateway.save(
                key=idempotency_key,
                endpoint=endpoint,
                request_hash=req_hash,
                status_code=status.HTTP_201_CREATED,
                response_body=response.model_dump_json(),
            )
        except IntegrityError:
            cached_for_key = self.idem_gateway.get_by_key_endpoint(key=idempotency_key, endpoint=endpoint)
            if cached_for_key and cached_for_key.request_hash == req_hash:
                parsed_response = FinancialCreateResponse.model_validate_json(cached_for_key.response_body)
                replayed_response = parsed_response.model_copy(update={"replayed": True})
                self.audit_gateway.append(
                    area="financeiro",
                    action="transaction.replayed",
                    actor=actor,
                    request_id=request_id,
                    detail={
                        "idempotency_key": idempotency_key,
                        "endpoint": endpoint,
                        "response": replayed_response.model_dump(mode="json"),
                    },
                )
                return replayed_response
            raise
        self.audit_gateway.append(
            area="financeiro",
            action="transaction.created",
            actor=actor,
            request_id=request_id,
            detail=response.model_dump(mode="json"),
        )
        EventPublisher.publish(
            "finance.transaction.created",
            {"transaction_id": txn.id, "external_ref": txn.external_ref, "amount": str(txn.amount)},
        )
        return response
