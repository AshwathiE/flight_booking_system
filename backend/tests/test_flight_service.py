import pytest

from backend.services import flight_service


def make_flight(fid, origin, destination, date, travel_class, price):
    return {
        "id": fid,
        "origin": origin,
        "destination": destination,
        "date": date,
        "travel_class": travel_class,
        "price": price,
    }


def test_search_flights_filters(monkeypatch):
    flights = [
        make_flight("A", "DEL", "BLR", "2026-08-27", "Economy", 100),
        make_flight("B", "DEL", "BLR", "2026-08-26", "Economy", 150),
        make_flight("C", "DEL", "BLR", "2026-08-27", "Business", 300),
    ]

    monkeypatch.setattr(
        flight_service, "get_all_flights", lambda: flights
    )

    results = flight_service.search_flights(
        origin="DEL",
        destination="BLR",
        date="2026-08-27",
        travel_class="Economy",
    )

    assert len(results) == 1
    assert results[0]["id"] == "A"


def test_get_fare_success_and_errors(monkeypatch):
    sample = {
        "flight_id": "F1",
        "price": 200,
        "travel_class": "Economy",
    }

    monkeypatch.setattr(
        flight_service, "get_flight_by_id", lambda fid: sample if fid == "F1" else None
    )

    ok = flight_service.get_fare("F1", total_seats=2, travel_class="Economy")
    assert ok["total_fare"] == 400

    missing = flight_service.get_fare("NOPE")
    assert missing["available"] is False

    class_mismatch = flight_service.get_fare("F1", travel_class="Business")
    assert class_mismatch["available"] is False
