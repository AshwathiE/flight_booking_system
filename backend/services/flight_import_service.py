"""
flight_import_service.py
------------------------
Handles validation and bulk-import of flight records submitted via:
  - CSV upload
  - Excel upload
  - Manual admin form

Reuses the existing Flight SQLAlchemy model and SessionLocal.
Does NOT create a new table, new DB connection, or duplicate the model.

Transaction strategy: partial import.
  - Each valid row is committed individually.
  - Invalid rows are skipped and reported in the ImportSummary.
  - This matches the existing booking_service pattern and gives the best admin UX.
"""

import re
from datetime import date as date_type
from typing import Any

from sqlalchemy.orm import Session

from backend.models.flight import Flight


# =========================================================
# CONSTANTS
# =========================================================

VALID_TRAVEL_CLASSES = {"economy", "business", "first"}

FLIGHT_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-]{1,20}$")
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

# Maximum file size allowed for uploads (10 MB)
MAX_FILE_BYTES = 10 * 1024 * 1024

# Required CSV / Excel column names (case-insensitive)
REQUIRED_COLUMNS = {
    "flight_id",
    "airline",
    "origin",
    "destination",
    "date",
    "departure_time",
    "arrival_time",
    "price",
    "travel_class",
    "available_seats",
}


# =========================================================
# RESULT TYPES
# =========================================================

class RowError:
    """Stores validation errors for a single row."""

    def __init__(self, row_number: int, errors: list[str]):
        self.row_number = row_number
        self.errors = errors

    def to_dict(self) -> dict:
        return {
            "row": self.row_number,
            "errors": self.errors,
        }


class ImportSummary:
    """Aggregate result returned to the caller / API response."""

    def __init__(self):
        self.total_rows: int = 0
        self.imported: int = 0
        self.failed: int = 0
        self.row_errors: list[RowError] = []

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "imported": self.imported,
            "failed": self.failed,
            "errors": [e.to_dict() for e in self.row_errors],
        }


# =========================================================
# VALIDATOR
# =========================================================

def _validate_row(row: dict[str, Any], row_number: int, db: Session) -> list[str]:
    """
    Validate a single flight data dict.

    Returns a list of human-readable error strings.
    An empty list means the row is valid.

    Validation rules:
      - All required fields must be present and non-empty.
      - flight_id: alphanumeric + hyphen, max 20 chars, must not already exist in DB.
      - airline: max 100 chars.
      - origin / destination: non-empty, must not be equal.
      - date: YYYY-MM-DD format, must be a real calendar date.
      - departure_time / arrival_time: HH:MM format.
      - price: numeric, >= 0.
      - travel_class: one of Economy / Business / First (case-insensitive).
      - available_seats: integer, >= 0.
      - total_seats: optional; if provided must be integer >= 0.
    """

    errors: list[str] = []

    # ── Normalise keys to lowercase strip
    r = {k.strip().lower(): (str(v).strip() if v is not None else "") for k, v in row.items()}

    # ── Check required columns present ──────────────────────────
    for col in REQUIRED_COLUMNS:
        if col not in r or r[col] == "":
            errors.append(f"Missing or empty required field: '{col}'")

    # If any required field is missing we cannot do further checks that depend
    # on those fields — return early to avoid confusing follow-on errors.
    if errors:
        return errors

    # ── flight_id ────────────────────────────────────────────────
    flight_id = r["flight_id"]
    if not FLIGHT_ID_PATTERN.match(flight_id):
        errors.append(
            "flight_id must be 1–20 alphanumeric characters or hyphens "
            f"(got: '{flight_id}')"
        )
    else:
        # Duplicate check against the existing flights table
        exists = db.query(Flight).filter(Flight.flight_id == flight_id).first()
        if exists:
            errors.append(f"Duplicate: flight_id '{flight_id}' already exists in the database")

    # ── airline ─────────────────────────────────────────────────
    if len(r["airline"]) > 100:
        errors.append("airline must not exceed 100 characters")

    # ── origin / destination ─────────────────────────────────────
    if r["origin"].lower() == r["destination"].lower():
        errors.append("origin and destination must not be the same")

    # ── date ─────────────────────────────────────────────────────
    try:
        date_type.fromisoformat(r["date"])
    except ValueError:
        errors.append(f"date must be in YYYY-MM-DD format (got: '{r['date']}')")

    # ── departure_time ───────────────────────────────────────────
    if not TIME_PATTERN.match(r["departure_time"]):
        errors.append(
            f"departure_time must be in HH:MM format (got: '{r['departure_time']}')"
        )
    else:
        h, m = r["departure_time"].split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            errors.append(f"departure_time has invalid hours/minutes: '{r['departure_time']}'")

    # ── arrival_time ─────────────────────────────────────────────
    if not TIME_PATTERN.match(r["arrival_time"]):
        errors.append(
            f"arrival_time must be in HH:MM format (got: '{r['arrival_time']}')"
        )
    else:
        h, m = r["arrival_time"].split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            errors.append(f"arrival_time has invalid hours/minutes: '{r['arrival_time']}'")

    # ── price ────────────────────────────────────────────────────
    try:
        price = float(r["price"])
        if price < 0:
            errors.append("price must be >= 0")
    except ValueError:
        errors.append(f"price must be a numeric value (got: '{r['price']}')")

    # ── travel_class ─────────────────────────────────────────────
    if r["travel_class"].lower() not in VALID_TRAVEL_CLASSES:
        errors.append(
            f"travel_class must be one of Economy, Business, First "
            f"(got: '{r['travel_class']}')"
        )

    # ── available_seats ──────────────────────────────────────────
    try:
        seats = int(r["available_seats"])
        if seats < 0:
            errors.append("available_seats must be >= 0")
    except ValueError:
        errors.append(
            f"available_seats must be an integer (got: '{r['available_seats']}')"
        )

    # ── total_seats (optional) ───────────────────────────────────
    if "total_seats" in r and r["total_seats"] != "":
        try:
            ts = int(r["total_seats"])
            if ts < 0:
                errors.append("total_seats must be >= 0")
        except ValueError:
            errors.append(
                f"total_seats must be an integer if provided (got: '{r['total_seats']}')"
            )

    return errors


# =========================================================
# IMPORT RUNNER
# =========================================================

def import_flights_from_records(
    records: list[dict[str, Any]],
    db: Session,
) -> ImportSummary:
    """
    Validate and import a list of flight data dicts into the existing
    'flights' table using the existing SQLAlchemy session.

    Each valid row is committed individually (partial-import strategy).
    Invalid rows are collected in the returned ImportSummary.

    Args:
        records:  List of dicts; keys should match Flight model field names.
        db:       Active SQLAlchemy session (from the route's Depends(get_db)).

    Returns:
        ImportSummary with totals and per-row error details.
    """

    summary = ImportSummary()
    summary.total_rows = len(records)

    for idx, record in enumerate(records, start=1):
        row_errors = _validate_row(record, idx, db)

        if row_errors:
            summary.failed += 1
            summary.row_errors.append(RowError(row_number=idx, errors=row_errors))
            continue

        # Normalise for insertion
        r = {k.strip().lower(): (str(v).strip() if v is not None else "") for k, v in record.items()}

        # Capitalise travel_class consistently (e.g. "economy" → "Economy")
        travel_class_value = r["travel_class"].capitalize()

        total_seats_value = 180  # default
        if "total_seats" in r and r["total_seats"] != "":
            try:
                total_seats_value = int(r["total_seats"])
            except ValueError:
                total_seats_value = 180

        try:
            flight = Flight(
                flight_id=r["flight_id"],
                airline=r["airline"],
                origin=r["origin"],
                destination=r["destination"],
                date=date_type.fromisoformat(r["date"]),
                departure_time=r["departure_time"],
                arrival_time=r["arrival_time"],
                price=float(r["price"]),
                travel_class=travel_class_value,
                total_seats=total_seats_value,
                available_seats=int(r["available_seats"]),
            )
            db.add(flight)
            db.commit()
            summary.imported += 1

        except Exception as exc:
            db.rollback()
            summary.failed += 1
            summary.row_errors.append(
                RowError(
                    row_number=idx,
                    errors=[f"Database error: {str(exc)}"],
                )
            )

    return summary


# =========================================================
# CSV PARSER
# =========================================================

def parse_csv_bytes(content: bytes) -> tuple[list[dict], str | None]:
    """Parse and validate a CSV file."""

    import csv
    import io

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], "CSV file is not valid UTF-8 text"

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        return [], "CSV file appears to be empty or has no header row"

    # Normalize headers
    headers = [
        h.strip().lower() if h else ""
        for h in reader.fieldnames
    ]

    missing = REQUIRED_COLUMNS - set(headers)

    if missing:
        return [], (
            "CSV is missing required columns: "
            + ", ".join(sorted(missing))
        )

    records = []

    for row in reader:
        # Normalize every key
        normalized_row = {
            k.strip().lower(): (
                str(v).strip() if v is not None else ""
            )
            for k, v in row.items()
            if k is not None
        }

        # Skip completely empty rows
        if not any(normalized_row.values()):
            continue

        records.append(normalized_row)

    if not records:
        return [], "CSV file contains a header but no data rows"

    return records, None

# =========================================================
# EXCEL PARSER
# =========================================================

def parse_excel_bytes(content: bytes, filename: str) -> tuple[list[dict], str | None]:
    """
    Parse raw Excel bytes (.xlsx or .xls) into a list of dicts.

    Returns:
        (records, error_message)
    """
    import io

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "xlsx":
        return _parse_xlsx(content)
    elif ext == "xls":
        return _parse_xls(content)
    else:
        return [], f"Unsupported Excel format: '.{ext}'. Use .xlsx or .xls"


def _parse_xlsx(content: bytes) -> tuple[list[dict], str | None]:
    import io
    try:
        import openpyxl
    except ImportError:
        return [], "openpyxl is not installed. Run: pip install openpyxl"

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        return [], f"Cannot read .xlsx file: {e}"

    if not rows:
        return [], "Excel file is empty"

    headers = [str(h).strip().lower() if h is not None else "" for h in rows[0]]

    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        return [], f"Excel is missing required columns: {', '.join(sorted(missing))}"

    records = []
    for row in rows[1:]:
        # Skip entirely empty rows
        if all(v is None or str(v).strip() == "" for v in row):
            continue
        record = {headers[i]: (str(row[i]).strip() if row[i] is not None else "") for i in range(len(headers))}
        records.append(record)

    if not records:
        return [], "Excel file contains a header but no data rows"

    return records, None


def _parse_xls(content: bytes) -> tuple[list[dict], str | None]:
    import io
    try:
        import xlrd
    except ImportError:
        return [], "xlrd is not installed. Run: pip install xlrd"

    try:
        wb = xlrd.open_workbook(file_contents=content)
        ws = wb.sheet_by_index(0)
    except Exception as e:
        return [], f"Cannot read .xls file: {e}"

    if ws.nrows == 0:
        return [], "Excel (.xls) file is empty"

    headers = [str(ws.cell_value(0, c)).strip().lower() for c in range(ws.ncols)]

    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        return [], f"Excel (.xls) is missing required columns: {', '.join(sorted(missing))}"

    records = []
    for r_idx in range(1, ws.nrows):
        row_values = [ws.cell_value(r_idx, c) for c in range(ws.ncols)]
        if all(str(v).strip() == "" for v in row_values):
            continue
        record = {headers[i]: str(row_values[i]).strip() for i in range(len(headers))}
        records.append(record)

    if not records:
        return [], "Excel (.xls) file contains a header but no data rows"

    return records, None
