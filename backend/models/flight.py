from sqlalchemy import Column, String, Float, Integer,Date
from backend.database.connection import Base


class Flight(Base):
    __tablename__ = "flights"

    flight_id = Column(
        String,
        primary_key=True,
        index=True
    )

    airline = Column(
        String,
        nullable=False
    )

    origin = Column(
        String,
        nullable=False
    )

    destination = Column(
        String,
        nullable=False
    )

    date = Column(
        Date,
        nullable=False
    )

    departure_time = Column(
        String,
        nullable=False
    )

    arrival_time = Column(
        String,
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    travel_class = Column(
        String,
        nullable=False
    )

    available_seats = Column(
        Integer,
        nullable=False
    )