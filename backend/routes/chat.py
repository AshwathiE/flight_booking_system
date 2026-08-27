import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.user import User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.auth_service import get_current_user
from backend.services.chat_service import process_chat
from backend.services.ticket_service import handle_ticket_intent
from backend.utils.chat_helpers import (
    clear_conversation,
    is_ticket_intent,
)
logger = logging.getLogger("chat_route")
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:

    user_message = (request.message or "").strip()

    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    logger.info(
        "CHAT user_id=%d | message=%r",
        current_user.id,
        user_message,
    )

    # Handle ticket requests separately.
    if is_ticket_intent(user_message):
        return await handle_ticket_intent(
            user_message=user_message,
            current_user=current_user,
        )

    # Handle normal AI chat.
    return await process_chat(
        user_message=user_message,
        current_user=current_user,
    )


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
):
    clear_conversation(current_user.id)

    return {
        "message": "Conversation history cleared."
    }