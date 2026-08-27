import logging
from typing import Any, Optional

from agent.flight_agent import execute_agent_request

from backend.models.user import User
from backend.schemas.chat import ChatResponse
from backend.utils.chat_helpers import (
    append_to_conversation,
    build_context_message,
    enforce_user_authorization,
)


logger = logging.getLogger("chat_service")


def detect_response_type(agent_result: dict) -> str:

    tool = agent_result.get("tool")
    agent_status = agent_result.get("status", "")

    if agent_status == "error":
        return "error"

    if (
        tool == "search_flights"
        and agent_status in (
            "success",
            "no_results",
            "no_availability",
        )
    ):
        return "flight_results"

    if (
        tool == "create_booking"
        and agent_status == "success"
    ):
        return "booking_success"

    if (
        tool in (
            "get_booking",
            "get_user_bookings",
        )
        and agent_status == "success"
    ):
        return "booking_summary"

    if (
        tool in (
            "create_payment",
            "process_payment",
            "verify_payment",
            "get_payment",
            "get_payment_by_booking",
            "refund_payment",
        )
        and agent_status == "success"
    ):
        return "payment_summary"

    if agent_status in (
        "needs_information",
        "validation_error",
    ):
        return "text"

    return "text"



def build_response_data(
    agent_result: dict,
    response_type: str,
) -> Optional[Any]:

    if response_type == "flight_results":

        flights = agent_result.get("flights", [])

        return {
            "flights": flights,
            "recommended_flight": agent_result.get(
                "recommended_flight"
            ),
            "recommendation_reason": agent_result.get(
                "recommendation_reason"
            ),
            "search_parameters": agent_result.get(
                "search_parameters"
            ),
            "count": len(flights),
        }

    if response_type == "booking_success":

        payload = agent_result.get("data", {})

        booking_id = payload.get("booking_id")

        return {
            "booking_id": booking_id,
            "booking_reference": payload.get(
                "booking_reference"
            ),
            "flight_id": payload.get("flight_id"),
            "number_of_seats": payload.get(
                "number_of_seats"
            ),
            "total_price": payload.get(
                "total_price"
            ),
            "status": payload.get("status"),
            "download_url": (
                f"/bookings/{booking_id}/ticket/pdf"
                if booking_id
                else None
            ),
        }

    if response_type == "booking_summary":

        payload = agent_result.get("data", {})

        if agent_result.get("tool") == "get_user_bookings":
            return payload

        booking_id = (
            payload.get("id")
            or payload.get("booking_id")
        )

        return {
            **payload,
            "download_url": (
                f"/bookings/{booking_id}/ticket/pdf"
                if booking_id
                else None
            ),
        }

    if response_type == "payment_summary":
        return agent_result.get("data", {})

    if response_type == "error":
        return agent_result.get("data")


    return None


async def process_chat(
    user_message: str,
    current_user: User,
) -> ChatResponse:

    context_message = build_context_message(
        current_user.id,
        user_message,
    )

    try:
        agent_result = await execute_agent_request(
            user_request=context_message,
            context_user_id=current_user.id,
        )

    except Exception:
        logger.exception(
            "Chat agent execution failed."
        )

        error_message = (
            "I'm sorry, I encountered an error. "
            "Please try again."
        )

        append_to_conversation(
            current_user.id,
            "user",
            user_message,
        )

        append_to_conversation(
            current_user.id,
            "assistant",
            error_message,
        )

        return ChatResponse(
            message=error_message,
            type="error",
            status="error",
        )

    agent_result = enforce_user_authorization(
        agent_result,
        current_user.id,
    )

    response_type = detect_response_type(
        agent_result
    )

    agent_message = agent_result.get(
        "message",
        "",
    )

    agent_status = agent_result.get(
        "status",
        "",
    )

    tool = agent_result.get("tool")
    intent = agent_result.get("intent")

    data = build_response_data(
        agent_result,
        response_type,
    )

    append_to_conversation(
        current_user.id,
        "user",
        user_message,
    )

    append_to_conversation(
        current_user.id,
        "assistant",
        agent_message,
    )

    return ChatResponse(
        message=agent_message,
        type=response_type,
        data=data,
        intent=intent,
        tool=tool,
        status=agent_status,
    )