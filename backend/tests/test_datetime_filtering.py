import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from backend.utils.datetime_utils import (
    KOLKATA_TZ,
    get_current_datetime_kolkata,
    get_current_date_kolkata,
    parse_flight_departure_datetime,
    is_flight_in_future,
)
from backend.models.flight import Flight
from backend.models.user import User
from backend.models.booking import Booking
from backend.repositories.flight_repository import FlightRepository
from backend.services.booking_service import BookingService
from backend.database.connection import SessionLocal


# ============================================================
# 1. TIMEZONE & DATETIME UTILS TESTS
# ============================================================

def test_timezone_is_kolkata():
    curr = get_current_datetime_kolkata()
    assert curr.tzinfo is not None
    # Offset for India Standard Time is UTC+05:30 (+19800 seconds)
    assert curr.utcoffset() == timedelta(hours=5, minutes=30)


def test_parse_flight_departure_datetime():
    dt = parse_flight_departure_datetime("2026-08-20", "14:30:00")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 8
    assert dt.day == 20
    assert dt.hour == 14
    assert dt.minute == 30
    assert dt.utcoffset() == timedelta(hours=5, minutes=30)


def test_is_flight_in_future_past():
    # Frozen current time: 2026-08-17 18:00:00 IST
    mock_now = datetime(2026, 8, 17, 18, 0, 0, tzinfo=KOLKATA_TZ)
    with patch("backend.utils.datetime_utils.get_current_datetime_kolkata", return_value=mock_now):
        # 1. Yesterday's flight
        assert is_flight_in_future("2026-08-16", "10:00:00") is False
        # 2. Today's flight earlier than 18:00
        assert is_flight_in_future("2026-08-17", "10:00:00") is False
        assert is_flight_in_future("2026-08-17", "17:59:00") is False
        # 3. Today's flight later than 18:00
        assert is_flight_in_future("2026-08-17", "18:30:00") is True
        # 4. Tomorrow's flight
        assert is_flight_in_future("2026-08-18", "06:00:00") is True


# ============================================================
# 2. FLIGHT REPOSITORY SEARCH FILTERING TESTS
# ============================================================

def test_flight_repository_filters_past_flights():
    mock_db = MagicMock(spec=Session)

    # Prepare mock flights:
    # f1: Yesterday (2026-08-16 10:00)
    # f2: Today departed (2026-08-17 12:00)
    # f3: Today future (2026-08-17 21:00)
    # f4: Tomorrow (2026-08-18 09:00)
    f1 = Flight(flight_id="F1", origin="Chennai", destination="Delhi", date=date(2026, 8, 16), departure_time="10:00:00", arrival_time="12:30:00", price=5000.0, travel_class="Economy", available_seats=10)
    f2 = Flight(flight_id="F2", origin="Chennai", destination="Delhi", date=date(2026, 8, 17), departure_time="12:00:00", arrival_time="14:30:00", price=5000.0, travel_class="Economy", available_seats=10)
    f3 = Flight(flight_id="F3", origin="Chennai", destination="Delhi", date=date(2026, 8, 17), departure_time="21:00:00", arrival_time="23:30:00", price=5000.0, travel_class="Economy", available_seats=10)
    f4 = Flight(flight_id="F4", origin="Chennai", destination="Delhi", date=date(2026, 8, 18), departure_time="09:00:00", arrival_time="11:30:00", price=5000.0, travel_class="Economy", available_seats=10)

    repo = FlightRepository(mock_db)

    # Freeze current time to 2026-08-17 18:00 IST
    mock_now = datetime(2026, 8, 17, 18, 0, 0, tzinfo=KOLKATA_TZ)
    with patch("backend.repositories.flight_repository.get_current_date_kolkata", return_value=mock_now.date()), \
         patch("backend.utils.datetime_utils.get_current_datetime_kolkata", return_value=mock_now):

        # Scenario A: User searches for past date (2026-08-16)
        res_past = repo.search_flights(origin="Chennai", destination="Delhi", date="2026-08-16")
        assert res_past == []

        # Scenario B: User searches today's flights (2026-08-17)
        # Mock query filter returning f2 and f3
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [f2, f3]
        mock_db.query.return_value = mock_query

        res_today = repo.search_flights(origin="Chennai", destination="Delhi", date="2026-08-17")
        # f2 has departed (12:00 < 18:00), f3 is in future (21:00 > 18:00)
        assert len(res_today) == 1
        assert res_today[0].flight_id == "F3"


# ============================================================
# 3. BOOKING SERVICE PAST-FLIGHT VALIDATION TESTS
# ============================================================

def test_booking_service_rejects_departed_flight():
    mock_db = MagicMock(spec=Session)

    # Flight departed earlier today (14:00 IST)
    departed_flight = Flight(
        flight_id="6E_PAST",
        origin="Chennai",
        destination="Delhi",
        date=date(2026, 8, 17),
        departure_time="14:00:00",
        arrival_time="16:30:00",
        price=5000.0,
        travel_class="Economy",
        available_seats=10
    )

    mock_user = User(id=1, name="Test User", email="user@test.com")

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.with_for_update.return_value = mock_query
    
    def side_effect_first():
        # First call is user, second is flight
        return mock_user
    
    mock_query.first.side_effect = [mock_user, departed_flight]
    mock_db.query.return_value = mock_query

    # Current time: 2026-08-17 18:00 IST
    mock_now = datetime(2026, 8, 17, 18, 0, 0, tzinfo=KOLKATA_TZ)
    with patch("backend.services.booking_service.get_current_datetime_kolkata", return_value=mock_now):
        result = BookingService.create_booking(
            db=mock_db,
            user_id=1,
            flight_id="6E_PAST",
            number_of_seats=2
        )

        assert result["success"] is False
        assert result["error"] == "FLIGHT_DEPARTED"
        assert "already departed" in result["message"]


def test_booking_service_allows_future_flight():
    mock_db = MagicMock(spec=Session)

    future_flight = Flight(
        flight_id="6E_FUTURE",
        origin="Chennai",
        destination="Delhi",
        date=date(2026, 8, 17),
        departure_time="21:00:00",
        arrival_time="23:30:00",
        price=5000.0,
        travel_class="Economy",
        available_seats=10
    )

    mock_user = User(id=1, name="Test User", email="user@test.com")

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.with_for_update.return_value = mock_query
    mock_query.update.return_value = 1  # 1 row updated
    mock_query.first.side_effect = [mock_user, future_flight, None]
    mock_db.query.return_value = mock_query

    mock_now = datetime(2026, 8, 17, 18, 0, 0, tzinfo=KOLKATA_TZ)
    with patch("backend.services.booking_service.get_current_datetime_kolkata", return_value=mock_now), \
         patch("backend.services.booking_service.generate_booking_reference", return_value="BK20260817001"):
        result = BookingService.create_booking(
            db=mock_db,
            user_id=1,
            flight_id="6E_FUTURE",
            number_of_seats=2
        )

        assert result["success"] is True
        assert result["status"] == "PENDING_PAYMENT"
        assert result["booking_reference"] == "BK20260817001"
