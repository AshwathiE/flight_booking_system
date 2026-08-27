import logging
import re
from typing import Dict, List, Optional


logger = logging.getLogger("chat_helpers")

MAX_HISTORY = 20

_conversation_store: Dict[int, List[Dict[str, str]]] = {}


def get_conversation(user_id: int) -> List[Dict[str, str]]:
    return _conversation_store.get(user_id, [])


def append_to_conversation(
    user_id: int,
    role: str,
    content: str,
) -> None:
    history = _conversation_store.setdefault(user_id, [])

    history.append({
        "role": role,
        "content": content,
    })

    if len(history) > MAX_HISTORY:
        _conversation_store[user_id] = history[-MAX_HISTORY:]


def build_context_message(
    user_id: int,
    new_message: str,
) -> str:
    history = get_conversation(user_id)

    if not history:
        return new_message

    context_lines = []

    for turn in history[-6:]:
        prefix = (
            "User"
            if turn["role"] == "user"
            else "Assistant"
        )

        context_lines.append(
            f"{prefix}: {turn['content']}"
        )

    context_block = "\n".join(context_lines)

    return (
        f"[Previous conversation]\n"
        f"{context_block}\n\n"
        f"[Current message]\n"
        f"{new_message}"
    )


def clear_conversation(user_id: int) -> None:
    _conversation_store.pop(user_id, None)


TICKET_KEYWORDS = [
    "download ticket",
    "download my ticket",
    "get my ticket",
    "give me my ticket",
    "ticket download",
    "my ticket",
    "generate ticket",
    "ticket for booking",
    "show ticket",
    "view ticket",
    "print ticket",
    "pdf ticket",
]


def is_ticket_intent(message: str) -> bool:
    lower = message.lower()

    return any(
        keyword in lower
        for keyword in TICKET_KEYWORDS
    )


def extract_booking_reference(
    message: str,
) -> Optional[str]:
    match = re.search(
        r"\bBK\d+\b",
        message.upper(),
    )

    if match:
        return match.group(0)

    return None


def extract_booking_id(
    message: str,
) -> Optional[int]:
    match = re.search(
        r"\bbooking\s*#?\s*(\d+)\b",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def enforce_user_authorization(
    agent_result: dict,
    authenticated_user_id: int,
) -> dict:

    data = agent_result.get("data", {})

    if not isinstance(data, dict):
        return agent_result

    result_user_id = data.get("user_id")

    if result_user_id is None:
        return agent_result

    if int(result_user_id) != authenticated_user_id:
        logger.warning(
            "Agent returned user_id=%s but authenticated "
            "user_id=%d. Overriding.",
            result_user_id,
            authenticated_user_id,
        )

        data["user_id"] = authenticated_user_id
        agent_result["data"] = data

    return agent_result