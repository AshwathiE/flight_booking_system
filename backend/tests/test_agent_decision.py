import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agent.flight_agent import (
    AgentDecision,
    ALLOWED_TOOLS,
    TOOL_MAP,
    decide_tool,
    validate_agent_decision,
    execute_agent_request,
    normalize_city,
    resolve_date_string,
)

# ============================================================
# 1. TEST AGENT DECISION MODEL & WHITELIST
# ============================================================

def test_agent_decision_model():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "destination": "Delhi", "date": "2026-08-20"}
    )
    assert decision.intent == "SEARCH_FLIGHTS"
    assert decision.tool == "search_flights"
    assert decision.parameters["origin"] == "Chennai"


def test_tool_whitelist():
    assert "search_flights" in ALLOWED_TOOLS
    assert "get_flight_details" in ALLOWED_TOOLS
    assert "check_availability" in ALLOWED_TOOLS
    assert "get_fare" in ALLOWED_TOOLS
    assert "create_booking" in ALLOWED_TOOLS
    assert "get_booking" in ALLOWED_TOOLS
    assert "get_user_bookings" in ALLOWED_TOOLS
    assert "cancel_booking" in ALLOWED_TOOLS
    assert "change_booking" in ALLOWED_TOOLS
    assert "delete_database" not in ALLOWED_TOOLS


# ============================================================
# 2. TEST VALIDATION LOGIC FOR ALL INTENTS / TOOLS
# ============================================================

def test_validate_search_flights_success():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={
            "origin": "Chennai",
            "destination": "Delhi",
            "date": "2026-09-25",
            "total_seats": 2,
            "travel_class": "economy"
        }
    )
    params, err = validate_agent_decision(decision)
    assert err is None
    assert params["origin"] == "Chennai"
    assert params["destination"] == "Delhi"
    assert params["date"] == "2026-09-25"
    assert params["total_seats"] == 2
    assert params["travel_class"] == "Economy"


def test_validate_search_flights_missing_origin():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"destination": "Delhi", "date": "2026-09-25"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "origin" in err["missing_fields"]


def test_validate_search_flights_missing_destination():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "date": "2026-09-25"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "destination" in err["missing_fields"]


def test_validate_search_flights_missing_date():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "destination": "Delhi"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "date" in err["missing_fields"]


def test_validate_search_flights_same_origin_destination():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Delhi", "destination": "Delhi", "date": "2026-09-25"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "validation_error"
    assert err["field"] == "origin_destination"


def test_validate_search_flights_past_date():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "destination": "Delhi", "date": "2020-01-01"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "validation_error"
    assert err["field"] == "date"


def test_validate_search_flights_invalid_seats():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "destination": "Delhi", "date": "2026-09-25", "total_seats": -2}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "validation_error"
    assert err["field"] == "total_seats"


def test_validate_search_flights_invalid_class():
    decision = AgentDecision(
        intent="SEARCH_FLIGHTS",
        tool="search_flights",
        parameters={"origin": "Chennai", "destination": "Delhi", "date": "2026-09-25", "travel_class": "luxury"}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "validation_error"
    assert err["field"] == "travel_class"


def test_validate_get_flight_details_success():
    decision = AgentDecision(
        intent="GET_FLIGHT_DETAILS",
        tool="get_flight_details",
        parameters={"flight_id": "6e207"}
    )
    params, err = validate_agent_decision(decision)
    assert err is None
    assert params["flight_id"] == "6E207"


def test_validate_get_flight_details_missing_id():
    decision = AgentDecision(
        intent="GET_FLIGHT_DETAILS",
        tool="get_flight_details",
        parameters={}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "flight_id" in err["missing_fields"]


def test_validate_check_availability_success():
    decision = AgentDecision(
        intent="CHECK_AVAILABILITY",
        tool="check_availability",
        parameters={"flight_id": "AI101", "total_seats": 4}
    )
    params, err = validate_agent_decision(decision)
    assert err is None
    assert params["flight_id"] == "AI101"
    assert params["total_seats"] == 4


def test_validate_check_availability_missing_id():
    decision = AgentDecision(
        intent="CHECK_AVAILABILITY",
        tool="check_availability",
        parameters={"total_seats": 2}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "flight_id" in err["missing_fields"]


def test_validate_get_fare_success():
    decision = AgentDecision(
        intent="GET_FARE",
        tool="get_fare",
        parameters={"flight_id": "6E202", "travel_class": "business", "total_seats": 2}
    )
    params, err = validate_agent_decision(decision)
    assert err is None
    assert params["flight_id"] == "6E202"
    assert params["travel_class"] == "Business"
    assert params["total_seats"] == 2


def test_validate_create_booking_success():
    decision = AgentDecision(
        intent="CREATE_BOOKING",
        tool="create_booking",
        parameters={"flight_id": "6E202", "number_of_seats": 2}
    )
    params, err = validate_agent_decision(decision, context_user_id=10)
    assert err is None
    assert params["flight_id"] == "6E202"
    assert params["number_of_seats"] == 2
    assert params["user_id"] == 10


def test_validate_create_booking_missing_flight():
    decision = AgentDecision(
        intent="CREATE_BOOKING",
        tool="create_booking",
        parameters={"number_of_seats": 2}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert "flight_id" in err["missing_fields"]


def test_validate_get_booking_success():
    decision = AgentDecision(
        intent="GET_BOOKING",
        tool="get_booking",
        parameters={"booking_id": "BK105"}
    )
    params, err = validate_agent_decision(decision)
    assert err is None
    assert params["booking_id"] == 105


def test_validate_cancel_booking_success():
    decision = AgentDecision(
        intent="CANCEL_BOOKING",
        tool="cancel_booking",
        parameters={"booking_id": 42}
    )
    params, err = validate_agent_decision(decision, context_user_id=5)
    assert err is None
    assert params["booking_id"] == 42
    assert params["user_id"] == 5


def test_validate_change_booking_success():
    decision = AgentDecision(
        intent="CHANGE_BOOKING",
        tool="change_booking",
        parameters={"booking_id": 12, "new_flight_id": "AI202", "new_number_of_seats": 3}
    )
    params, err = validate_agent_decision(decision, context_user_id=8)
    assert err is None
    assert params["booking_id"] == 12
    assert params["new_flight_id"] == "AI202"
    assert params["new_number_of_seats"] == 3
    assert params["user_id"] == 8


def test_validate_unknown_intent():
    decision = AgentDecision(
        intent="UNKNOWN",
        tool=None,
        parameters={}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "needs_information"
    assert err["intent"] == "UNKNOWN"


def test_validate_unauthorized_tool():
    decision = AgentDecision(
        intent="UNKNOWN",
        tool="drop_all_tables",
        parameters={}
    )
    params, err = validate_agent_decision(decision)
    assert err is not None
    assert err["status"] == "validation_error"
    assert err["field"] == "tool"


def test_city_normalization():
    assert normalize_city("madras") == "Chennai"
    assert normalize_city("bombay") == "Mumbai"
    assert normalize_city("calcutta") == "Kolkata"
    assert normalize_city("bangalore") == "Bengaluru"
    assert normalize_city("new  delhi ") == "New Delhi"


def test_date_resolution():
    res = resolve_date_string("tomorrow")
    assert res is not None
    assert len(res) == 10
    assert resolve_date_string("2026-08-20") == "2026-08-20"


# ============================================================
# 3. TEST ASYNC END-TO-END EXECUTION FLOW WITH MOCKS
# ============================================================

@pytest.mark.anyio
async def test_execute_agent_unknown_intent():
    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide:
        mock_decide.return_value = AgentDecision(intent="UNKNOWN", tool=None, parameters={})
        
        result = await execute_agent_request("Hello there")
        assert result["status"] == "needs_information"
        assert "Flight Booking AI Assistant" in result["message"]


@pytest.mark.anyio
async def test_execute_agent_missing_param_stops_mcp():
    mock_mcp = AsyncMock()
    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"search_flights": mock_mcp}):
        
        mock_decide.return_value = AgentDecision(
            intent="SEARCH_FLIGHTS",
            tool="search_flights",
            parameters={"origin": "Chennai"}  # missing destination and date
        )
        
        result = await execute_agent_request("Find flights from Chennai")
        assert result["status"] == "needs_information"
        assert "destination" in result["missing_fields"]
        # Crucial check: MCP tool must NOT be called!
        mock_mcp.assert_not_called()


@pytest.mark.anyio
async def test_execute_agent_get_flight_details_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"flight_id": "6E207", "airline": "IndiGo", "origin": "Chennai", "destination": "Delhi", "date": "2026-08-20", "departure_time": "06:00", "arrival_time": "08:45", "price": 5000.0, "travel_class": "Economy", "available_seats": 25}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"get_flight_details": mock_mcp}):
        
        mock_decide.return_value = AgentDecision(
            intent="GET_FLIGHT_DETAILS",
            tool="get_flight_details",
            parameters={"flight_id": "6E207"}
        )

        result = await execute_agent_request("Give me details for flight 6E207")
        assert result["status"] == "success"
        assert result["tool"] == "get_flight_details"
        assert result["data"]["flight_id"] == "6E207"
        assert "IndiGo" in result["message"]
        mock_mcp.assert_called_once_with(flight_id="6E207")


@pytest.mark.anyio
async def test_execute_agent_check_availability_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"flight_id": "6E207", "requested_seats": 3, "available_seats": 25, "available": true}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"check_availability": mock_mcp}):
        
        mock_decide.return_value = AgentDecision(
            intent="CHECK_AVAILABILITY",
            tool="check_availability",
            parameters={"flight_id": "6E207", "total_seats": 3}
        )

        result = await execute_agent_request("Are there 3 seats on 6E207?")
        assert result["status"] == "success"
        assert result["data"]["available"] is True
        mock_mcp.assert_called_once_with(flight_id="6E207", total_seats=3)


@pytest.mark.anyio
async def test_execute_agent_get_fare_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"flight_id": "6E207", "total_seats": 2, "travel_class": "Business", "base_fare": 10000.0, "tax": 500.0, "service_fee": 200.0, "total_fare": 10700.0}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"get_fare": mock_mcp}):
        
        mock_decide.return_value = AgentDecision(
            intent="GET_FARE",
            tool="get_fare",
            parameters={"flight_id": "6E207", "travel_class": "business", "total_seats": 2}
        )

        result = await execute_agent_request("How much is 6E207 in business for 2 seats?")
        assert result["status"] == "success"
        assert result["data"]["total_fare"] == 10700.0
        assert "10,700" in result["message"]
        mock_mcp.assert_called_once_with(flight_id="6E207", total_seats=2, travel_class="Business")


@pytest.mark.anyio
async def test_execute_agent_cancel_booking_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"success": true, "booking_id": 10, "status": "CANCELLED", "seats_released": 2}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"cancel_booking": mock_mcp}):
        
        mock_decide.return_value = AgentDecision(
            intent="CANCEL_BOOKING",
            tool="cancel_booking",
            parameters={"booking_id": 10}
        )

        result = await execute_agent_request("Cancel booking 10", context_user_id=1)
        assert result["status"] == "success"
        assert result["data"]["status"] == "CANCELLED"
        mock_mcp.assert_called_once_with(booking_id=10, user_id=1)


# ============================================================
# 4. TEST PAYMENT MCP TOOLS VIA AI AGENT
# ============================================================

def test_validate_payment_tools():
    # create_payment
    dec = AgentDecision(intent="CREATE_PAYMENT", tool="create_payment", parameters={"booking_id": "BK46", "amount": 5000.0})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is None
    assert params["booking_id"] == 46
    assert params["amount"] == 5000.0
    assert params["user_id"] == 10

    # process_payment
    dec = AgentDecision(intent="PROCESS_PAYMENT", tool="process_payment", parameters={"booking_id": 46, "payment_method": "upi"})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is None
    assert params["booking_id"] == 46
    assert params["payment_method"] == "UPI"

    # process_payment invalid method
    dec = AgentDecision(intent="PROCESS_PAYMENT", tool="process_payment", parameters={"payment_id": "PM1", "payment_method": "BITCOIN"})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is not None
    assert err["status"] == "validation_error"

    # verify_payment
    dec = AgentDecision(intent="VERIFY_PAYMENT", tool="verify_payment", parameters={"payment_id": "PM123"})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is None
    assert params["payment_id"] == "PM123"

    # get_payment_by_booking
    dec = AgentDecision(intent="GET_PAYMENT_BY_BOOKING", tool="get_payment_by_booking", parameters={"booking_id": 46})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is None
    assert params["booking_id"] == 46
    assert params["user_id"] == 10

    # refund_payment
    dec = AgentDecision(intent="REFUND_PAYMENT", tool="refund_payment", parameters={"payment_id": "PM123", "reason": "Trip cancelled"})
    params, err = validate_agent_decision(dec, context_user_id=10)
    assert err is None
    assert params["payment_id"] == "PM123"
    assert params["reason"] == "Trip cancelled"
    assert params["user_id"] == 10


@pytest.mark.anyio
async def test_execute_agent_process_payment_success():
    mock_pay_content = MagicMock()
    mock_pay_content.text = '{"success": true, "payment_id": "PM20260825000001", "booking_id": 46, "status": "SUCCESS", "transaction_id": "TXN20260825000001", "amount": 5000.0, "payment_method": "UPI"}'
    mock_pay_result = MagicMock()
    mock_pay_result.content = [mock_pay_content]

    mock_process_mcp = AsyncMock(return_value=mock_pay_result)
    mock_get_payment = AsyncMock(return_value=mock_pay_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(
             TOOL_MAP,
             {
                 "process_payment": mock_process_mcp,
                 "get_payment": mock_get_payment,
             },
         ):

        mock_decide.return_value = AgentDecision(
            intent="PROCESS_PAYMENT",
            tool="process_payment",
            parameters={"payment_id": "PM20260825000001", "payment_method": "UPI"}
        )

        result = await execute_agent_request("Pay using UPI for payment PM20260825000001", context_user_id=10)
        assert result["status"] == "success"
        assert result["tool"] == "process_payment"
        assert "Payment successful" in result["message"]
        assert "PM20260825000001" in result["message"]
        assert "TXN20260825000001" in result["message"]
        mock_process_mcp.assert_called_once_with(payment_id="PM20260825000001", payment_method="UPI")


@pytest.mark.anyio
async def test_execute_agent_process_payment_failure_clean():
    mock_pay_content = MagicMock()
    mock_pay_content.text = '{"success": false, "payment_id": "PM20260825000002", "booking_id": 46, "status": "FAILED", "failure_reason": "Insufficient balance", "amount": 5000.0, "payment_method": "UPI"}'
    mock_pay_result = MagicMock()
    mock_pay_result.content = [mock_pay_content]

    mock_process_mcp = AsyncMock(return_value=mock_pay_result)
    mock_get_payment = AsyncMock(return_value=mock_pay_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(
             TOOL_MAP,
             {
                 "process_payment": mock_process_mcp,
                 "get_payment": mock_get_payment,
             },
         ):

        mock_decide.return_value = AgentDecision(
            intent="PROCESS_PAYMENT",
            tool="process_payment",
            parameters={"payment_id": "PM20260825000002", "payment_method": "UPI"}
        )

        result = await execute_agent_request("Pay using UPI", context_user_id=10)
        assert result["status"] == "success"  # Result formatted from MCP
        assert "Payment failed" in result["message"]
        assert "Insufficient balance" in result["message"]
        assert "Payment successful" not in result["message"]


@pytest.mark.anyio
async def test_execute_agent_verify_payment_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"success": true, "payment_id": "PM20260825000001", "booking_id": 46, "status": "SUCCESS", "transaction_id": "TXN123", "amount": 5000.0, "payment_method": "CARD"}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"verify_payment": mock_mcp}):

        mock_decide.return_value = AgentDecision(
            intent="VERIFY_PAYMENT",
            tool="verify_payment",
            parameters={"payment_id": "PM20260825000001"}
        )

        result = await execute_agent_request("Is my payment successful?", context_user_id=10)
        assert result["status"] == "success"
        assert "Payment Verification: SUCCESS" in result["message"]
        mock_mcp.assert_called_once_with(payment_id="PM20260825000001", user_id=10)


@pytest.mark.anyio
async def test_execute_agent_refund_payment_mcp():
    mock_content = MagicMock()
    mock_content.text = '{"success": true, "payment_id": "PM20260825000001", "booking_id": 46, "refund_id": "RF20260825000001", "status": "REFUNDED", "amount": 5000.0}'
    mock_result = MagicMock()
    mock_result.content = [mock_content]
    mock_mcp = AsyncMock(return_value=mock_result)

    with patch("agent.flight_agent.decide_tool", new_callable=AsyncMock) as mock_decide, \
         patch.dict(TOOL_MAP, {"refund_payment": mock_mcp}):

        mock_decide.return_value = AgentDecision(
            intent="REFUND_PAYMENT",
            tool="refund_payment",
            parameters={"payment_id": "PM20260825000001", "reason": "Customer request"}
        )

        result = await execute_agent_request("Refund my payment", context_user_id=10)
        assert result["status"] == "success"
        assert "Refund Processed Successfully" in result["message"]
        assert "RF20260825000001" in result["message"]
        mock_mcp.assert_called_once_with(payment_id="PM20260825000001", user_id=10)

