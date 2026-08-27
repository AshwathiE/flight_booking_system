import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.connection import Base
from backend.models.user import User
from backend.models.flight import Flight
from backend.models.booking import Booking
from backend.models.payment import Payment
from backend.services.booking_service import BookingService
from backend.services.payment_service import PaymentService
from backend.utils.payment_gateway import MockPaymentGateway
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

    # Seed test flight
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
        total_seats=10,
        available_seats=10
    )
    db.add(flight1)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def get_test_db():
    return TestingSessionLocal()

# --- SUCCESS CASES ---

def test_create_payment_success():
    db = get_test_db()
    # 1. Create booking (default status is PENDING)
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2, status="PENDING")
    assert booking_res["success"] is True
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # 2. Create payment
    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    assert pay_res["success"] is True
    assert pay_res["status"] == "PENDING"
    assert pay_res["amount"] == total_price
    db.close()

def test_process_upi_payment_success():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="UPI")
    assert proc_res["success"] is True
    assert proc_res["status"] == "SUCCESS"
    assert proc_res["transaction_id"] is not None

    # Verify booking status became CONFIRMED
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CONFIRMED"
    db.close()

def test_process_card_payment_success():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="CARD")
    assert proc_res["success"] is True
    assert proc_res["status"] == "SUCCESS"
    db.close()

def test_process_net_banking_payment_success():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="NET_BANKING")
    assert proc_res["success"] is True
    assert proc_res["status"] == "SUCCESS"
    db.close()

def test_verify_and_get_payment():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    # Verify payment
    verify_res = PaymentService.verify_payment(db, payment_id=payment_id)
    assert verify_res["success"] is True
    assert verify_res["status"] == "PENDING"

    # Get payment by ID
    get_res = PaymentService.get_payment(db, payment_id=payment_id, requesting_user_id=10)
    assert get_res["success"] is True
    assert get_res["amount"] == total_price

    # Get payment by booking
    by_booking_res = PaymentService.get_payment_by_booking(db, booking_id=booking_id, requesting_user_id=10)
    assert by_booking_res["success"] is True
    assert by_booking_res["payment_id"] == payment_id
    db.close()

def test_refund_successful_payment():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    PaymentService.process_payment(db, payment_id=payment_id, payment_method="UPI")

    # Refund
    ref_res = PaymentService.refund_payment(db, payment_id=payment_id, reason="Customer cancel", requesting_user_id=10)
    assert ref_res["success"] is True
    assert ref_res["status"] == "REFUNDED"
    assert ref_res["refund_id"] is not None

    # Verify booking status became CANCELLED
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CANCELLED"
    db.close()


# --- FAILURE CASES ---

def test_create_payment_invalid_booking():
    db = get_test_db()
    res = PaymentService.create_payment(db, booking_id=999, user_id=10, amount=100.0, currency="INR")
    assert res["success"] is False
    assert res["error"] == "BOOKING_NOT_FOUND"
    db.close()

def test_create_payment_unauthorized_user():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # Bob (user 20) attempts to create payment for Alice's booking
    res = PaymentService.create_payment(db, booking_id=booking_id, user_id=20, amount=total_price, currency="INR")
    assert res["success"] is False
    assert res["error"] == "UNAUTHORIZED"
    db.close()

def test_create_payment_invalid_amount():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # Invalid amount
    res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price + 10.0, currency="INR")
    assert res["success"] is False
    assert res["error"] == "INVALID_AMOUNT"
    db.close()

def test_create_payment_cancelled_booking():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # Cancel booking first
    BookingService.cancel_booking(db, booking_id=booking_id, user_id=10)

    # Attempt payment
    res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    assert res["success"] is False
    assert res["error"] == "BOOKING_ALREADY_CANCELLED"
    db.close()

def test_create_payment_duplicate_payment():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # Create first payment
    PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")

    # Create second payment
    res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    assert res["success"] is False
    assert res["error"] == "DUPLICATE_PAYMENT"
    db.close()

def test_process_payment_gateway_failure():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    # Pass method UPI_FAILED to trigger mock failure
    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="UPI_FAILED")
    assert proc_res["success"] is False
    assert proc_res["status"] == "FAILED"

    # Booking must NOT be confirmed and seats must be released!
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CANCELLED"
    db.close()

def test_process_payment_timeout():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    # Pass method UPI_TIMEOUT to trigger mock timeout
    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="UPI_TIMEOUT")
    assert proc_res["success"] is False
    assert proc_res["status"] == "FAILED"
    assert proc_res["failure_reason"] == "Mock payment timeout"

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CANCELLED"
    db.close()

def test_refund_failed_payment():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    # Refund a PENDING payment should fail
    res = PaymentService.refund_payment(db, payment_id=payment_id, reason="cancel", requesting_user_id=10)
    assert res["success"] is False
    assert res["error"] == "PAYMENT_NOT_PAID"
    db.close()

def test_refund_duplicate():
    db = get_test_db()
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=1, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    PaymentService.process_payment(db, payment_id=payment_id, payment_method="UPI")

    # First refund succeeds
    res1 = PaymentService.refund_payment(db, payment_id=payment_id, reason="cancel", requesting_user_id=10)
    assert res1["success"] is True

    # Second refund fails
    res2 = PaymentService.refund_payment(db, payment_id=payment_id, reason="cancel", requesting_user_id=10)
    assert res2["success"] is False
    assert res2["error"] == "PAYMENT_ALREADY_REFUNDED"
    db.close()


# --- INTEGRATION CASES ---

def test_flight_booking_payment_integration_flow():
    db = get_test_db()
    # 1. Check flight seats
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 10

    # 2. Create Booking
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2, status="PENDING")
    assert booking_res["success"] is True
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    # 3. Check seats deducted (temporarily locked)
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 8

    # 4. Create Payment
    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    assert pay_res["success"] is True
    payment_id = pay_res["payment_id"]

    # 5. Process Payment
    proc_res = PaymentService.process_payment(db, payment_id=payment_id, payment_method="CARD")
    assert proc_res["success"] is True

    # 6. Verify status and booking confirmation
    verify_res = PaymentService.verify_payment(db, payment_id=payment_id)
    assert verify_res["status"] == "SUCCESS"

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CONFIRMED"

    # Seats should remain deducted
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 8
    db.close()

def test_booking_payment_refund_flow():
    db = get_test_db()
    # 1. Create paid booking
    booking_res = BookingService.create_booking(db, user_id=10, flight_id="AI101", number_of_seats=2, status="PENDING")
    booking_id = booking_res["booking_id"]
    total_price = booking_res["total_price"]

    pay_res = PaymentService.create_payment(db, booking_id=booking_id, user_id=10, amount=total_price, currency="INR")
    payment_id = pay_res["payment_id"]

    PaymentService.process_payment(db, payment_id=payment_id, payment_method="CARD")

    # Verify seats are at 8
    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 8

    # 2. Refund Payment
    ref_res = PaymentService.refund_payment(db, payment_id=payment_id, reason="Customer cancelled", requesting_user_id=10)
    assert ref_res["success"] is True

    # 3. Verify booking cancelled and seats returned
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    assert booking.status == "CANCELLED"

    flight = db.query(Flight).filter(Flight.flight_id == "AI101").first()
    assert flight.available_seats == 10
    db.close()
