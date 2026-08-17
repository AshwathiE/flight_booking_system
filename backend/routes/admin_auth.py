from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

from backend.database.connection import SessionLocal
from backend.models.admin import Admin
from backend.models.user import User
from backend.models.flight import Flight
from backend.models.booking import Booking
from backend.schemas.auth import (
    AdminLoginRequest,
    TokenResponse,
    AdminResponse,
)
from backend.services.auth_service import (
    verify_password,
    create_access_token,
    get_current_admin,
)
from backend.services.flight_import_service import (
    import_flights_from_records,
    parse_csv_bytes,
    parse_excel_bytes,
    MAX_FILE_BYTES,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Authentication"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.email == request.email).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )

    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(user_id=admin.id, role="admin")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "admin",
        "admin": AdminResponse.model_validate(admin)
    }


@router.get("/me", response_model=AdminResponse)
def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    return current_admin


@router.get("/dashboard-stats")
def get_admin_dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_admins = db.query(Admin).count()
    total_flights = db.query(Flight).count()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_flights": total_flights,
        "system_status": "Healthy",
        "mcp_server": "Connected"
    }


@router.get("/bookings")
def get_all_bookings(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint. Returns all bookings sorted by created_at descending.
    Read-only – does not modify any booking or seat data.
    """
    bookings = (
        db.query(Booking)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "bookings": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "user_id": b.user_id,
                "flight_id": b.flight_id,
                "number_of_seats": b.number_of_seats,
                "total_price": b.total_price,
                "status": b.status,
                "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else None,
            }
            for b in bookings
        ],
    }


# =========================================================
# ADMIN FLIGHT MANAGEMENT ENDPOINTS
# =========================================================

# ── Pydantic schema for manual flight entry ───────────────

class ManualFlightCreate(BaseModel):
    """
    Schema for admin manual flight creation.
    Mirrors the Flight SQLAlchemy model fields exactly.
    Only fields that exist in the actual Flight model are included.
    """
    flight_id: str = Field(..., min_length=1, max_length=20,
                           description="Unique flight identifier, e.g. AI101")
    airline: str = Field(..., min_length=1, max_length=100)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    departure_time: str = Field(..., description="Time in HH:MM format")
    arrival_time: str = Field(..., description="Time in HH:MM format")
    price: float = Field(..., ge=0, description="Price per seat in INR")
    travel_class: str = Field(..., description="Economy, Business, or First")
    available_seats: int = Field(..., ge=0)
    total_seats: Optional[int] = Field(default=180, ge=0)

    @field_validator("flight_id")
    @classmethod
    def validate_flight_id_format(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9\-]{1,20}$", v):
            raise ValueError(
                "flight_id must be 1–20 alphanumeric characters or hyphens"
            )
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        from datetime import date as date_type
        try:
            date_type.fromisoformat(v)
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

    @field_validator("departure_time", "arrival_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        h, m = v.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Time has invalid hours or minutes")
        return v

    @field_validator("travel_class")
    @classmethod
    def validate_travel_class(cls, v: str) -> str:
        if v.lower() not in {"economy", "business", "first"}:
            raise ValueError("travel_class must be Economy, Business, or First")
        return v.capitalize()

    def validate_origin_destination(self) -> None:
        if self.origin.lower() == self.destination.lower():
            raise ValueError("origin and destination must not be the same")


# ── POST /admin/flights — manual single flight entry ─────

@router.post(
    "/flights",
    status_code=status.HTTP_201_CREATED,
    summary="Admin: manually add a single flight",
    tags=["Admin Flight Management"],
)
def admin_create_flight(
    payload: ManualFlightCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint.
    Accepts a single flight's data as JSON and inserts it into the
    existing 'flights' table after validation.
    """

    # Cross-field validation (Pydantic v2 model validators work differently;
    # we do it here to keep the pattern consistent with the rest of the project)
    if payload.origin.lower() == payload.destination.lower():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="origin and destination must not be the same",
        )

    # Duplicate check
    existing = db.query(Flight).filter(
        Flight.flight_id == payload.flight_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Flight with id '{payload.flight_id}' already exists",
        )

    from datetime import date as date_type

    try:
        flight = Flight(
            flight_id=payload.flight_id,
            airline=payload.airline,
            origin=payload.origin,
            destination=payload.destination,
            date=date_type.fromisoformat(payload.date),
            departure_time=payload.departure_time,
            arrival_time=payload.arrival_time,
            price=payload.price,
            travel_class=payload.travel_class,
            total_seats=payload.total_seats if payload.total_seats is not None else 180,
            available_seats=payload.available_seats,
        )
        db.add(flight)
        db.commit()
        db.refresh(flight)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flight: {str(exc)}",
        )

    return {
        "success": True,
        "message": f"Flight '{flight.flight_id}' created successfully",
        "flight_id": flight.flight_id,
    }


# ── POST /admin/flights/upload/csv ───────────────────────

@router.post(
    "/flights/upload/csv",
    summary="Admin: bulk-import flights from a CSV file",
    tags=["Admin Flight Management"],
)
async def admin_upload_csv(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint.
    Accepts a multipart CSV file upload.
    Validates file type, parses rows, validates each row,
    inserts valid rows into the existing 'flights' table,
    and returns an ImportSummary.
    """

    # ── File-type guard ──────────────────────────────────
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted for CSV upload",
        )

    content = await file.read()

    # ── Size guard ───────────────────────────────────────
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty",
        )
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the 10 MB limit ({len(content)} bytes received)",
        )

    # ── Parse ────────────────────────────────────────────
    records, parse_error = parse_csv_bytes(content)
    if parse_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parse_error,
        )

    # ── Import ───────────────────────────────────────────
    summary = import_flights_from_records(records, db)
    return summary.to_dict()


# ── POST /admin/flights/upload/excel ────────────────────

@router.post(
    "/flights/upload/excel",
    summary="Admin: bulk-import flights from an Excel file (.xlsx / .xls)",
    tags=["Admin Flight Management"],
)
async def admin_upload_excel(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint.
    Accepts a multipart .xlsx or .xls file upload.
    Validates file type, parses rows, validates each row,
    inserts valid rows into the existing 'flights' table,
    and returns an ImportSummary.
    """

    # ── File-type guard ──────────────────────────────────
    filename = file.filename or ""
    lower_fname = filename.lower()
    if not (lower_fname.endswith(".xlsx") or lower_fname.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx or .xls files are accepted for Excel upload",
        )

    content = await file.read()

    # ── Size guard ───────────────────────────────────────
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded Excel file is empty",
        )
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the 10 MB limit ({len(content)} bytes received)",
        )

    # ── Parse ────────────────────────────────────────────
    records, parse_error = parse_excel_bytes(content, filename)
    if parse_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parse_error,
        )

    # ── Import ───────────────────────────────────────────
    summary = import_flights_from_records(records, db)
    return summary.to_dict()
