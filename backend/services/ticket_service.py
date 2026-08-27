from typing import Optional

from backend.database.connection import SessionLocal
from backend.models.booking import Booking
from backend.models.user import User
from backend.schemas.chat import ChatResponse
from backend.utils.chat_helpers import (
    append_to_conversation,
    extract_booking_id,
    extract_booking_reference,
)


def _error_response(
    user_id: int,
    user_message: str,
    message: str,
) -> ChatResponse:

    append_to_conversation(
        user_id,
        "user",
        user_message,
    )

    append_to_conversation(
        user_id,
        "assistant",
        message,
    )

    return ChatResponse(
        message=message,
        type="error",
        status="error",
    )


async def handle_ticket_intent(
    user_message: str,
    current_user: User,
) -> ChatResponse:

    db = SessionLocal()

    try:
        booking_ref = extract_booking_reference(
            user_message
        )

        booking_id = extract_booking_id(
            user_message
        )

        booking: Optional[Booking] = None

        # 1. Search using booking reference
        if booking_ref:

            booking = (
                db.query(Booking)
                .filter(
                    Booking.booking_reference == booking_ref,
                    Booking.user_id == current_user.id,
                )
                .first()
            )

            if not booking:
                return _error_response(
                    current_user.id,
                    user_message,
                    (
                        f"I couldn't find booking "
                        f"{booking_ref} linked to your account. "
                        "Please check the booking reference "
                        "and try again."
                    ),
                )

        # 2. Search using booking ID
        elif booking_id:

            booking = (
                db.query(Booking)
                .filter(
                    Booking.id == booking_id,
                    Booking.user_id == current_user.id,
                )
                .first()
            )

            if not booking:
                return _error_response(
                    current_user.id,
                    user_message,
                    (
                        f"I couldn't find booking "
                        f"#{booking_id} linked to your account. "
                        "Please check and try again."
                    ),
                )

        # 3. Find latest booking
        else:

            booking = (
                db.query(Booking)
                .filter(
                    Booking.user_id == current_user.id,
                    Booking.status == "CONFIRMED",
                )
                .order_by(
                    Booking.created_at.desc()
                )
                .first()
            )

            # If no confirmed booking exists,
            # get the latest booking of any status.
            if not booking:
                booking = (
                    db.query(Booking)
                    .filter(
                        Booking.user_id == current_user.id
                    )
                    .order_by(
                        Booking.created_at.desc()
                    )
                    .first()
                )

            if not booking:
                message = (
                    "You don't have any bookings yet. "
                    "Would you like to search for a flight?"
                )

                append_to_conversation(
                    current_user.id,
                    "user",
                    user_message,
                )

                append_to_conversation(
                    current_user.id,
                    "assistant",
                    message,
                )

                return ChatResponse(
                    message=message,
                    type="text",
                    status="no_results",
                )

        download_url = (
            f"/bookings/{booking.id}/ticket/pdf"
        )

        message = (
            f"Your ticket for booking "
            f"**{booking.booking_reference}** is ready! "
            "Click the button below to download "
            "your PDF ticket."
        )

        append_to_conversation(
            current_user.id,
            "user",
            user_message,
        )

        append_to_conversation(
            current_user.id,
            "assistant",
            message,
        )

        return ChatResponse(
            message=message,
            type="ticket",
            data={
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "flight_id": booking.flight_id,
                "download_url": download_url,
                "status": booking.status,
            },
            status="success",
        )

    finally:
        db.close()