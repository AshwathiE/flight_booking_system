from sqlalchemy.orm import Session
from backend.models.payment import Payment

class PaymentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_payment(
        self,
        payment_id: str,
        booking_id: int,
        user_id: int,
        amount: float,
        currency: str,
        payment_method: str,
        status: str = "PENDING"
    ) -> Payment:
        payment = Payment(
            payment_id=payment_id,
            booking_id=booking_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=status
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payment_by_id(self, payment_id: str) -> Payment | None:
        return self.db.query(Payment).filter(
            Payment.payment_id == payment_id
        ).first()

    def get_payment_by_booking_id(self, booking_id: int) -> Payment | None:
        return self.db.query(Payment).filter(
            Payment.booking_id == booking_id
        ).first()

    def update_payment(self, payment: Payment) -> Payment:
        self.db.commit()
        self.db.refresh(payment)
        return payment
