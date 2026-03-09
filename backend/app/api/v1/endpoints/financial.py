from fastapi import APIRouter, Depends, Header, status

from app.api.deps import get_actor, get_financial_service, get_request_id
from app.application.services.financial_service import FinancialService
from app.domain.schemas.finance import FinancialCreateRequest, FinancialCreateResponse

router = APIRouter(prefix="/financial", tags=["financial"])


@router.post(
    "/transactions",
    response_model=FinancialCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar transação financeira (idempotente)",
)
def create_transaction(
    payload: FinancialCreateRequest,
    service: FinancialService = Depends(get_financial_service),
    request_id: str = Depends(get_request_id),
    actor: str = Depends(get_actor),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> FinancialCreateResponse:
    return service.create_transaction(
        payload=payload,
        idempotency_key=idempotency_key,
        endpoint="/financial/transactions",
        actor=actor,
        request_id=request_id,
    )
