from sqlalchemy.orm import Session
from backend.models.flight import Flight
from backend.utils.datetime_utils import (
    get_current_date_kolkata,
    is_flight_in_future,
)


class FlightRepository:

    def __init__(self, db: Session):
        self.db = db

    def search_flights(
        self,
        origin: str | None = "",
        destination: str | None = "",
        date: str | None = "",
        travel_class: str | None = None,
        max_price: float | None = None
    ):
        origin_str = (origin or "").strip()
        dest_str = (destination or "").strip()
        date_str = (date or "").strip()
        class_str = (travel_class or "").strip()

        # If a specific date is given, verify it is not entirely in the past
        if date_str:
            try:
                today_kolkata = get_current_date_kolkata()
                from datetime import datetime
                search_d = datetime.strptime(date_str, "%Y-%m-%d").date()
                if search_d < today_kolkata:
                    # Past date -> return no flights
                    return []
            except ValueError:
                pass

        query = self.db.query(Flight)

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

        all_matching = query.all()

        # Filter strictly for future flights (comparing full departure datetime in Asia/Kolkata)
        future_flights = [
            f for f in all_matching
            if is_flight_in_future(f.date, f.departure_time, f.flight_id)
        ]

        return future_flights

    def get_flight_by_id(self, flight_id: str):
        flight_id_str = (flight_id or "").strip()
        return self.db.query(Flight).filter(
            Flight.flight_id == flight_id_str
        ).first()