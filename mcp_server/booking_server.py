from mcp.server import MCPServer
from backend.database.connection import SessionLocal
from backend.services.booking_service import BookingService


# =========================================================
# CREATE BOOKING MCP SERVER
# =========================================================

mcp = MCPServer(
    "Booking MCP Server",
    instructions="MCP server providing complete flight booking creation, retrieval, cancellation, and modification tools."
)


# =========================================================
# TOOL 1: CREATE BOOKING
# =========================================================

@mcp.tool()
def create_booking(
    user_id: int,
    flight_id: str,
    number_of_seats: int = 1
) -> dict:
    """
    Create a new flight booking for a user.
    Validates user, flight, availability, calculates total price,
    creates booking record, and deducts available seats.
    """
    db = SessionLocal()
    try:
        return BookingService.create_booking(
            db=db,
            user_id=user_id,
            flight_id=flight_id,
            number_of_seats=number_of_seats
        )
    finally:
        db.close()


# =========================================================
# TOOL 2: GET BOOKING
# =========================================================

@mcp.tool()
def get_booking(
    booking_id: int,
    user_id: int | None = None
) -> dict:
    """
    Retrieve details of a specific booking by ID.
    Optionally checks if the user is authorized to view the booking.
    """
    db = SessionLocal()
    try:
        return BookingService.get_booking(
            db=db,
            booking_id=booking_id,
            requesting_user_id=user_id
        )
    finally:
        db.close()


# =========================================================
# TOOL 3: GET USER BOOKINGS
# =========================================================

@mcp.tool()
def get_user_bookings(
    user_id: int
) -> dict:
    """
    Get all bookings belonging to a specific user.
    """
    db = SessionLocal()
    try:
        return BookingService.get_user_bookings(
            db=db,
            user_id=user_id
        )
    finally:
        db.close()


# =========================================================
# TOOL 4: CANCEL BOOKING
# =========================================================

@mcp.tool()
def cancel_booking(
    booking_id: int,
    user_id: int
) -> dict:
    """
    Cancel an existing booking and restore seats to the flight.
    Does not delete the booking record; updates status to CANCELLED.
    """
    db = SessionLocal()
    try:
        return BookingService.cancel_booking(
            db=db,
            booking_id=booking_id,
            user_id=user_id
        )
    finally:
        db.close()


# =========================================================
# TOOL 5: CHANGE BOOKING
# =========================================================

@mcp.tool()
def change_booking(
    booking_id: int,
    user_id: int,
    new_flight_id: str,
    new_number_of_seats: int
) -> dict:
    """
    Change an existing booking to a new flight and/or new seat count.
    Releases seats from old flight and reserves seats on new flight atomically.
    """
    db = SessionLocal()
    try:
        return BookingService.change_booking(
            db=db,
            booking_id=booking_id,
            user_id=user_id,
            new_flight_id=new_flight_id,
            new_number_of_seats=new_number_of_seats
        )
    finally:
        db.close()


# =========================================================
# START MCP SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002,
        streamable_http_path="/mcp"
    )
