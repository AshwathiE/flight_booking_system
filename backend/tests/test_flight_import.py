import io
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.connection import Base
from backend.models.admin import Admin
from backend.models.user import User
from backend.models.flight import Flight
from backend.services.auth_service import hash_password, create_access_token
from backend.services.flight_import_service import (
    parse_csv_bytes,
    parse_excel_bytes,
    import_flights_from_records,
)
from backend.main import app
from backend.routes.admin_auth import get_db

# ── Test Database Setup ───────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed an active admin
    admin = Admin(
        id=1,
        name="Admin Test",
        email="admin@test.com",
        password_hash=hash_password("adminpass123"),
        role="admin",
        status="active",
    )
    # Seed a normal user
    user = User(
        id=1,
        name="User Test",
        email="user@test.com",
        password_hash=hash_password("userpass123"),
    )
    # Seed an existing flight for duplicate checking
    existing_flight = Flight(
        flight_id="EXISTING01",
        airline="Air India",
        origin="Chennai",
        destination="Delhi",
        date=date(2026, 8, 20),
        departure_time="08:00",
        arrival_time="10:30",
        price=5000.0,
        travel_class="Economy",
        total_seats=180,
        available_seats=180,
    )

    db.add_all([admin, user, existing_flight])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


# ── Tokens ───────────────────────────────────────────────────────────────────

def get_admin_token() -> str:
    return create_access_token(user_id=1, role="admin")


def get_user_token() -> str:
    return create_access_token(user_id=1, role="user")


# ── 1. Unit Tests for CSV Parser & Validator ─────────────────────────────────

def test_parse_csv_valid():
    csv_data = (
        "flight_id,airline,origin,destination,date,departure_time,arrival_time,price,travel_class,available_seats,total_seats\n"
        "AI201,Air India,Chennai,Delhi,2026-08-25,06:00,09:00,5500,Economy,180,180\n"
        "6E302,IndiGo,Bangalore,Mumbai,2026-08-26,10:00,11:45,4200,Economy,150,180\n"
    ).encode("utf-8")

    records, err = parse_csv_bytes(csv_data)
    assert err is None
    assert len(records) == 2
    assert records[0]["flight_id"] == "AI201"


def test_parse_csv_missing_header():
    csv_data = "flight_id,airline,origin\nAI201,Air India,Chennai\n".encode("utf-8")
    records, err = parse_csv_bytes(csv_data)
    assert records == []
    assert "missing required columns" in err.lower()


def test_parse_csv_empty():
    records, err = parse_csv_bytes(b"")
    assert records == []
    assert "empty" in err.lower()


def test_import_service_validation_and_partial_success():
    db = TestingSessionLocal()
    records = [
        # Valid row 1
        {
            "flight_id": "VALID01",
            "airline": "Air India",
            "origin": "Chennai",
            "destination": "Delhi",
            "date": "2026-08-25",
            "departure_time": "06:00",
            "arrival_time": "09:00",
            "price": 5500,
            "travel_class": "Economy",
            "available_seats": 180,
        },
        # Invalid row 2: same origin & destination
        {
            "flight_id": "INVALID02",
            "airline": "Air India",
            "origin": "Delhi",
            "destination": "Delhi",
            "date": "2026-08-25",
            "departure_time": "06:00",
            "arrival_time": "09:00",
            "price": 5500,
            "travel_class": "Economy",
            "available_seats": 180,
        },
        # Invalid row 3: negative price
        {
            "flight_id": "INVALID03",
            "airline": "IndiGo",
            "origin": "Chennai",
            "destination": "Mumbai",
            "date": "2026-08-25",
            "departure_time": "06:00",
            "arrival_time": "09:00",
            "price": -100,
            "travel_class": "Economy",
            "available_seats": 180,
        },
        # Invalid row 4: duplicate flight_id (pre-seeded)
        {
            "flight_id": "EXISTING01",
            "airline": "Air India",
            "origin": "Chennai",
            "destination": "Delhi",
            "date": "2026-08-25",
            "departure_time": "06:00",
            "arrival_time": "09:00",
            "price": 5500,
            "travel_class": "Economy",
            "available_seats": 180,
        },
        # Invalid row 5: bad date format
        {
            "flight_id": "INVALID05",
            "airline": "Air India",
            "origin": "Chennai",
            "destination": "Delhi",
            "date": "25-08-2026",
            "departure_time": "06:00",
            "arrival_time": "09:00",
            "price": 5500,
            "travel_class": "Economy",
            "available_seats": 180,
        },
    ]

    summary = import_flights_from_records(records, db)
    db.close()

    assert summary.total_rows == 5
    assert summary.imported == 1
    assert summary.failed == 4
    assert len(summary.row_errors) == 4

    # Verify that VALID01 is in the database
    db = TestingSessionLocal()
    f = db.query(Flight).filter(Flight.flight_id == "VALID01").first()
    assert f is not None
    assert f.airline == "Air India"
    db.close()


# ── 2. Endpoint Tests: POST /admin/flights (Manual Entry) ────────────────────

def test_admin_create_flight_success():
    token = get_admin_token()
    payload = {
        "flight_id": "MANUAL01",
        "airline": "Vistara",
        "origin": "Mumbai",
        "destination": "Goa",
        "date": "2026-09-01",
        "departure_time": "14:00",
        "arrival_time": "15:15",
        "price": 3800.0,
        "travel_class": "Economy",
        "available_seats": 120,
        "total_seats": 180,
    }
    response = client.post(
        "/admin/flights",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["flight_id"] == "MANUAL01"

    # Verify in DB
    db = TestingSessionLocal()
    f = db.query(Flight).filter(Flight.flight_id == "MANUAL01").first()
    assert f is not None
    assert f.price == 3800.0
    db.close()


def test_admin_create_flight_duplicate_rejected():
    token = get_admin_token()
    payload = {
        "flight_id": "EXISTING01",
        "airline": "Air India",
        "origin": "Chennai",
        "destination": "Delhi",
        "date": "2026-08-20",
        "departure_time": "08:00",
        "arrival_time": "10:30",
        "price": 5000.0,
        "travel_class": "Economy",
        "available_seats": 180,
    }
    response = client.post(
        "/admin/flights",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_admin_create_flight_same_origin_destination():
    token = get_admin_token()
    payload = {
        "flight_id": "SAME01",
        "airline": "Air India",
        "origin": "Chennai",
        "destination": "chennai",
        "date": "2026-08-20",
        "departure_time": "08:00",
        "arrival_time": "10:30",
        "price": 5000.0,
        "travel_class": "Economy",
        "available_seats": 180,
    }
    response = client.post(
        "/admin/flights",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_admin_create_flight_unauthorized_user():
    token = get_user_token()
    payload = {
        "flight_id": "UNAUTH01",
        "airline": "Air India",
        "origin": "Chennai",
        "destination": "Delhi",
        "date": "2026-08-20",
        "departure_time": "08:00",
        "arrival_time": "10:30",
        "price": 5000.0,
        "travel_class": "Economy",
        "available_seats": 180,
    }
    response = client.post(
        "/admin/flights",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ── 3. Endpoint Tests: POST /admin/flights/upload/csv ────────────────────────

def test_admin_upload_csv_success():
    token = get_admin_token()
    csv_content = (
        "flight_id,airline,origin,destination,date,departure_time,arrival_time,price,travel_class,available_seats,total_seats\n"
        "CSV01,SpiceJet,Kolkata,Hyderabad,2026-08-22,11:00,13:15,4800,Economy,160,180\n"
        "CSV02,Akasa Air,Delhi,Bangalore,2026-08-23,17:00,19:40,5900,Business,20,30\n"
    )
    files = {"file": ("flights.csv", csv_content, "text/csv")}
    response = client.post(
        "/admin/flights/upload/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["imported"] == 2
    assert data["failed"] == 0
    assert len(data["errors"]) == 0


def test_admin_upload_csv_partial_failure():
    token = get_admin_token()
    csv_content = (
        "flight_id,airline,origin,destination,date,departure_time,arrival_time,price,travel_class,available_seats,total_seats\n"
        "GOOD01,Air India,Chennai,Delhi,2026-08-22,11:00,13:15,4800,Economy,160,180\n"
        "BAD01,Air India,Chennai,Delhi,2026-08-22,11:00,13:15,-500,Economy,160,180\n"
    )
    files = {"file": ("flights.csv", csv_content, "text/csv")}
    response = client.post(
        "/admin/flights/upload/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["imported"] == 1
    assert data["failed"] == 1
    assert data["errors"][0]["row"] == 2
    assert any("price" in e.lower() for e in data["errors"][0]["errors"])


def test_admin_upload_csv_empty_file():
    token = get_admin_token()
    files = {"file": ("flights.csv", b"", "text/csv")}
    response = client.post(
        "/admin/flights/upload/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_admin_upload_csv_wrong_extension():
    token = get_admin_token()
    files = {"file": ("flights.txt", b"some,text", "text/plain")}
    response = client.post(
        "/admin/flights/upload/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert ".csv files are accepted" in response.json()["detail"]


# ── 4. Endpoint Tests: POST /admin/flights/upload/excel ──────────────────────

def test_admin_upload_xlsx_success():
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([
        "flight_id", "airline", "origin", "destination", "date",
        "departure_time", "arrival_time", "price", "travel_class",
        "available_seats", "total_seats"
    ])
    ws.append([
        "XLSX01", "Air India", "Chennai", "Kochi", "2026-08-30",
        "07:00", "08:15", 3200, "Economy", 150, 180
    ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    token = get_admin_token()
    files = {"file": ("flights.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post(
        "/admin/flights/upload/excel",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1
    assert data["imported"] == 1
    assert data["failed"] == 0


def test_admin_upload_excel_wrong_extension():
    token = get_admin_token()
    files = {"file": ("flights.pdf", b"fake", "application/pdf")}
    response = client.post(
        "/admin/flights/upload/excel",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert ".xlsx or .xls" in response.json()["detail"]
