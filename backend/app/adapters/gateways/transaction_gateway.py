from sqlalchemy.orm import Session

from app.domain.models.financial import FinancialTransaction


class TransactionGateway:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        external_ref: str,
        customer_document: str,
        amount,
        currency: str,
    ) -> FinancialTransaction:
        txn = FinancialTransaction(
            external_ref=external_ref,
            customer_document=customer_document,
            amount=amount,
            currency=currency,
        )
        self.db.add(txn)
        self.db.flush()
        return txn
