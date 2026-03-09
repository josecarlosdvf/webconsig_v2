import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_ref: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_document: Mapped[str] = mapped_column(String(20), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="BRL")
    status: Mapped[str] = mapped_column(String(20), default="CREATED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
