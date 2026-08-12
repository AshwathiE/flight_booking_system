from backend.database.connection import SessionLocal

from backend.models.flight import Flight


flights = [

    Flight(
        flight_id="AI101",
        airline="Air India",
        origin="Chennai",
        destination="Delhi",
        date="2026-08-15",
        departure_time="06:00",
        arrival_time="09:00",
        price=5500,
        travel_class="Economy",
    ),

    Flight(
        flight_id="6E202",
        airline="IndiGo",
        origin="Chennai",
        destination="Delhi",
        date="2026-08-15",
        departure_time="10:00",
        arrival_time="13:00",
        price=4800,
        travel_class="Economy",
    ),

    Flight(
        flight_id="UK303",
        airline="Vistara",
        origin="Chennai",
        destination="Delhi",
        date="2026-08-15",
        departure_time="15:00",
        arrival_time="18:00",
        price=6200,
        travel_class="Economy",
    ),
]


db = SessionLocal()

try:

    db.add_all(flights)
    db.commit()

    print("Flights inserted successfully")

except Exception as e:

    db.rollback()

    print("Error:", e)

finally:

    db.close()