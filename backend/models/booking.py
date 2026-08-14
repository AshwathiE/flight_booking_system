from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.connection import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    booking_reference = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    flight_id = Column(
        String,
        ForeignKey("flights.flight_id"),
        nullable=False,
        index=True
    )

    number_of_seats = Column(
        Integer,
        nullable=False
    )

    total_price = Column(
        Float,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="CONFIRMED"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user = relationship("User", backref="bookings")
    flight = relationship("Flight", backref="bookings")
