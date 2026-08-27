from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from backend.database.connection import Base


IST = ZoneInfo("Asia/Kolkata")


class Payment(Base):
    __tablename__ = "payments"

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    # ============================================================
    # PAYMENT ID
    # ============================================================
    #
    # Internal/payment-gateway reference.
    #
    # Example:
    # PAY20260825123456
    #
    # ============================================================

    payment_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # ============================================================
    # BOOKING
    # ============================================================

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )

    # ============================================================
    # USER
    # ============================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # ============================================================
    # PAYMENT AMOUNT
    # ============================================================

    amount = Column(
        Float,
        nullable=False,
    )

    # ============================================================
    # CURRENCY
    # ============================================================

    currency = Column(
        String(10),
        nullable=False,
        default="INR",
    )

    # ============================================================
    # PAYMENT METHOD
    # ============================================================
    #
    # Examples:
    # CARD
    # UPI
    # NET_BANKING
    # WALLET
    #
    # ============================================================

    payment_method = Column(
        String(30),
        nullable=False,
    )

    # ============================================================
    # PAYMENT STATUS
    # ============================================================
    #
    # PENDING
    # PROCESSING
    # SUCCESS
    # FAILED
    # REFUNDED
    #
    # ============================================================

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    # ============================================================
    # GATEWAY TRANSACTION ID
    # ============================================================

    transaction_id = Column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    # ============================================================
    # REFUND ID
    # ============================================================

    refund_id = Column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    # ============================================================
    # FAILURE REASON
    # ============================================================

    failure_reason = Column(
        String(255),
        nullable=True,
    )

    # ============================================================
    # CREATED AT
    # ============================================================

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),
        nullable=False,
    )

    # ============================================================
    # UPDATED AT
    # ============================================================

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),
        onupdate=lambda: datetime.now(IST),
        nullable=False,
    )

    # ============================================================
    # RELATIONSHIPS
    # ============================================================

    user = relationship(
        "User",
        backref="payments",
    )

    booking = relationship(
        "Booking",
        backref="payments",
    )