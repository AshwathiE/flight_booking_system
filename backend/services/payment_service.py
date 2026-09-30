# backend/services/payment_service.py

import logging
import random
import string
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from backend.models.payment import Payment
from backend.models.booking import Booking
from backend.models.flight import Flight
from backend.models.user import User


logger = logging.getLogger("payment_service")

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# PAYMENT STATUS
# ============================================================

PAYMENT_PENDING = "PENDING"
PAYMENT_PROCESSING = "PROCESSING"
PAYMENT_SUCCESS = "SUCCESS"
PAYMENT_FAILED = "FAILED"
PAYMENT_REFUNDED = "REFUNDED"


# ============================================================
# BOOKING STATUS
# ============================================================

BOOKING_PENDING_PAYMENT = "PENDING_PAYMENT"
BOOKING_CONFIRMED = "CONFIRMED"
BOOKING_CANCELLED = "CANCELLED"


# ============================================================
# TICKET STATUS
# ============================================================

TICKET_NOT_AVAILABLE = "NOT_AVAILABLE"
TICKET_AVAILABLE = "AVAILABLE"


class PaymentService:
    """
    Business logic for payment lifecycle management.

    Payment lifecycle:

        PENDING
            |
            +------> SUCCESS
            |
            +------> FAILED
            |
            +------> REFUNDED

    Booking lifecycle:

        PENDING_PAYMENT
            |
            +------> CONFIRMED
            |
            +------> CANCELLED

    Booking payment summary:

        PENDING
        SUCCESS
        FAILED
        REFUNDED

    Ticket:

        NOT_AVAILABLE
        AVAILABLE
    """

    # ========================================================
    # ID GENERATORS
    # ========================================================

    @staticmethod
    def _random_suffix(length: int = 6) -> str:
        """
        Generate random uppercase alphanumeric suffix.
        """

        return "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=length,
            )
        )

    # ========================================================
    # PAYMENT ID
    # ========================================================

    @staticmethod
    def generate_payment_id(db: Session) -> str:
        """
        Generate a unique payment ID.

        Example:

            PAY20260825153045ABC123
        """

        for _ in range(100):

            timestamp = datetime.now(IST).strftime(
                "%Y%m%d%H%M%S"
            )

            payment_id = (
                f"PAY"
                f"{timestamp}"
                f"{PaymentService._random_suffix()}"
            )

            existing = (
                db.query(Payment)
                .filter(
                    Payment.payment_id == payment_id
                )
                .first()
            )

            if not existing:
                return payment_id

        raise RuntimeError(
            "Unable to generate unique payment ID."
        )

    # ========================================================
    # TRANSACTION ID
    # ========================================================

    @staticmethod
    def generate_transaction_id(db: Session) -> str:
        """
        Generate a unique gateway transaction ID.

        Example:

            TXN20260825153045ABC123
        """

        for _ in range(100):

            timestamp = datetime.now(IST).strftime(
                "%Y%m%d%H%M%S"
            )

            transaction_id = (
                f"TXN"
                f"{timestamp}"
                f"{PaymentService._random_suffix()}"
            )

            existing = (
                db.query(Payment)
                .filter(
                    Payment.transaction_id
                    == transaction_id
                )
                .first()
            )

            if not existing:
                return transaction_id

        raise RuntimeError(
            "Unable to generate unique transaction ID."
        )

    # ========================================================
    # REFUND ID
    # ========================================================

    @staticmethod
    def generate_refund_id(db: Session) -> str:
        """
        Generate a unique refund ID.

        Example:

            REF20260825153045ABC123
        """

        for _ in range(100):

            timestamp = datetime.now(IST).strftime(
                "%Y%m%d%H%M%S"
            )

            refund_id = (
                f"REF"
                f"{timestamp}"
                f"{PaymentService._random_suffix()}"
            )

            existing = (
                db.query(Payment)
                .filter(
                    Payment.refund_id == refund_id
                )
                .first()
            )

            if not existing:
                return refund_id

        raise RuntimeError(
            "Unable to generate unique refund ID."
        )

    # ========================================================
    # CREATE PAYMENT
    # ========================================================

    @staticmethod
    def create_payment(
        db: Session,
        booking_id: int,
        user_id: int,
        payment_method: str = "MOCK",
        amount: float | None = None,
        currency: str = "INR",
    ) -> dict:
        """
        Create a payment for a pending booking.

        IMPORTANT:

        The payment amount is ALWAYS taken from:

            Booking.total_price

        The client cannot provide or modify the amount.

        Existing pending payment:
            return existing payment.

        Existing successful payment:
            reject duplicate payment.

        Failed payment:
            create a new payment attempt.
        """

        try:

            # ------------------------------------------------
            # 1. Validate user
            # ------------------------------------------------

            user = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if not user:

                return {
                    "success": False,
                    "error": "USER_NOT_FOUND",
                    "message": (
                        f"User with ID {user_id} "
                        f"does not exist."
                    ),
                }

            # ------------------------------------------------
            # 2. Get booking
            # ------------------------------------------------

            booking = (
                db.query(Booking)
                .filter(
                    Booking.id == booking_id
                )
                .first()
            )

            if not booking:

                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} "
                        f"not found."
                    ),
                }

            # ------------------------------------------------
            # 3. Authorization
            # ------------------------------------------------

            if booking.user_id != user_id:

                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized to "
                        "pay for this booking."
                    ),
                }

            # ------------------------------------------------
            # 4. Cancelled booking
            # ------------------------------------------------

            if booking.status == BOOKING_CANCELLED:

                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CANCELLED",
                    "message": (
                        "Payment cannot be created "
                        "for a cancelled booking."
                    ),
                }

            # ------------------------------------------------
            # 5. Already confirmed
            # ------------------------------------------------

            if booking.status == BOOKING_CONFIRMED:

                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CONFIRMED",
                    "message": (
                        "This booking has already "
                        "been confirmed."
                    ),
                }

            if amount is not None:
                try:
                    requested_amount = float(amount)
                except (TypeError, ValueError):
                    requested_amount = None

                if requested_amount is None or requested_amount != float(booking.total_price):
                    return {
                        "success": False,
                        "error": "INVALID_AMOUNT",
                        "message": "Payment amount must match the booking total.",
                    }

            # ------------------------------------------------
            # 6. Check successful payment
            # ------------------------------------------------

            successful_payment = (
                db.query(Payment)
                .filter(
                    Payment.booking_id == booking_id,
                    Payment.status == PAYMENT_SUCCESS,
                )
                .first()
            )

            if successful_payment:

                return {
                    "success": False,
                    "error": "PAYMENT_ALREADY_COMPLETED",
                    "message": (
                        "Payment for this booking "
                        "has already been completed."
                    ),
                    "payment_id": (
                        successful_payment.payment_id
                    ),
                }

                logger.info(
                    "MOCK GATEWAY: processing payment_id=%r user_id=%r success=%r",
                    payment_id,
                    user_id,
                    success,
                )

            # ------------------------------------------------
            # 7. Check existing pending payment
            # ------------------------------------------------

            pending_payment = (
                db.query(Payment)
                .filter(
                    Payment.booking_id == booking_id,
                    Payment.status == PAYMENT_PENDING,
                )
                .order_by(
                    Payment.created_at.desc()
                )
                .first()
            )

            if pending_payment:

                # Ensure booking summary is synchronized.
                booking.payment_status = PAYMENT_PENDING
                booking.status = BOOKING_PENDING_PAYMENT

                db.commit()

                return PaymentService._payment_response(
                    pending_payment,
                    booking,
                    message=(
                        "A pending payment already "
                        "exists."
                    ),
                )

            # ------------------------------------------------
            # 8. Create new payment
            # ------------------------------------------------

            if booking.total_price is None:
                return {
                    "success": False,
                    "error": "INVALID_BOOKING_AMOUNT",
                    "message": (
                        f"Booking {booking_id} does not have "
                        "a valid total price."
                    ),
                }

            amount = float(booking.total_price)

            if amount <= 0:
                return {
                    "success": False,
                    "error": "INVALID_BOOKING_AMOUNT",
                        "message": (
                        f"Booking {booking_id} has an invalid "
                        f"total price: {amount}."
                        ),
                    }

            payment = Payment(
               payment_id=PaymentService.generate_payment_id(db),
               booking_id=booking.id,
               user_id=user_id,
               amount=float(booking.total_price),
               currency=currency,
               payment_method=payment_method,
               status=PAYMENT_PENDING,
            )

            db.add(payment) 
            
            # ------------------------------------------------
            # 9. Synchronize booking state
            # ------------------------------------------------

            booking.status = BOOKING_PENDING_PAYMENT

            booking.payment_status = PAYMENT_PENDING

            booking.payment_id = None

            booking.paid_at = None

            booking.ticket_status = (
                TICKET_NOT_AVAILABLE
            )

            # ------------------------------------------------
            # 10. Commit
            # ------------------------------------------------

            db.commit()

            db.refresh(payment)
            db.refresh(booking)

            logger.info(
                "Payment created | "
                "payment_id=%s | "
                "booking_id=%s | "
                "amount=%s",
                payment.payment_id,
                booking.id,
                payment.amount,
            )

            # ------------------------------------------------
            # 11. Response
            # ------------------------------------------------

            return PaymentService._payment_response(
                payment,
                booking,
                message=(
                    "Payment initiated successfully."
                ),
            )

        except Exception as exc:

            db.rollback()

            logger.exception(
                "Failed to create payment."
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": (
                    f"Failed to create payment: {str(exc)}"
                ),
            }

    # ========================================================
    # PROCESS PAYMENT
    # ========================================================

    @staticmethod
    def process_payment(
        db: Session,
        payment_id: str,
        user_id: int | None = None,
        success: bool = True,
        payment_method: str | None = None,
    ) -> dict:
        """
        Process a payment.

        This currently represents a MOCK payment gateway.

        Success:

            Payment -> SUCCESS
            Booking -> CONFIRMED
            Booking.payment_status -> SUCCESS
            Ticket -> AVAILABLE

        Failure:

            Payment -> FAILED
            Booking -> PENDING_PAYMENT
            Booking.payment_status -> FAILED
            Ticket -> NOT_AVAILABLE
        """

        try:

            # ------------------------------------------------
            # 1. Find payment
            # ------------------------------------------------

            payment = (
                db.query(Payment)
                .filter(
                    Payment.payment_id == payment_id
                )
                .first()
            )

            if not payment:

                return {
                    "success": False,
                    "error": "PAYMENT_NOT_FOUND",
                    "message": (
                        f"Payment {payment_id} "
                        f"not found."
                    ),
                }

            if user_id is None:
                user_id = payment.user_id

            if payment_method:
                method = payment_method.upper()
                if "FAIL" in method or "TIMEOUT" in method:
                    success = False

            # ------------------------------------------------
            # 2. Authorization
            # ------------------------------------------------

            if payment.user_id != user_id:

                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized to "
                        "process this payment."
                    ),
                }

            # ------------------------------------------------
            # 3. Get booking
            # ------------------------------------------------

            booking = (
                db.query(Booking)
                .filter(
                    Booking.id == payment.booking_id
                )
                .first()
            )

            if not booking:

                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        "Booking associated with "
                        "payment was not found."
                    ),
                }

            # ------------------------------------------------
            # 4. Already successful
            # ------------------------------------------------

            if payment.status == PAYMENT_SUCCESS:

                return PaymentService._payment_response(
                    payment,
                    booking,
                    message=(
                        "Payment has already "
                        "been completed."
                    ),
                    ticket_download_allowed=(
                        booking.status
                        == BOOKING_CONFIRMED
                        and booking.payment_status
                        == PAYMENT_SUCCESS
                    ),
                )

            # ------------------------------------------------
            # 5. Already refunded
            # ------------------------------------------------

            if payment.status == PAYMENT_REFUNDED:

                return {
                    "success": False,
                    "error": "PAYMENT_REFUNDED",
                    "message": (
                        "This payment has already "
                        "been refunded."
                    ),
                }

            # ------------------------------------------------
            # 6. Already failed
            # ------------------------------------------------

            if payment.status == PAYMENT_FAILED:

                return {
                    "success": False,
                    "error": "PAYMENT_ALREADY_FAILED",
                    "message": (
                        "This payment attempt has "
                        "already failed. Create a "
                        "new payment to retry."
                    ),
                }

            # ------------------------------------------------
            # 7. Invalid status
            # ------------------------------------------------

            if payment.status not in (
                PAYMENT_PENDING,
                PAYMENT_PROCESSING,
            ):

                return {
                    "success": False,
                    "error": "INVALID_PAYMENT_STATUS",
                    "message": (
                        f"Payment cannot be processed "
                        f"from status "
                        f"{payment.status}."
                    ),
                }

            # ------------------------------------------------
            # 8. Cancelled booking
            # ------------------------------------------------

            if booking.status == BOOKING_CANCELLED:

                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CANCELLED",
                    "message": (
                        "Payment cannot be processed "
                        "for a cancelled booking."
                    ),
                }

            # =================================================
            # PAYMENT FAILURE
            # =================================================

            if not success:

                payment.status = PAYMENT_FAILED

                payment.failure_reason = (
                    "Mock payment timeout"
                    if payment_method and "TIMEOUT" in payment_method.upper()
                    else "Mock payment failure"
                    if payment_method and "FAIL" in payment_method.upper()
                    else "Payment was declined by payment gateway."
                )

                # IMPORTANT:
                # Keep booking itself in PENDING_PAYMENT.
                booking.status = BOOKING_PENDING_PAYMENT

                booking.payment_status = PAYMENT_FAILED

                booking.ticket_status = (
                    TICKET_NOT_AVAILABLE
                )

                db.commit()

                db.refresh(payment)
                db.refresh(booking)

                logger.warning(
                    "Payment failed | "
                    "payment_id=%s | "
                    "booking_id=%s",
                    payment.payment_id,
                    booking.id,
                )

                return {
                    "success": False,
                    "error": "PAYMENT_FAILED",
                    "message": (
                        "Payment failed. "
                        "Booking has not been confirmed."
                    ),
                    "payment_id": (
                        payment.payment_id
                    ),
                    "status": payment.status,
                    "failure_reason": payment.failure_reason,
                    "booking_id": booking.id,
                    "payment_status": (
                        payment.status
                    ),
                    "booking_status": (
                        booking.status
                    ),
                    "ticket_status": (
                        booking.ticket_status
                    ),
                    "ticket_download_allowed": False,
                }

            # =================================================
            # PAYMENT SUCCESS
            # =================================================

            transaction_id = (
                PaymentService.generate_transaction_id(db)
            )

            payment.status = PAYMENT_SUCCESS

            payment.transaction_id = transaction_id

            payment.failure_reason = None

            # ------------------------------------------------
            # Update booking payment information
            # ------------------------------------------------

            booking.payment_status = PAYMENT_SUCCESS

            booking.payment_id = payment.payment_id

            booking.paid_at = (
                datetime.now(IST)
            )

            # ------------------------------------------------
            # Confirm booking
            # ------------------------------------------------

            booking.status = BOOKING_CONFIRMED

            # ------------------------------------------------
            # Make ticket available
            # ------------------------------------------------

            booking.ticket_status = (
                TICKET_AVAILABLE
            )

            # ------------------------------------------------
            # Commit
            # ------------------------------------------------

            db.commit()

            db.refresh(payment)
            db.refresh(booking)

            logger.info(
                "Payment successful | "
                "payment_id=%s | "
                "transaction_id=%s | "
                "booking_id=%s",
                payment.payment_id,
                transaction_id,
                booking.id,
            )

            return PaymentService._payment_response(
                payment,
                booking,
                message=(
                    "Payment completed successfully. "
                    "Booking confirmed."
                ),
                ticket_download_allowed=True,
            )

        except Exception as exc:

            db.rollback()

            logger.exception(
                "Failed to process payment."
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": (
                    f"Failed to process payment: {str(exc)}"
                ),
            }

    # ========================================================
    # GET PAYMENT
    # ========================================================

    @staticmethod
    def get_payment(
        db: Session,
        payment_id: str,
        user_id: int | None = None,
        requesting_user_id: int | None = None,
    ) -> dict:

        try:

            user_id = user_id if user_id is not None else requesting_user_id

            payment = (
                db.query(Payment)
                .filter(
                    Payment.payment_id == payment_id
                )
                .first()
            )

            if not payment:

                return {
                    "success": False,
                    "error": "PAYMENT_NOT_FOUND",
                    "message": (
                        f"Payment {payment_id} "
                        f"not found."
                    ),
                }

            if payment.user_id != user_id:

                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized "
                        "to view this payment."
                    ),
                }

            booking = payment.booking

            return PaymentService._payment_response(
                payment,
                booking,
                message=None,
                ticket_download_allowed=(
                    payment.status
                    == PAYMENT_SUCCESS
                    and booking is not None
                    and booking.status
                    == BOOKING_CONFIRMED
                    and booking.payment_status
                    == PAYMENT_SUCCESS
                    and booking.ticket_status
                    == TICKET_AVAILABLE
                ),
                include_failure_reason=True,
            )

        except Exception as exc:

            logger.exception(
                "Failed to retrieve payment."
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # GET PAYMENT BY BOOKING
    # ========================================================

    @staticmethod
    def get_booking_payment(
        db: Session,
        booking_id: int,
        user_id: int,
    ) -> dict:

        try:

            booking = (
                db.query(Booking)
                .filter(
                    Booking.id == booking_id
                )
                .first()
            )

            if not booking:

                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        f"Booking {booking_id} "
                        f"not found."
                    ),
                }

            if booking.user_id != user_id:

                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized "
                        "to view this booking."
                    ),
                }

            payment = (
                db.query(Payment)
                .filter(
                    Payment.booking_id == booking_id
                )
                .order_by(
                    Payment.created_at.desc()
                )
                .first()
            )

            if not payment:

                return {
                    "success": True,
                    "payment_exists": False,
                    "booking_id": booking_id,
                    "booking_status": booking.status,
                    "payment_status": (
                        booking.payment_status
                    ),
                    "ticket_status": (
                        booking.ticket_status
                    ),
                    "ticket_download_allowed": False,
                }

            result = PaymentService._payment_response(
                payment,
                booking,
                message=None,
                ticket_download_allowed=(
                    payment.status
                    == PAYMENT_SUCCESS
                    and booking.status
                    == BOOKING_CONFIRMED
                    and booking.payment_status
                    == PAYMENT_SUCCESS
                    and booking.ticket_status
                    == TICKET_AVAILABLE
                ),
                include_failure_reason=True,
            )

            result["payment_exists"] = True

            return result

        except Exception as exc:

            logger.exception(
                "Failed to retrieve booking payment."
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    @staticmethod
    def get_payment_by_booking(
        db: Session,
        booking_id: int,
        user_id: int | None = None,
        requesting_user_id: int | None = None,
    ) -> dict:
        """Backward-compatible alias for retrieving a booking payment."""
        user_id = user_id if user_id is not None else requesting_user_id
        return PaymentService.get_booking_payment(db, booking_id, user_id)

    @staticmethod
    def verify_payment(
        db: Session,
        payment_id: str,
        user_id: int | None = None,
    ) -> dict:
        """Backward-compatible alias for retrieving payment status."""
        if user_id is None:
            payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
            if not payment:
                return {
                    "success": False,
                    "error": "PAYMENT_NOT_FOUND",
                    "message": f"Payment {payment_id} not found.",
                }
            user_id = payment.user_id
        return PaymentService.get_payment(db, payment_id, user_id)

    # ========================================================
    # REFUND PAYMENT
    # ========================================================

    @staticmethod
    def refund_payment(
        db: Session,
        payment_id: str,
        user_id: int | None = None,
        reason: str | None = None,
        requesting_user_id: int | None = None,
    ) -> dict:
        """
        Refund a successful payment.

        IMPORTANT:

        This method changes payment and booking state.

        Seat restoration should be handled by the
        BookingService cancellation flow.

        Payment:

            SUCCESS -> REFUNDED

        Booking:

            CONFIRMED -> CANCELLED

        Booking payment:

            SUCCESS -> REFUNDED

        Ticket:

            AVAILABLE -> NOT_AVAILABLE
        """

        try:

            # ------------------------------------------------
            # 1. Find payment
            # ------------------------------------------------

            payment = (
                db.query(Payment)
                .filter(
                    Payment.payment_id == payment_id
                )
                .first()
            )

            if not payment:

                return {
                    "success": False,
                    "error": "PAYMENT_NOT_FOUND",
                    "message": (
                        f"Payment {payment_id} "
                        f"not found."
                    ),
                }

            if user_id is None:
                user_id = requesting_user_id or payment.user_id

            # ------------------------------------------------
            # 2. Authorization
            # ------------------------------------------------

            if payment.user_id != user_id:

                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized "
                        "to refund this payment."
                    ),
                }

            # ------------------------------------------------
            # 3. Already refunded
            # ------------------------------------------------

            if payment.status == PAYMENT_REFUNDED:

                return {
                    "success": False,
                    "error": "PAYMENT_ALREADY_REFUNDED",
                    "message": (
                        "This payment has already "
                        "been refunded."
                    ),
                    "payment_id": (
                        payment.payment_id
                    ),
                    "refund_id": (
                        payment.refund_id
                    ),
                }

            # ------------------------------------------------
            # 4. Must be successful
            # ------------------------------------------------

            if payment.status != PAYMENT_SUCCESS:

                return {
                    "success": False,
                    "error": "INVALID_PAYMENT_STATUS",
                    "message": (
                        "Only successful payments "
                        "can be refunded."
                    ),
                }

            # ------------------------------------------------
            # 5. Get booking
            # ------------------------------------------------

            booking = payment.booking

            if not booking:

                return {
                    "success": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        "Booking associated with "
                        "payment was not found."
                    ),
                }

            # ------------------------------------------------
            # 6. Already cancelled
            # ------------------------------------------------

            if booking.status == BOOKING_CANCELLED:

                return {
                    "success": False,
                    "error": "BOOKING_ALREADY_CANCELLED",
                    "message": (
                        "The booking is already "
                        "cancelled."
                    ),
                }

            # ------------------------------------------------
            # 7. Generate refund ID
            # ------------------------------------------------

            refund_id = (
                PaymentService.generate_refund_id(db)
            )

            # ------------------------------------------------
            # 8. Update payment
            # ------------------------------------------------

            payment.status = PAYMENT_REFUNDED

            payment.refund_id = refund_id

            # ------------------------------------------------
            # 9. Update booking
            # ------------------------------------------------

            booking.status = BOOKING_CANCELLED

            booking.payment_status = (
                PAYMENT_REFUNDED
            )

            booking.ticket_status = (
                TICKET_NOT_AVAILABLE
            )

            flight = (
                db.query(Flight)
                .filter(Flight.flight_id == booking.flight_id)
                .with_for_update()
                .first()
            )
            if flight:
                flight.available_seats += booking.number_of_seats

            # ------------------------------------------------
            # Do NOT clear payment_id
            # ------------------------------------------------
            #
            # Keeping payment_id provides an audit trail.
            #

            # ------------------------------------------------
            # 10. Commit
            # ------------------------------------------------

            db.commit()

            db.refresh(payment)
            db.refresh(booking)

            logger.info(
                "Payment refunded | "
                "payment_id=%s | "
                "refund_id=%s | "
                "booking_id=%s",
                payment.payment_id,
                refund_id,
                booking.id,
            )

            return {
                "success": True,
                "status": payment.status,
                "message": (
                    "Payment refunded successfully."
                ),
                "payment_id": (
                    payment.payment_id
                ),
                "refund_id": (
                    payment.refund_id
                ),
                "booking_id": (
                    payment.booking_id
                ),
                "payment_status": (
                    payment.status
                ),
                "booking_status": (
                    booking.status
                ),
                "ticket_status": (
                    booking.ticket_status
                ),
                "ticket_download_allowed": False,
            }

        except Exception as exc:

            db.rollback()

            logger.exception(
                "Failed to refund payment."
            )

            return {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": (
                    f"Failed to refund payment: {str(exc)}"
                ),
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
        Ticket can be downloaded ONLY when:

            1. Booking belongs to user
            2. Booking is CONFIRMED
            3. Payment is SUCCESS
            4. Ticket is AVAILABLE
        """

        try:

            booking = (
                db.query(Booking)
                .filter(
                    Booking.id == booking_id
                )
                .first()
            )

            if not booking:

                return {
                    "success": False,
                    "allowed": False,
                    "error": "BOOKING_NOT_FOUND",
                    "message": (
                        "Booking not found."
                    ),
                }

            # ------------------------------------------------
            # Authorization
            # ------------------------------------------------

            if booking.user_id != user_id:

                return {
                    "success": False,
                    "allowed": False,
                    "error": "UNAUTHORIZED",
                    "message": (
                        "You are not authorized "
                        "to access this ticket."
                    ),
                }

            # ------------------------------------------------
            # Booking status
            # ------------------------------------------------

            if booking.status != BOOKING_CONFIRMED:

                return {
                    "success": False,
                    "allowed": False,
                    "error": "BOOKING_NOT_CONFIRMED",
                    "message": (
                        "Ticket cannot be downloaded "
                        "because the booking is not confirmed."
                    ),
                }

            # ------------------------------------------------
            # Payment status
            # ------------------------------------------------

            if (
                booking.payment_status
                != PAYMENT_SUCCESS
            ):

                return {
                    "success": False,
                    "allowed": False,
                    "error": "PAYMENT_REQUIRED",
                    "message": (
                        "Ticket cannot be downloaded "
                        "until payment is successfully completed."
                    ),
                }

            # ------------------------------------------------
            # Ticket status
            # ------------------------------------------------

            if (
                booking.ticket_status
                != TICKET_AVAILABLE
            ):

                return {
                    "success": False,
                    "allowed": False,
                    "error": "TICKET_NOT_AVAILABLE",
                    "message": (
                        "Ticket is not available yet."
                    ),
                }

            # ------------------------------------------------
            # Allowed
            # ------------------------------------------------

            return {
                "success": True,
                "allowed": True,
                "booking_id": booking.id,
                "booking_reference": (
                    booking.booking_reference
                ),
                "status": booking.status,
                "payment_status": (
                    booking.payment_status
                ),
                "payment_id": (
                    booking.payment_id
                ),
                "ticket_status": (
                    booking.ticket_status
                ),
            }

        except Exception as exc:

            logger.exception(
                "Failed to validate ticket access."
            )

            return {
                "success": False,
                "allowed": False,
                "error": "DATABASE_ERROR",
                "message": str(exc),
            }

    # ========================================================
    # COMMON RESPONSE BUILDER
    # ========================================================

    @staticmethod
    def _payment_response(
        payment: Payment,
        booking: Booking | None,
        message: str | None = None,
        ticket_download_allowed: bool | None = None,
        include_failure_reason: bool = False,
    ) -> dict:
        """
        Build a consistent payment response.
        """

        # ----------------------------------------------------
        # Calculate ticket permission
        # ----------------------------------------------------

        if ticket_download_allowed is None:

            ticket_download_allowed = (
                payment.status
                == PAYMENT_SUCCESS
                and booking is not None
                and booking.status
                == BOOKING_CONFIRMED
                and booking.payment_status
                == PAYMENT_SUCCESS
                and booking.ticket_status
                == TICKET_AVAILABLE
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        result = {
            "success": True,

            # Payment
            "payment_id": (
                payment.payment_id
            ),

            "booking_id": (
                payment.booking_id
            ),

            "booking_reference": (
                booking.booking_reference
                if booking
                else None
            ),

            "amount": (
                float(payment.amount)
            ),

            "currency": (
                payment.currency
            ),

            "payment_method": (
                payment.payment_method
            ),

            "status": (
                payment.status
            ),

            "payment_status": (
                payment.status
            ),

            "transaction_id": (
                payment.transaction_id
            ),

            # Booking
            "booking_status": (
                booking.status
                if booking
                else None
            ),

            "booking_payment_status": (
                booking.payment_status
                if booking
                else None
            ),

            "booking_payment_id": (
                booking.payment_id
                if booking
                else None
            ),

            "paid_at": (
                booking.paid_at.isoformat()
                if booking
                and booking.paid_at
                else None
            ),

            # Ticket
            "ticket_status": (
                booking.ticket_status
                if booking
                else TICKET_NOT_AVAILABLE
            ),

            "ticket_download_allowed": (
                ticket_download_allowed
            ),

            # Timestamps
            "created_at": (
                payment.created_at.isoformat()
                if payment.created_at
                else None
            ),

            "updated_at": (
                payment.updated_at.isoformat()
                if payment.updated_at
                else None
            ),
        }

        # ----------------------------------------------------
        # Optional message
        # ----------------------------------------------------

        if message:

            result["message"] = message

        # ----------------------------------------------------
        # Optional failure reason
        # ----------------------------------------------------

        if include_failure_reason:

            result["failure_reason"] = (
                payment.failure_reason
            )

        return result