from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class FinancialCreateRequest(StrictSchema):
    external_ref: str = Field(min_length=3, max_length=64)
    customer_document: str = Field(min_length=11, max_length=20)
    amount: float = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=8)


class FinancialCreateResponse(StrictSchema):
    id: str
    external_ref: str
    status: str
    amount: Decimal
    currency: str
    created_at: datetime
    replayed: bool = False
