import logging
import random
import string
import threading

from sqlalchemy.orm import Session

from backend.models.booking import Booking
from backend.models.flight import Flight
from backend.models.user import User

from backend.utils.datetime_utils import (
    get_current_datetime_kolkata,
    parse_flight_departure_datetime,
    is_flight_in_future,
)

logger = logging.getLogger("booking_service")


# ============================================================
# CONSTANTS
# ============================================================

TAX_PERCENTAGE = 5.0
SERVICE_FEE_PER_SEAT = 100.0


# ============================================================
# BOOKING STATUS
# ============================================================

BOOKING_PENDING_PAYMENT = "PENDING_PAYMENT"
BOOKING_CONFIRMED = "CONFIRMED"
BOOKING_CANCELLED = "CANCELLED"


# ============================================================
# PAYMENT STATUS
# ============================================================

PAYMENT_PENDING = "PENDING"
PAYMENT_SUCCESS = "SUCCESS"
PAYMENT_FAILED = "FAILED"
PAYMENT_REFUNDED = "REFUNDED"


# ============================================================
# FARE CALCULATION
# ============================================================

def calculate_fare(
    base_price: float,
    number_of_seats: int,
) -> dict:
    """
    Calculate the complete booking fare.

    Example:
        Flight price = ₹5000
        Seats = 2

        Base Fare = ₹10000
        Tax       = ₹500
        Service   = ₹200
        Total     = ₹10700
    """

    base_fare = round(
        float(base_price) * number_of_seats,
        2,
    )

    tax_amount = round(
        base_fare * TAX_PERCENTAGE / 100,
        2,
    )

    service_fee = round(
        SERVICE_FEE_PER_SEAT * number_of_seats,
        2,
    )

    total_price = round(
        base_fare + tax_amount + service_fee,
        2,
    )

    return {
        "base_fare": base_fare,
        "tax_amount": tax_amount,
        "service_fee": service_fee,
        "total_price": total_price,
    }


# ============================================================
# BOOKING REFERENCE
# ============================================================

def generate_booking_reference(db: Session) -> str:
    """
    Generate a unique booking reference.

    Example:
        BK202608251234
    """

    current_dt = get_current_datetime_kolkata()
    date_str = current_dt.strftime("%Y%m%d")

    for _ in range(100):
        random_suffix = "".join(
            random.choices(
                string.digits,
                k=4,
            )
        )

        reference = f"BK{date_str}{random_suffix}"

        existing = (
            db.query(Booking)
            .filter(
                Booking.booking_reference == reference
            )
            .first()
        )

        if not existing:
            return reference

    # Extremely unlikely fallback
    return (
        f"BK{date_str}{current_dt.microsecond:06d}"
    )[:18]


# ============================================================
# BOOKING SERVICE
# ============================================================

class BookingService:

    # Protect seat operations inside this application process.
    _seat_lock = threading.Lock()

    # ========================================================
    # CREATE BOOKING
    # ========================================================

    @staticmethod
    def create_booking(
        db: Session,
        user_id: int,
        flight_id: str,
        number_of_seats: int,
    ) -> dict:
        """
        Create a booking and reserve seats.

        New booking:

            status = PENDING_PAYMENT
            payment_status = PENDING

        The booking becomes CONFIRMED only after
        successful payment.
        """

        if number_of_seats <= 0:
            return {
                "success": False,
                "error": "INVALID_SEAT_COUNT",
                "message": "Number of seats must be greater than zero.",
            }

        BookingService._seat_lock.acquire()

        try:
            # ------------------------------------------------
            # 1. Validate user
            # ------------------------------------------------

            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                return {
                    "success": False,
                    "error": "USER_NOT_FOUND",
                    "message": (
                        f"User with ID {user_id} does not exist."
                    ),
                }

            # ------------------------------------------------
            # 2. Get and lock flight
            # ------------------------------------------------

            flight = (
                db.query(Flight)
                .filter(Flight.flight_id == flight_id)
                .with_for_update()
                .first()
            )

            if not flight:
                return {
                    "success": False,
                    "error": "FLIGHT_NOT_FOUND",
                    "message": (
                        f"Flight {flight_id} not found."
                    ),
                }

            # ------------------------------------------------
            # 3. Validate departure time
            # ------------------------------------------------

            current_dt = get_current_datetime_kolkata()

            flight_dt = parse_flight_departure_datetime(
                flight.date,
                flight.departure_time,
            )

            logger.info(
                "Booking validation | Flight=%s | Current=%s | Departure=%s",
                flight_id,
                current_dt,
                flight_dt,
            )

            if not flight_dt:
                return {
                    "success": False,
                    "error": "INVALID_FLIGHT_DATETIME",
                    "message": (
                        f"Unable to determine departure time "
                        f"for flight {flight_id}."
                    ),
                }

            if flight_dt <= current_dt:
                return {
                    "success": False,
                    "error": "FLIGHT_DEPARTED",
                    "message": (
                        f"Flight {flight_id} has already departed "
                        f"and cannot be booked."
                    ),
                }

            # ------------------------------------------------
            # 4. Check seats
            # ------------------------------------------------

            if flight.available_seats < number_of_seats:
                return {
                    "success": False,
                    "error": "NOT_ENOUGH_SEATS",
                    "message": (
                        f"Only {flight.available_seats} seat(s) available."
                    ),
                }

            # ------------------------------------------------
            # 5. Calculate fare
            # ------------------------------------------------

            fare = calculate_fare(
                base_price=float(flight.price),
                number_of_seats=number_of_seats,
            )

            logger.info(
                "Fare calculated | Flight=%s | Seats=%s | "
                "Base=%s | Tax=%s | Service=%s | Total=%s",
                flight_id,
                number_of_seats,
                fare["base_fare"],
                fare["tax_amount"],
                fare["service_fee"],
                fare["total_price"],
            )

            # ------------------------------------------------
            # 6. Reserve seats
            # ------------------------------------------------

            flight.available_seats -= number_of_seats

            # ------------------------------------------------
            # 7. Generate booking reference
            # ------------------------------------------------

            booking_reference = generate_booking_reference(db)

            # ------------------------------------------------
            # 8. Create booking
            # ------------------------------------------------

            booking = Booking(
                booking_reference=booking_reference,

                user_id=user_id,
                flight_id=flight_id,

                number_of_seats=number_of_seats,

                base_fare=fare["base_fare"],
                tax_amount=fare["tax_amount"],
                service_fee=fare["service_fee"],
                total_price=fare["total_price"],

                # Booking state
                status=BOOKING_PENDING_PAYMENT,

                # Payment state
                payment_status=PAYMENT_PENDING,
                payment_id=None,
                paid_at=None,
            )

            db.add(booking)

            # ------------------------------------------------
            # 9. Commit
            # ------------------------------------------------

            db.commit()
            db.refresh(booking)

            logger.info(
                "Booking created | Booking=%s | Reference=%s | "
                "Status=%s | Payment=%s",
                booking.id,
                booking.booking_reference,
                booking.status,
                booking.payment_status,
            )

            # ------------------------------------------------
            # 10. Return
            # ------------------------------------------------

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "user_id": booking.user_id,
                "flight_id": booking.flight_id,

                "number_of_seats": booking.number_of_seats,

                "base_fare": float(booking.base_fare),
                "tax_amount": float(booking.tax_amount),
                "service_fee": float(booking.service_fee),
                "total_price": float(booking.total_price),

                "status": booking.status,

                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,
                "paid_at": None,

                "created_at": (
                    booking.created_at.isoformat()
                    if booking.created_at
                    else None
                ),

                "message": (
                    "Booking created successfully. "
                    "Payment is required to confirm the booking."
                ),
            }

        except Exception as exc:
            db.rollback()

            logger.exception("Failed to create booking")

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to create booking: {str(exc)}",
            }

        finally:
            BookingService._seat_lock.release()

    # ========================================================
    # GET BOOKING
    # ========================================================

    @staticmethod
    def get_booking(
        db: Session,
        booking_id: int,
        requesting_user_id: int | None = None,
        is_admin: bool = False,
    ) -> dict:

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking with ID {booking_id} not found."
                    ),
                }

            # ------------------------------------------------
            # Authorization
            # ------------------------------------------------

            if (
                not is_admin
                and requesting_user_id is not None
                and booking.user_id != requesting_user_id
            ):
                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized to view this booking."
                    ),
                }

            # ------------------------------------------------
            # Computed status
            # ------------------------------------------------

            if booking.status == BOOKING_CANCELLED:
                computed_status = BOOKING_CANCELLED

            elif booking.status == BOOKING_PENDING_PAYMENT:
                computed_status = BOOKING_PENDING_PAYMENT

            elif booking.flight:
                computed_status = (
                    "UPCOMING"
                    if is_flight_in_future(
                        booking.flight.date,
                        booking.flight.departure_time,
                    )
                    else "COMPLETED"
                )

            else:
                computed_status = "UPCOMING"

            # ------------------------------------------------
            # Ticket eligibility
            # ------------------------------------------------

            ticket_download_allowed = (
                booking.status == BOOKING_CONFIRMED
                and booking.payment_status == PAYMENT_SUCCESS
            )

            return {
                "success": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "user_id": booking.user_id,
                "flight_id": booking.flight_id,

                "number_of_seats": booking.number_of_seats,

                "base_fare": float(booking.base_fare),
                "tax_amount": float(booking.tax_amount),
                "service_fee": float(booking.service_fee),
                "total_price": float(booking.total_price),

                "status": booking.status,
                "computed_status": computed_status,

                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,

                "paid_at": (
                    booking.paid_at.isoformat()
                    if booking.paid_at
                    else None
                ),

                "ticket_download_allowed": (
                    ticket_download_allowed
                ),

                "created_at": (
                    booking.created_at.isoformat()
                    if booking.created_at
                    else None
                ),

                "airline": (
                    booking.flight.airline
                    if booking.flight
                    else "Unknown"
                ),

                "origin": (
                    booking.flight.origin
                    if booking.flight
                    else "Unknown"
                ),

                "destination": (
                    booking.flight.destination
                    if booking.flight
                    else "Unknown"
                ),

                "date": (
                    str(booking.flight.date)
                    if booking.flight
                    else "Unknown"
                ),

                "departure_time": (
                    booking.flight.departure_time
                    if booking.flight
                    else "Unknown"
                ),

                "arrival_time": (
                    booking.flight.arrival_time
                    if booking.flight
                    else "Unknown"
                ),

                "travel_class": (
                    booking.flight.travel_class
                    if booking.flight
                    else "Unknown"
                ),
            }

        except Exception as exc:
            logger.exception("Failed to get booking")

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # GET USER BOOKINGS
    # ========================================================

    @staticmethod
    def get_user_bookings(
        db: Session,
        user_id: int,
    ) -> dict:

        try:
            bookings = (
                db.query(Booking)
                .filter(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
                .all()
            )

            result = []

            for booking in bookings:

                if booking.status == BOOKING_CANCELLED:
                    computed_status = BOOKING_CANCELLED

                elif booking.status == BOOKING_PENDING_PAYMENT:
                    computed_status = BOOKING_PENDING_PAYMENT

                elif (
                    booking.flight
                    and is_flight_in_future(
                        booking.flight.date,
                        booking.flight.departure_time,
                    )
                ):
                    computed_status = "UPCOMING"

                else:
                    computed_status = "COMPLETED"

                ticket_download_allowed = (
                    booking.status == BOOKING_CONFIRMED
                    and booking.payment_status == PAYMENT_SUCCESS
                )

                result.append({
                    "booking_id": booking.id,

                    "booking_reference": (
                        booking.booking_reference
                    ),

                    "flight_id": booking.flight_id,

                    "number_of_seats": (
                        booking.number_of_seats
                    ),

                    "base_fare": float(booking.base_fare),
                    "tax_amount": float(booking.tax_amount),
                    "service_fee": float(booking.service_fee),
                    "total_price": float(booking.total_price),

                    "status": booking.status,
                    "computed_status": computed_status,

                    "payment_status": (
                        booking.payment_status
                    ),

                    "payment_id": booking.payment_id,

                    "paid_at": (
                        booking.paid_at.isoformat()
                        if booking.paid_at
                        else None
                    ),

                    "ticket_download_allowed": (
                        ticket_download_allowed
                    ),

                    "created_at": (
                        booking.created_at.isoformat()
                        if booking.created_at
                        else None
                    ),

                    "airline": (
                        booking.flight.airline
                        if booking.flight
                        else "Unknown"
                    ),

                    "origin": (
                        booking.flight.origin
                        if booking.flight
                        else "Unknown"
                    ),

                    "destination": (
                        booking.flight.destination
                        if booking.flight
                        else "Unknown"
                    ),

                    "date": (
                        str(booking.flight.date)
                        if booking.flight
                        else "Unknown"
                    ),

                    "departure_time": (
                        booking.flight.departure_time
                        if booking.flight
                        else "Unknown"
                    ),

                    "arrival_time": (
                        booking.flight.arrival_time
                        if booking.flight
                        else "Unknown"
                    ),

                    "travel_class": (
                        booking.flight.travel_class
                        if booking.flight
                        else "Unknown"
                    ),
                })

            return {
                "success": True,
                "user_id": user_id,
                "count": len(result),
                "bookings": result,
            }

        except Exception as exc:
            logger.exception("Failed to get user bookings")

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # CONFIRM BOOKING
    # ========================================================

    @staticmethod
    def confirm_booking(
        db: Session,
        booking_id: int,
        user_id: int,
    ) -> dict:
        """
        Confirm booking only when payment_status == SUCCESS.
        """

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .with_for_update()
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} not found."
                    ),
                }

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized to confirm this booking."
                    ),
                }

            if booking.status == BOOKING_CANCELLED:
                return {
                    "success": False,
                    "error": "BOOKING_CANCELLED",
                    "message": (
                        "Cancelled booking cannot be confirmed."
                    ),
                }

            if booking.payment_status != PAYMENT_SUCCESS:
                return {
                    "success": False,
                    "error": "PAYMENT_REQUIRED",
                    "message": (
                        "Booking cannot be confirmed until "
                        "payment is successfully completed."
                    ),
                    "booking_id": booking.id,
                    "booking_status": booking.status,
                    "payment_status": booking.payment_status,
                }

            booking.status = BOOKING_CONFIRMED

            db.commit()
            db.refresh(booking)

            return {
                "success": True,
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,
                "paid_at": (
                    booking.paid_at.isoformat()
                    if booking.paid_at
                    else None
                ),
                "ticket_download_allowed": True,
            }

        except Exception as exc:
            db.rollback()

            logger.exception("Failed to confirm booking")

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # MARK PAYMENT SUCCESS
    # ========================================================

    @staticmethod
    def mark_payment_success(
        db: Session,
        booking_id: int,
        payment_id: str,
    ) -> dict:
        """
        Trusted payment transition.

        PENDING_PAYMENT
              ↓
        PAYMENT SUCCESS
              ↓
        CONFIRMED
        """

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .with_for_update()
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} not found."
                    ),
                }

            if booking.status == BOOKING_CANCELLED:
                return {
                    "success": False,
                    "error": "BOOKING_CANCELLED",
                    "message": (
                        "Payment cannot be completed for "
                        "a cancelled booking."
                    ),
                }

            # ------------------------------------------------
            # Idempotency
            # ------------------------------------------------

            if booking.payment_status == PAYMENT_SUCCESS:
                return {
                    "success": True,
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "status": booking.status,
                    "payment_status": booking.payment_status,
                    "payment_id": booking.payment_id,
                    "paid_at": (
                        booking.paid_at.isoformat()
                        if booking.paid_at
                        else None
                    ),
                    "message": (
                        "Payment was already successfully processed."
                    ),
                    "ticket_download_allowed": (
                        booking.status == BOOKING_CONFIRMED
                    ),
                }

            # ------------------------------------------------
            # Update booking payment state
            # ------------------------------------------------

            booking.payment_status = PAYMENT_SUCCESS
            booking.payment_id = payment_id
            booking.paid_at = get_current_datetime_kolkata()

            # ------------------------------------------------
            # Confirm booking
            # ------------------------------------------------

            booking.status = BOOKING_CONFIRMED

            db.commit()
            db.refresh(booking)

            logger.info(
                "Payment successful | Booking=%s | Payment=%s",
                booking.id,
                payment_id,
            )

            return {
                "success": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "status": booking.status,
                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,

                "paid_at": (
                    booking.paid_at.isoformat()
                    if booking.paid_at
                    else None
                ),

                "total_price": float(
                    booking.total_price
                ),

                "ticket_download_allowed": True,

                "message": (
                    "Payment successful. "
                    "Booking confirmed. "
                    "Ticket can now be downloaded."
                ),
            }

        except Exception as exc:
            db.rollback()

            logger.exception(
                "Failed to mark payment success"
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # MARK PAYMENT FAILED
    # ========================================================

    @staticmethod
    def mark_payment_failed(
        db: Session,
        booking_id: int,
        payment_id: str | None = None,
    ) -> dict:
        """
        Mark payment as failed.

        Booking remains unconfirmed.

        Seats remain reserved until the booking is cancelled
        or an expiration/cleanup process releases them.
        """

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .with_for_update()
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} not found."
                    ),
                }

            if booking.status == BOOKING_CONFIRMED:
                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CONFIRMED",
                    "message": (
                        "A confirmed booking cannot be marked "
                        "as payment failed."
                    ),
                }

            if booking.status == BOOKING_CANCELLED:
                return {
                    "success": False,
                    "error": "BOOKING_CANCELLED",
                    "message": "Booking is already cancelled.",
                }

            booking.status = BOOKING_PENDING_PAYMENT
            booking.payment_status = PAYMENT_FAILED

            if payment_id:
                booking.payment_id = payment_id

            db.commit()
            db.refresh(booking)

            return {
                "success": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "status": booking.status,
                "payment_status": booking.payment_status,

                "payment_id": booking.payment_id,

                "paid_at": None,

                "ticket_download_allowed": False,

                "message": (
                    "Payment failed. "
                    "Booking is not confirmed."
                ),
            }

        except Exception as exc:
            db.rollback()

            logger.exception(
                "Failed to mark payment failed"
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # CAN DOWNLOAD TICKET
    # ========================================================

    @staticmethod
    def can_download_ticket(
        db: Session,
        booking_id: int,
        user_id: int,
    ) -> dict:
        """
        Ticket is allowed ONLY when:

            booking belongs to user
            AND
            booking.status == CONFIRMED
            AND
            booking.payment_status == SUCCESS
        """

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "allowed": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": "Booking not found.",
                }

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "allowed": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized to access this ticket."
                    ),
                }

            if booking.payment_status != PAYMENT_SUCCESS:
                return {
                    "success": False,
                    "allowed": False,
                    "error": "PAYMENT_REQUIRED",
                    "message": (
                        "Ticket cannot be downloaded until "
                        "payment is successfully completed."
                    ),
                }

            if booking.status != BOOKING_CONFIRMED:
                return {
                    "success": False,
                    "allowed": False,
                    "error": "BOOKING_NOT_CONFIRMED",
                    "message": (
                        "Ticket cannot be downloaded because "
                        "the booking is not confirmed."
                    ),
                }

            return {
                "success": True,
                "allowed": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "status": booking.status,
                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,
            }

        except Exception as exc:
            logger.exception(
                "Failed to validate ticket access"
            )

            return {
                "success": False,
                "allowed": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # CANCEL BOOKING
    # ========================================================

    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        user_id: int,
    ) -> dict:

        BookingService._seat_lock.acquire()

        try:
            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .with_for_update()
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking with ID {booking_id} not found."
                    ),
                }

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_OWNED",
                    "message": (
                        "You are not authorized to cancel this booking."
                    ),
                }

            if booking.status == BOOKING_CANCELLED:
                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CANCELLED",
                    "message": "Booking is already cancelled.",
                }

            # ------------------------------------------------
            # Lock flight
            # ------------------------------------------------

            flight = (
                db.query(Flight)
                .filter(
                    Flight.flight_id == booking.flight_id
                )
                .with_for_update()
                .first()
            )

            # ------------------------------------------------
            # Cancel booking
            # ------------------------------------------------

            booking.status = BOOKING_CANCELLED

            # ------------------------------------------------
            # Release seats
            # ------------------------------------------------

            if flight:
                flight.available_seats += booking.number_of_seats

            db.commit()
            db.refresh(booking)

            logger.info(
                "Booking cancelled | Booking=%s",
                booking.id,
            )

            return {
                "success": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "user_id": booking.user_id,
                "flight_id": booking.flight_id,

                "number_of_seats": booking.number_of_seats,

                "base_fare": float(booking.base_fare),
                "tax_amount": float(booking.tax_amount),
                "service_fee": float(booking.service_fee),
                "total_price": float(booking.total_price),

                "status": booking.status,

                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,

                "created_at": (
                    booking.created_at.isoformat()
                    if booking.created_at
                    else None
                ),

                "available_seats": (
                    flight.available_seats
                    if flight
                    else None
                ),
            }

        except Exception as exc:
            db.rollback()

            logger.exception(
                "Failed to cancel booking"
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": (
                    f"Failed to cancel booking: {str(exc)}"
                ),
            }

        finally:
            BookingService._seat_lock.release()

    # ========================================================
    # CHANGE BOOKING
    # ========================================================

    @staticmethod
    def change_booking(
        db: Session,
        booking_id: int,
        user_id: int,
        new_flight_id: str,
        new_number_of_seats: int,
    ) -> dict:

        if new_number_of_seats <= 0:
            return {
                "success": False,
                "error": "INVALID_SEAT_COUNT",
                "message": (
                    "Number of seats must be greater than zero."
                ),
            }

        BookingService._seat_lock.acquire()

        try:
            # ------------------------------------------------
            # 1. Get booking
            # ------------------------------------------------

            booking = (
                db.query(Booking)
                .filter(Booking.id == booking_id)
                .with_for_update()
                .first()
            )

            if not booking:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} not found."
                    ),
                }

            # ------------------------------------------------
            # 2. Authorization
            # ------------------------------------------------

            if booking.user_id != user_id:
                return {
                    "success": False,
                    "error": "BOOKING_NOT_OWNED",
                    "message": (
                        "You are not authorized to modify this booking."
                    ),
                }

            # ------------------------------------------------
            # 3. Cancelled booking
            # ------------------------------------------------

            if booking.status == BOOKING_CANCELLED:
                return {
                    "success": False,
                    "error": "INVALID_BOOKING_STATUS",
                    "message": (
                        "Cannot change a cancelled booking."
                    ),
                }

            # ------------------------------------------------
            # 4. Lock old flight
            # ------------------------------------------------

            old_flight = (
                db.query(Flight)
                .filter(
                    Flight.flight_id == booking.flight_id
                )
                .with_for_update()
                .first()
            )

            # ------------------------------------------------
            # 5. Lock new flight
            # ------------------------------------------------

            new_flight = (
                db.query(Flight)
                .filter(
                    Flight.flight_id == new_flight_id
                )
                .with_for_update()
                .first()
            )

            if not new_flight:
                return {
                    "success": False,
                    "error": "FLIGHT_NOT_FOUND",
                    "message": (
                        f"Target flight {new_flight_id} not found."
                    ),
                }

            # ------------------------------------------------
            # 6. Validate new flight
            # ------------------------------------------------

            current_dt = get_current_datetime_kolkata()

            new_flight_dt = parse_flight_departure_datetime(
                new_flight.date,
                new_flight.departure_time,
            )

            if (
                not new_flight_dt
                or new_flight_dt <= current_dt
            ):
                return {
                    "success": False,
                    "error": "FLIGHT_DEPARTED",
                    "message": (
                        f"Target flight {new_flight_id} "
                        f"has already departed."
                    ),
                }

            # ------------------------------------------------
            # 7. Check seats
            # ------------------------------------------------

            available_for_booking = new_flight.available_seats

            if new_flight_id == booking.flight_id:
                available_for_booking += booking.number_of_seats

            if available_for_booking < new_number_of_seats:
                return {
                    "success": False,
                    "error": "NOT_ENOUGH_SEATS",
                    "message": (
                        f"Only {available_for_booking} seat(s) "
                        f"available on flight {new_flight_id}."
                    ),
                }

            # ------------------------------------------------
            # 8. Release old seats
            # ------------------------------------------------

            if old_flight:
                old_flight.available_seats += booking.number_of_seats

            # ------------------------------------------------
            # 9. Reserve new seats
            # ------------------------------------------------

            new_flight.available_seats -= new_number_of_seats

            # ------------------------------------------------
            # 10. Calculate new fare
            # ------------------------------------------------

            fare = calculate_fare(
                base_price=float(new_flight.price),
                number_of_seats=new_number_of_seats,
            )

            # ------------------------------------------------
            # 11. Update booking
            # ------------------------------------------------

            booking.flight_id = new_flight_id
            booking.number_of_seats = new_number_of_seats

            booking.base_fare = fare["base_fare"]
            booking.tax_amount = fare["tax_amount"]
            booking.service_fee = fare["service_fee"]
            booking.total_price = fare["total_price"]

            # ------------------------------------------------
            # IMPORTANT:
            # Existing payment cannot be reused because
            # fare may have changed.
            # ------------------------------------------------

            booking.status = BOOKING_PENDING_PAYMENT
            booking.payment_status = PAYMENT_PENDING
            booking.payment_id = None
            booking.paid_at = None

            # ------------------------------------------------
            # 12. Commit
            # ------------------------------------------------

            db.commit()
            db.refresh(booking)

            logger.info(
                "Booking changed | Booking=%s | NewFlight=%s | "
                "Seats=%s | Payment reset",
                booking.id,
                new_flight_id,
                new_number_of_seats,
            )

            return {
                "success": True,

                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,

                "user_id": booking.user_id,
                "flight_id": booking.flight_id,

                "number_of_seats": booking.number_of_seats,

                "base_fare": float(booking.base_fare),
                "tax_amount": float(booking.tax_amount),
                "service_fee": float(booking.service_fee),
                "total_price": float(booking.total_price),

                "status": booking.status,

                "payment_status": booking.payment_status,
                "payment_id": booking.payment_id,
                "paid_at": None,

                "ticket_download_allowed": False,

                "created_at": (
                    booking.created_at.isoformat()
                    if booking.created_at
                    else None
                ),

                "message": (
                    "Booking changed successfully. "
                    "Payment is required again before "
                    "the booking can be confirmed."
                ),
            }

        except Exception as exc:
            db.rollback()

            logger.exception(
                "Failed to change booking"
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": (
                    f"Failed to change booking: {str(exc)}"
                ),
            }

        finally:
            BookingService._seat_lock.release()