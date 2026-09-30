import threading
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.database.connection import Base
from backend.models.user import User
from backend.models.flight import Flight
from backend.models.booking import Booking
from backend.services.booking_service import BookingService

# Use an in-memory SQLite database for fast unit test execution
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test users
    user1 = User(id=10, name="Alice", email="alice@example.com", password_hash="hash")
    user2 = User(id=20, name="Bob", email="bob@example.com", password_hash="hash")
    db.add_all([user1, user2])

    future_date = date.today() + timedelta(days=5)

    # Seed test flights
    flight1 = Flight(
        flight_id="AI101",
        airline="Air India",
        origin="Chennai",
        destination="Delhi",
        date=future_date,
        departure_time="08:00",
        arrival_time="10:30",
        price=5000.0,
        travel_class="Economy",
        total_seats=180,
        available_seats=180
    )
    flight2 = Flight(
        flight_id="6E202",
        airline="IndiGo",
        origin="Chennai",
        destination="Delhi",
        date=future_date,
        departure_time="12:00",
        arrival_time="14:30",
        price=3500.0,
        travel_class="Economy",
        total_seats=2,
        available_seats=1  # Only 1 seat left for testing
    )
    db.add_all([flight1, flight2])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def get_test_db():
    return TestingSessionLocal()


# 1. Successful booking
def test_successful_booking():
    db = get_test_db()
    res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2)
    db.close()

    assert res["success"] is True
    assert res["number_of_seats"] == 2
    assert res["total_price"] == 10700.0
    assert res["status"] == "PENDING_PAYMENT"
    assert res["booking_reference"].startswith("BK")

    # Check database persistence
    db = get_test_db()
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 178
    db.close()


# 2. Flight not found
def test_flight_not_found():
    db = get_test_db()
    res = BookingService.create_booking(db, user_id=10, flight_id="INVALID999", number_of_seats=1)
    db.close()

    assert res["success"] is False
    assert res["error"] == "FLIGHT_NOT_FOUND"


# 3. User not found
def test_user_not_found():
    db = get_test_db()
    res = BookingService.create_booking(db, user_id=9999, flight_id="AI101", number_of_seats=1)
    db.close()

    assert res["success"] is False
    assert res["error"] == "USER_NOT_FOUND"


# 4. Invalid seat count
def test_invalid_seat_count():
    db = get_test_db()
    res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=0)
    db.close()

    assert res["success"] is False
    assert res["error"] == "INVALID_SEAT_COUNT"


# 5. Not enough seats
def test_not_enough_seats():
    db = get_test_db()
    res = BookingService.create_booking(db, user_id=10, flight_id="6E202", number_of_seats=5)
    db.close()

    assert res["success"] is False
    assert res["error"] == "NOT_ENOUGH_SEATS"


# 6. Successful cancellation
def test_successful_cancellation():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2)
    booking_id = booking_res["booking_id"]

    cancel_res = BookingService.cancel_booking(db, booking_id=booking_id, user_id=10)
    db.close()

    assert cancel_res["success"] is True
    assert cancel_res["status"] == "CANCELLED"


# 7. Cancellation returns seats
def test_cancellation_returns_seats():
    db = get_test_db()
    BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=5)
    
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 175

    booking = db.query(Booking).filter(Booking.user_id == 10).first()
    cancel_res = BookingService.cancel_booking(db, booking_id=booking.id, user_id=10)
    
    assert cancel_res["success"] is True
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 180
    db.close()


# 8. Cannot cancel already cancelled booking
def test_cannot_cancel_already_cancelled_booking():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1)
    booking_id = booking_res["booking_id"]

    BookingService.cancel_booking(db, booking_id=booking_id, user_id=10)
    second_cancel = BookingService.cancel_booking(db, booking_id=booking_id, user_id=10)
    db.close()

    assert second_cancel["success"] is False
    assert second_cancel["error"] == "BOOKING_ALREADY_CANCELLED"


# 9. Successful booking change
def test_successful_booking_change():
    db = get_test_db()
    # Book on AI101
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2)
    booking_id = booking_res["booking_id"]

    # Change to 6E202 (which has 1 seat available) for 1 seat
    change_res = BookingService.change_booking(
        db, booking_id=booking_id, user_id=10, new_flight_id="6E202", new_number_of_seats=1
    )
    db.close()

    assert change_res["success"] is True
    assert change_res["flight_id"] == "6E202"
    assert change_res["number_of_seats"] == 1
    assert change_res["total_price"] == 3775.0

    # Verify old seats restored and new seats deducted
    db = get_test_db()
    old_flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    new_flight = db.query(Flight).filter(Flight.flight_id == "6E202").first()
    assert old_flight.available_seats == 180
    assert new_flight.available_seats == 0
    db.close()


# 10. Cannot change to unavailable flight
def test_cannot_change_to_unavailable_flight():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2)
    booking_id = booking_res["booking_id"]

    # 6E202 has only 1 seat available, request 2 seats
    change_res = BookingService.change_booking(
        db, booking_id=booking_id, user_id=10, new_flight_id="6E202", new_number_of_seats=2
    )
    db.close()

    assert change_res["success"] is False
    assert change_res["error"] == "NOT_ENOUGH_SEATS"

    # Verify booking remained unchanged on AI101
    db = get_test_db()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.flight_id == "AI101"
    assert booking.number_of_seats == 2
    db.close()


# 11. User cannot access another user's booking
def test_user_cannot_access_another_user_booking():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1)
    booking_id = booking_res["booking_id"]

    # Bob (user 20) attempts to access Alice's booking
    res = BookingService.get_booking(db, booking_id=booking_id, requesting_user_id=20)
    db.close()

    assert res["success"] is False
    assert res["error"] == "UNAUTHORIZED"


# 12. Concurrent booking protection
def test_concurrent_booking_protection():
    # 6E202 has only 1 seat left
    results = []

    def attempt_booking(user_id):
        db = get_test_db()
        res = BookingService.create_booking(db, user_id=user_id, flight_id="6E202", number_of_seats=1)
        results.append(res)
        db.close()

    t1 = threading.Thread(target=attempt_booking, args=(10,))
    t2 = threading.Thread(target=attempt_booking, args=(20,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    successes = [r for r in results if r["success"] is True]
    failures = [r for r in results if r["success"] is False]

    assert len(successes) == 1
    assert len(failures) == 1

    # Check available seats never fell below 0
    db = get_test_db()
    flight = db.query(Flight).filter(Flight.flight_id == "6E202").first()
    assert flight.available_seats >= 0
    db.close()


# 13. Transaction rollback
def test_transaction_rollback_on_failure():
    db = get_test_db()

    # Attempt invalid booking with negative seats or non-existent user
    res = BookingService.create_booking(db, user_id=999, flight_id="AI101", number_of_seats=2)

    assert res["success"] is False
    # Verify no seats deducted and no booking record created
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 180

    booking_count = db.query(Booking).count()
    assert booking_count == 0
    db.close()
