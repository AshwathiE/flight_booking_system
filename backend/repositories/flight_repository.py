from sqlalchemy.orm import Session
from backend.models.flight import Flight


class FlightRepository:

    def __init__(self, db: Session):
        self.db = db

    def search_flights( ## the function is receving search criteria from FlightMCP server
        self,
        origin: str | None = "",
        destination: str | None = "",
        date: str | None = "",
        travel_class: str | None = "Economy",
        max_price: float | None = None
    ):

        origin_str = (origin or "").strip() ## input cleaning
        dest_str = (destination or "").strip()
        date_str = (date or "").strip()
        class_str = (travel_class or "Economy").strip()

        query = self.db.query(Flight) ## start querry on the flight model

        if origin_str:
            query = query.filter(Flight.origin.ilike(origin_str))
        if dest_str:
            query = query.filter(Flight.destination.ilike(dest_str))
        if date_str:
            query = query.filter(Flight.date == date_str)
        if class_str:
            query = query.filter(Flight.travel_class.ilike(class_str))
        if max_price is not None:
            query = query.filter(Flight.price <= max_price)

        return query.all()

    def get_flight_by_id(self, flight_id: str):

        flight_id_str = (flight_id or "").strip()
        return self.db.query(Flight).filter(
            Flight.flight_id == flight_id_str
        ).first()



def test_search_chennai_delhi():

    db = SessionLocal()

    try:
        repository = FlightRepository(db)

        flights = repository.search_flights(
            origin="Chennai",
            destination="Delhi",
            date="2026-08-20",
            travel_class="Economy"
        )

        print("\nFlights returned:")

        for flight in flights:
            print(
                flight.flight_id,
                flight.airline,
                flight.origin,
                flight.destination,
                flight.date,
                flight.travel_class,
                flight.available_seats
            )

        assert len(flights) > 0

    finally:
        db.close()