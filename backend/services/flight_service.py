from backend.repositories.flight_repository import (
    get_all_flights,
    get_flight_by_id
)


def search_flights(
    origin: str,
    destination: str,
    date: str,
    travel_class: str = "Economy",
    max_price: float | None = None
):

    flights = get_all_flights()

    results = []

    for flight in flights:

        if flight["origin"].lower() != origin.lower():
            continue

        if flight["destination"].lower() != destination.lower():
            continue

        if flight["date"] != date:
            continue

        if flight["travel_class"].lower() != travel_class.lower():
            continue

        if max_price is not None:
            if flight["price"] > max_price:
                continue

        results.append(flight)

    return results


def get_flight_details(flight_id: str):

    return get_flight_by_id(flight_id)


def check_availability(
    flight_id: str,
    total_seats: int = 1
):

    flight = get_flight_by_id(flight_id)

    if flight is None:
        return {
            "flight_id": flight_id,
            "available": False,
            "error": "Flight not found"
        }

    available_seats = 20

    return {
        "flight_id": flight_id,
        "available": total_seats <= available_seats,
        "available_seats": available_seats,
        "requested_seats": total_seats
    }


def get_fare(
    flight_id: str,
    total_seats: int = 1,
    travel_class: str = "Economy"
):

    flight = get_flight_by_id(flight_id)

    if flight is None:
        return {
            "flight_id": flight_id,
            "available": False,
            "error": "Flight not found"
        }

    if flight["travel_class"].lower() != travel_class.lower():
        return {
            "flight_id": flight_id,
            "available": False,
            "error": "Requested travel class is not available"
        }

    total_fare = flight["price"] * total_seats

    return {
        "flight_id": flight_id,
        "travel_class": travel_class,
        "price_per_seat": flight["price"],
        "total_seats": total_seats,
        "total_fare": total_fare,
        "currency": "INR"
    }