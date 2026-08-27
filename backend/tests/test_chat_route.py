import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.flight_agent import (
    AgentDecision,
    ALLOWED_TOOLS,
    TOOL_MAP,
    decide_tool,
    validate_agent_decision,
    execute_agent_request,
    normalize_city,
    resolve_date_string,
    is_ticket_intent,
    extract_booking_reference,
    extract_booking_id,
)

from backend.services.chat_service import detect_response_type

from backend.utils.chat_helpers import (
    _conversation_store,
    append_to_conversation,
    get_conversation,
    build_context_message,
    enforce_user_authorization,
)


# ─── Reset conversation store between tests ───────────────────────────────────

@pytest.fixture(autouse=True)
def clear_store():
    _conversation_store.clear()
    yield
    _conversation_store.clear()


# ─── is_ticket_intent ─────────────────────────────────────────────────────────

class TestIsTicketIntent:

    def test_download_my_ticket(self):
        assert is_ticket_intent("Download my ticket") is True

    def test_give_me_my_ticket(self):
        assert is_ticket_intent("Give me my ticket") is True

    def test_my_ticket_mixed_case(self):
        assert is_ticket_intent("I want MY TICKET") is True

    def test_pdf_ticket(self):
        assert is_ticket_intent("I need the pdf ticket for my booking") is True

    def test_not_ticket_intent_search(self):
        assert is_ticket_intent("Find flights from Chennai to Delhi") is False

    def test_not_ticket_intent_booking(self):
        assert is_ticket_intent("Book the cheapest flight") is False

    def test_not_ticket_intent_cancel(self):
        assert is_ticket_intent("Cancel my booking") is False

    def test_show_ticket(self):
        assert is_ticket_intent("show ticket for BK2026001") is True

    def test_view_ticket(self):
        assert is_ticket_intent("View ticket") is True


# ─── extract_booking_reference ────────────────────────────────────────────────

class TestExtractBookingReference:

    def test_extract_bk_reference(self):
        assert extract_booking_reference("Download ticket for BK2026001") == "BK2026001"

    def test_extract_bk_lowercase_message(self):
        # The function converts to upper internally
        assert extract_booking_reference("my booking bk2026999 please") == "BK2026999"

    def test_no_reference(self):
        assert extract_booking_reference("Show my latest booking") is None

    def test_extract_from_middle(self):
        assert extract_booking_reference("Get me the ticket BK2026123 now") == "BK2026123"

    def test_no_bk_prefix(self):
        assert extract_booking_reference("booking 12") is None


# ─── extract_booking_id ───────────────────────────────────────────────────────

class TestExtractBookingId:

    def test_booking_number(self):
        assert extract_booking_id("booking 12") == 12

    def test_booking_hash(self):
        assert extract_booking_id("booking #15") == 15

    def test_booking_spaced(self):
        assert extract_booking_id("Cancel booking   7") == 7

    def test_no_booking_id(self):
        assert extract_booking_id("Download my latest ticket") is None

    def test_no_match(self):
        assert extract_booking_id("Find flights from Chennai") is None


# ─── detect_response_type ─────────────────────────────────────────────────────

class TestDetectResponseType:

    def test_flight_results_success(self):
        result = {"tool": "search_flights", "status": "success"}
        assert detect_response_type(result) == "flight_results"

    def test_flight_results_no_results(self):
        result = {"tool": "search_flights", "status": "no_results"}
        assert detect_response_type(result) == "flight_results"

    def test_flight_results_no_availability(self):
        result = {"tool": "search_flights", "status": "no_availability"}
        assert detect_response_type(result) == "flight_results"

    def test_booking_success(self):
        result = {"tool": "create_booking", "status": "success"}
        assert detect_response_type(result) == "booking_success"

    def test_booking_summary_get_booking(self):
        result = {"tool": "get_booking", "status": "success"}
        assert detect_response_type(result) == "booking_summary"

    def test_booking_summary_user_bookings(self):
        result = {"tool": "get_user_bookings", "status": "success"}
        assert detect_response_type(result) == "booking_summary"

    def test_error_status(self):
        result = {"tool": "search_flights", "status": "error"}
        assert detect_response_type(result) == "error"

    def test_needs_information(self):
        result = {"tool": "search_flights", "status": "needs_information"}
        assert detect_response_type(result) == "text"

    def test_validation_error(self):
        result = {"tool": "search_flights", "status": "validation_error"}
        assert detect_response_type(result) == "text"

    def test_unknown_tool(self):
        result = {"tool": "cancel_booking", "status": "success"}
        assert detect_response_type(result) == "text"


# ─── Conversation History ─────────────────────────────────────────────────────

class TestConversationHistory:

    def test_append_and_get(self):
        append_to_conversation(1, "user", "Hello")
        append_to_conversation(1, "assistant", "Hi there!")
        history = get_conversation(1)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_rolling_window(self):
        """Store should keep only last MAX_HISTORY messages."""
        from backend.utils.chat_helpers import MAX_HISTORY
        for i in range(MAX_HISTORY + 10):
            append_to_conversation(99, "user", f"msg {i}")
        history = get_conversation(99)
        assert len(history) <= MAX_HISTORY

    def test_empty_history(self):
        assert get_conversation(999) == []

    def test_user_isolation(self):
        append_to_conversation(1, "user", "User 1 message")
        append_to_conversation(2, "user", "User 2 message")
        assert len(get_conversation(1)) == 1
        assert len(get_conversation(2)) == 1
        assert get_conversation(1)[0]["content"] == "User 1 message"
        assert get_conversation(2)[0]["content"] == "User 2 message"


# ─── build_context_message ────────────────────────────────────────────────────

class TestBuildContextMessage:

    def test_no_history(self):
        msg = build_context_message(42, "Find flights")
        assert msg == "Find flights"

    def test_with_history(self):
        append_to_conversation(10, "user", "Find flights from Chennai to Delhi")
        append_to_conversation(10, "assistant", "I found 3 flights...")
        msg = build_context_message(10, "Book the cheapest one")
        assert "[Previous conversation]" in msg
        assert "Find flights from Chennai to Delhi" in msg
        assert "I found 3 flights" in msg
        assert "[Current message]" in msg
        assert "Book the cheapest one" in msg


# ─── enforce_user_authorization ─────────────────────────────────────────────

class TestEnforceUserAuthorization:

    def test_matching_user_id_unchanged(self):
        result = {"data": {"user_id": 5, "booking_id": 1}}
        out = enforce_user_authorization(result, 5)
        assert out["data"]["user_id"] == 5

    def test_mismatched_user_id_overridden(self):
        result = {"data": {"user_id": 999, "booking_id": 1}}
        out = enforce_user_authorization(result, 5)
        assert out["data"]["user_id"] == 5

    def test_no_data_key(self):
        result = {"message": "Hello", "status": "success"}
        out = enforce_user_authorization(result, 5)
        # Should not raise
        assert out["message"] == "Hello"

    def test_data_without_user_id(self):
        result = {"data": {"booking_id": 1}}
        out = enforce_user_authorization(result, 5)
        # user_id not present, should remain as-is
        assert "user_id" not in out["data"]

    def test_none_data(self):
        result = {"data": None}
        out = enforce_user_authorization(result, 5)
        assert out["data"] is None


# ─── Chat Endpoint Integration (mocked) ──────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_endpoint_unauthenticated():
    """
    Without a token, the dependency should raise 401.
    We test the FastAPI dependency by calling the endpoint
    through a test client with no auth header.
    """
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/chat", json={"message": "Find flights"})
    # Should be 401 (unauthorized) since no Bearer token
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_chat_empty_message_raises():
    """
    Empty message should return 400.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.services.auth_service import get_current_user
    from backend.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.name = "Test"

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/chat", json={"message": "  "})
    assert response.status_code == 400
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_returns_flight_results():
    """
    When agent returns search_flights success, endpoint returns flight_results type.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.services.auth_service import get_current_user
    from backend.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.name = "Test"

    agent_return = {
        "status": "success",
        "intent": "SEARCH_FLIGHTS",
        "tool": "search_flights",
        "flights": [
            {
                "flight_id": "6E101",
                "airline": "IndiGo",
                "origin": "Chennai",
                "destination": "Delhi",
                "date": "2026-08-20",
                "departure_time": "06:00",
                "arrival_time": "09:00",
                "price": 4000,
                "travel_class": "Economy",
                "available_seats": 5,
                "fare": {"total_fare": 4500},
            }
        ],
        "recommended_flight": None,
        "recommendation_reason": None,
        "search_parameters": {
            "origin": "Chennai",
            "destination": "Delhi",
            "date": "2026-08-20",
            "total_seats": 1,
        },
        "message": "I found 1 flight.",
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("backend.services.chat_service.execute_agent_request", new=AsyncMock(return_value=agent_return)):
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"message": "Find flights from Chennai to Delhi tomorrow"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "flight_results"
    assert data["data"]["count"] == 1
    assert data["data"]["flights"][0]["flight_id"] == "6E101"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_booking_success():
    """
    When agent returns create_booking success, endpoint returns booking_success type.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.services.auth_service import get_current_user
    from backend.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.name = "Test"

    agent_return = {
        "status": "success",
        "intent": "CREATE_BOOKING",
        "tool": "create_booking",
        "data": {
            "booking_id": 42,
            "booking_reference": "BK2026042",
            "flight_id": "6E101",
            "number_of_seats": 2,
            "total_price": 9000,
            "status": "CONFIRMED",
            "user_id": 1,
        },
        "message": "Booking confirmed.",
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("backend.services.chat_service.execute_agent_request", new=AsyncMock(return_value=agent_return)):
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Yes, confirm"})

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "booking_success"
    assert data["data"]["booking_reference"] == "BK2026042"
    assert data["data"]["total_price"] == 9000
    assert data["data"]["download_url"] == "/bookings/42/ticket/pdf"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_payment_success():
    """
    When agent returns process_payment success, endpoint returns payment_summary type.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.services.auth_service import get_current_user
    from backend.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 10
    mock_user.name = "Alice"

    agent_return = {
        "status": "success",
        "intent": "PROCESS_PAYMENT",
        "tool": "process_payment",
        "data": {
            "payment_id": "PM20260825000001",
            "booking_id": 46,
            "transaction_id": "TXN123456",
            "amount": 5000.0,
            "status": "SUCCESS",
            "user_id": 10,
        },
        "message": "Payment successful for booking 46.\nPayment ID: PM20260825000001\nTransaction ID: TXN123456\nAmount: ₹5,000",
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("backend.services.chat_service.execute_agent_request", new=AsyncMock(return_value=agent_return)):
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Pay using UPI"})

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "payment_summary"
    assert data["data"]["payment_id"] == "PM20260825000001"
    assert data["data"]["status"] == "SUCCESS"
    assert "Payment successful for booking 46" in data["message"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_ticket_intent_no_bookings():
    """
    When user asks for ticket but has no bookings, returns helpful message.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.services.auth_service import get_current_user
    from backend.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 9999  # unlikely to have bookings
    mock_user.name = "NoBookings"

    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("backend.services.ticket_service.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None  # No bookings

        client = TestClient(app)
        response = client.post("/chat", json={"message": "Download my ticket"})

    assert response.status_code == 200
    data = response.json()
    assert "no" in data["message"].lower() or "don't" in data["message"].lower()
    app.dependency_overrides.clear()

