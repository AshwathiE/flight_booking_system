from backend.services.chat_service import (
    detect_response_type,
    build_response_data,
)


def test_detect_response_type_flight_results():
    res = {"tool": "search_flights", "status": "success"}
    assert detect_response_type(res) == "flight_results"


def test_detect_response_type_booking_and_error():
    res = {"tool": "create_booking", "status": "success"}
    assert detect_response_type(res) == "booking_success"

    err = {"status": "error"}
    assert detect_response_type(err) == "error"


def test_build_response_data_flights_and_booking():
    flights = [{"id": "F1"}, {"id": "F2"}]
    agent_result = {
        "tool": "search_flights",
        "status": "success",
        "flights": flights,
        "recommended_flight": flights[0],
        "recommendation_reason": "cheap",
        "search_parameters": {"origin": "DEL"},
    }

    data = build_response_data(agent_result, "flight_results")
    assert data["count"] == 2
    assert data["recommended_flight"]["id"] == "F1"

    booking_payload = {
        "booking_id": "B1",
        "booking_reference": "PNR123",
        "flight_id": "F1",
        "number_of_seats": 1,
        "total_price": 200,
        "status": "CONFIRMED",
    }

    br = {"tool": "create_booking", "status": "success", "data": booking_payload}
    bdata = build_response_data(br, "booking_success")
    assert bdata["booking_id"] == "B1"
    assert bdata["download_url"].endswith("/bookings/B1/ticket/pdf")

    err = {"status": "error", "data": {"msg": "oops"}}
    assert build_response_data(err, "error") == {"msg": "oops"}
