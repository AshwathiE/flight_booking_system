import ast
from pathlib import Path

# Use AST to extract the two pure functions safely without importing module-level
# dependencies like DB, mcp clients or reportlab.
src_path = Path("backend/services/chat_service.py")
src = src_path.read_text(encoding="utf-8")
tree = ast.parse(src)

def _extract_funcs_ast(names):
    funcs = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            mod = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(mod)
            code = compile(mod, filename=str(src_path), mode="exec")
            import typing
            ns = {"Any": typing.Any, "Optional": typing.Optional}
            exec(code, ns)
            funcs[node.name] = ns[node.name]
    missing = set(names) - set(funcs.keys())
    if missing:
        raise RuntimeError(f"functions not found in source: {missing}")
    return funcs

_f = _extract_funcs_ast(["detect_response_type", "build_response_data"])
detect_response_type = _f["detect_response_type"]
build_response_data = _f["build_response_data"]


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
