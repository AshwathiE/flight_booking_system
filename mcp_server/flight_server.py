from mcp.server import MCPServer

from backend.database.connection import SessionLocal
from backend.repositories.flight_repository import FlightRepository


# =========================================================
# CREATE FLIGHT MCP SERVER
# =========================================================

mcp = MCPServer(
    "Flight MCP Server",
    instructions="MCP server providing flight search and flight information tools."
)


# =========================================================
# TOOL 1: SEARCH FLIGHTS
# =========================================================

@mcp.tool()
def search_flights(
    origin: str | None = "",
    destination: str | None = "",
    date: str | None = "",
    total_seats: int | None = 1,
    travel_class: str | None = None,
    max_price: float | None = None
) -> list:

    origin = origin or ""
    destination = destination or ""
    date = date or ""
    total_seats = total_seats or 1

    # IMPORTANT:
    # Do NOT convert None to Economy.
    # None means the user wants all available classes.

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flights = repository.search_flights(
            origin=origin,
            destination=destination,
            date=date,
            travel_class=travel_class,
            max_price=max_price,
        )

        return [
            {
                "flight_id": flight.flight_id,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "date": str(flight.date),
                "departure_time": str(flight.departure_time),
                "arrival_time": str(flight.arrival_time),
                "price": float(flight.price),
                "travel_class": flight.travel_class,
                "available_seats": flight.available_seats,
            }
            for flight in flights
        ]

    finally:
        db.close()


# =========================================================
# TOOL 2: GET FLIGHT DETAILS
# =========================================================

@mcp.tool()
def get_flight_details(
    flight_id: str
) -> dict:
    """
    Get complete details for a selected flight.
    """

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flight = repository.get_flight_by_id(flight_id)

        if flight is None:
            return {
                "error": "Flight not found",
                "flight_id": flight_id
            }

        return {
            "flight_id": flight.flight_id,
            "airline": flight.airline,
            "origin": flight.origin,
            "destination": flight.destination,
            "date": str(flight.date),
            "departure_time": str(flight.departure_time),
            "arrival_time": str(flight.arrival_time),
            "price": float(flight.price),
            "travel_class": flight.travel_class,
            "available_seats": flight.available_seats
        }

    finally:
        db.close()


# =========================================================
# TOOL 3: CHECK AVAILABILITY
# =========================================================

@mcp.tool()
def check_availability(
    flight_id: str,
    total_seats: int = 1
) -> dict:
    """
    Check whether the requested number of seats is available.
    """

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flight = repository.get_flight_by_id(flight_id)

        if flight is None:
            return {
                "error": "Flight not found",
                "flight_id": flight_id
            }

        available_seats = flight.available_seats

        return {
            "flight_id": flight_id,
            "requested_seats": total_seats,
            "available_seats": available_seats,
            "available": available_seats >= total_seats
        }

    finally:
        db.close()


# =========================================================
# TOOL 4: GET FARE
# =========================================================
@mcp.tool()
def get_fare(
    flight_id: str,
    total_seats: int = 1,
    travel_class: str = "Economy"
) -> dict:
    """
    Calculate the fare for the selected flight.
    """

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flight = repository.get_flight_by_id(flight_id)

        if flight is None:
            return {
                "error": "Flight not found",
                "flight_id": flight_id
            }

        # Check requested class
        if flight.travel_class.lower() != travel_class.lower():
            return {
                "error": "Travel class not available",
                "flight_id": flight_id,
                "requested_class": travel_class,
                "available_class": flight.travel_class
            }

        # Check seats
        if flight.available_seats < total_seats:
            return {
                "error": "Insufficient seats",
                "flight_id": flight_id,
                "total_seats": total_seats,
                "available_seats": flight.available_seats
            }

        # Calculate fare
        base_fare = float(flight.price) * total_seats

        tax = base_fare * 0.05

        service_fee = 100 * total_seats

        total_fare = (
            base_fare
            + tax
            + service_fee
        )

        return {
            "flight_id": flight_id,
            "total_seats": total_seats,
            "travel_class": travel_class,

            "base_fare": round(base_fare, 2),
            "tax": round(tax, 2),
            "service_fee": round(service_fee, 2),
            "total_fare": round(total_fare, 2)
        }

    finally:
        db.close()


# =========================================================
# START MCP SERVER
# =========================================================

if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        streamable_http_path="/mcp"
    )