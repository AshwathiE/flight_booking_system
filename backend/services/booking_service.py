import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.booking import Booking
from backend.models.flight import Flight
from backend.models.user import User


def generate_booking_reference(db: Session) -> str:
    """
    Generate a unique booking reference formatted like: BK202608140001
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    
    for _ in range(100):
        # Generate 4 random digits/chars or sequential count
        random_suffix = "".join(random.choices(string.digits, k=4))
        ref = f"BK{date_str}{random_suffix}"
        
        existing = db.query(Booking).filter(Booking.booking_reference == ref).first()
        if not existing:
            return ref
            
    # Fallback with timestamp microsecond
    return f"BK{date_str}{datetime.utcnow().microsecond:06d}"[:16]


class BookingService:

    @staticmethod
    def create_booking(
        db: Session,
        user_id: int,
        flight_id: str,
        number_of_seats: int
    ) -> dict:
        if number_of_seats <= 0:
            return {
                "success": False,
                "error": "INVALID_SEAT_COUNT",
                "message": "Number of seats must be greater than zero."
            }

        try:
            # 1. Validate User
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "USER_NOT_FOUND",
                    "message": f"User with ID {user_id} does not exist."
                }

            # 2. Lock flight row and check flight existence
            flight = db.query(Flight).filter(
                Flight.flight_id == flight_id
            ).with_for_update().first()

            if not flight:
                return {
                    "success": False,
                    "error": "FLIGHT_NOT_FOUND",
                    "message": f"Flight {flight_id} not found."
                }

            # 3. Check seat availability and perform atomic seat deduction
            updated_rows = db.query(Flight).filter(
                Flight.flight_id == flight_id,
                Flight.available_seats >= number_of_seats
            ).update(
                {Flight.available_seats: Flight.available_seats - number_of_seats},
                synchronize_session=False
            )

            if updated_rows == 0:
                return {
                    "success": False,
                    "error": "NOT_ENOUGH_SEATS",
                    "message": f"Only {flight.available_seats} seat(s) available."
                }

            # 4. Calculate total price
            total_price = float(flight.price) * number_of_seats

            # 5. Generate reference and create booking
            ref = generate_booking_reference(db)

            booking = Booking(
                booking_reference=ref,
                user_id=user_id,
                flight_id=flight_id,
                number_of_seats=number_of_seats,
                total_price=total_price,
                status="CONFIRMED"
            )

            # 6. Persist in same transaction
            db.add(booking)
            db.commit()
            db.refresh(booking)

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "user_id": booking.user_id,
                "flight_id": booking.flight_id,
                "number_of_seats": booking.number_of_seats,
                "total_price": booking.total_price,
                "status": booking.status,
                "created_at": str(booking.created_at)
            }

        except Exception as exc:
            try:
                db.rollback()
            except Exception:
                pass
            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to create booking: {str(exc)}"
            }

    @staticmethod
    def get_booking(
        db: Session,
        booking_id: int,
        requesting_user_id: int | None = None,
        is_admin: bool = False
    ) -> dict:
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": f"Booking with ID {booking_id} not found."
                }

            if requesting_user_id is not None and not is_admin:
                if booking.user_id != requesting_user_id:
                    return {
                        "success": False,
                        "error": "BOOKING_NOT_OWNED",
                        "message": "You are not authorized to view this booking."
                    }

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "user_id": booking.user_id,
                "flight_id": booking.flight_id,
                "number_of_seats": booking.number_of_seats,
                "total_price": float(booking.total_price),
                "status": booking.status,
                "created_at": str(booking.created_at)
            }

        except Exception as exc:
            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc)
            }

    @staticmethod
    def get_user_bookings(
        db: Session,
        user_id: int
    ) -> dict:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "USER_NOT_FOUND",
                    "message": f"User with ID {user_id} not found."
                }

            bookings = db.query(Booking).filter(Booking.user_id == user_id).all()

            return {
                "success": True,
                "bookings": [
                    {
                        "booking_id": b.id,
                        "booking_reference": b.booking_reference,
                        "user_id": b.user_id,
                        "flight_id": b.flight_id,
                        "number_of_seats": b.number_of_seats,
                        "total_price": float(b.total_price),
                        "status": b.status,
                        "created_at": str(b.created_at)
                    }
                    for b in bookings
                ]
            }

        except Exception as exc:
            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc)
            }

    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        user_id: int
    ) -> dict:
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": f"Booking with ID {booking_id} not found."
                }

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_OWNED",
                    "message": "You are not authorized to cancel this booking."
                }

            if booking.status == "CANCELLED":
                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CANCELLED",
                    "message": "Booking is already cancelled."
                }

            # Lock flight row and return seats
            flight = db.query(Flight).filter(
                Flight.flight_id == booking.flight_id
            ).with_for_update().first()

            booking.status = "CANCELLED"

            if flight:
                flight.available_seats += booking.number_of_seats

            db.commit()
            db.refresh(booking)

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "user_id": booking.user_id,
                "flight_id": booking.flight_id,
                "number_of_seats": booking.number_of_seats,
                "total_price": float(booking.total_price),
                "status": booking.status,
                "created_at": str(booking.created_at),
                "available_seats": flight.available_seats if flight else None
            }

        except Exception as exc:
            try:
                db.rollback()
            except Exception:
                pass
            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to cancel booking: {str(exc)}"
            }

    @staticmethod
    def change_booking(
        db: Session,
        booking_id: int,
        user_id: int,
        new_flight_id: str,
        new_number_of_seats: int
    ) -> dict:
        if new_number_of_seats <= 0:
            return {
                "success": False,
                "error": "INVALID_SEAT_COUNT",
                "message": "Number of seats must be greater than zero."
            }

        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": f"Booking with ID {booking_id} not found."
                }

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_OWNED",
                    "message": "You are not authorized to modify this booking."
                }

            if booking.status == "CANCELLED":
                return {
                    "success": False,
                    "error": "INVALID_BOOKING_STATUS",
                    "message": "Cannot change a cancelled booking."
                }

            # Lock old flight and new flight rows
            old_flight = db.query(Flight).filter(
                Flight.flight_id == booking.flight_id
            ).with_for_update().first()

            new_flight = db.query(Flight).filter(
                Flight.flight_id == new_flight_id
            ).with_for_update().first()

            if not new_flight:
                return {
                    "success": False,
                    "error": "FLIGHT_NOT_FOUND",
                    "message": f"Target flight {new_flight_id} not found."
                }

            # Release seats on old flight first within transaction
            if old_flight:
                db.query(Flight).filter(
                    Flight.flight_id == booking.flight_id
                ).update(
                    {Flight.available_seats: Flight.available_seats + booking.number_of_seats},
                    synchronize_session=False
                )

            # Atomically reserve seats on new flight
            updated_rows = db.query(Flight).filter(
                Flight.flight_id == new_flight_id,
                Flight.available_seats >= new_number_of_seats
            ).update(
                {Flight.available_seats: Flight.available_seats - new_number_of_seats},
                synchronize_session=False
            )

            if updated_rows == 0:
                try:
                    db.rollback()
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": "NOT_ENOUGH_SEATS",
                    "message": f"Only {new_flight.available_seats} seat(s) available on flight {new_flight_id}."
                }

            # Update booking details
            booking.flight_id = new_flight_id
            booking.number_of_seats = new_number_of_seats
            booking.total_price = float(new_flight.price) * new_number_of_seats

            db.commit()
            db.refresh(booking)

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "user_id": booking.user_id,
                "flight_id": booking.flight_id,
                "number_of_seats": booking.number_of_seats,
                "total_price": float(booking.total_price),
                "status": booking.status,
                "created_at": str(booking.created_at)
            }

        except Exception as exc:
            db.rollback()
            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to change booking: {str(exc)}"
            }
