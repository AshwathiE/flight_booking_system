from backend.database.connection import SessionLocal
from backend.repositories.flight_repository import FlightRepository


def test_search_flights():

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flights = repository.search_flights(
            origin="Chennai",
            destination="Delhi",
            date="2026-08-20",
            travel_class="Economy"
        )

        print("\nFlights found:")

        for flight in flights:
            print(
                flight.flight_id,
                flight.airline,
                flight.price
            )

        assert isinstance(flights, list)

    finally:
        db.close()


def test_get_flight_by_id():

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flight = repository.get_flight_by_id("AI101")

        print("\nFlight details:")

        if flight:
            print(
                flight.flight_id,
                flight.airline,
                flight.origin,
                flight.destination,
                flight.price
            )

        assert flight is not None

    finally:
        db.close()