from mcp.server import MCPServer

from backend.database.connection import SessionLocal
from backend.services.payment_service import PaymentService


# =========================================================
# CREATE PAYMENT MCP SERVER
# =========================================================

mcp = MCPServer(
    "Payment MCP Server",
    instructions=(
        "MCP server providing complete payment creation, "
        "processing, verification, retrieval, and refunds."
    )
)


# =========================================================
# TOOL 1: CREATE PAYMENT
# =========================================================

@mcp.tool()
def create_payment(
    booking_id: int,
    user_id: int,
    payment_method: str = "MOCK"
) -> dict:
    """
    Create a pending payment for a booking.

    The payment amount is obtained securely from the
    booking's total_price in the database.
    """

    db = SessionLocal()

    try:
        return PaymentService.create_payment(
            db=db,
            booking_id=booking_id,
            user_id=user_id,
            payment_method=payment_method
        )

    finally:
        db.close()


# =========================================================
# TOOL 2: PROCESS PAYMENT
# =========================================================

@mcp.tool()
def process_payment(
    payment_id: str,
    user_id: int,
    success: bool = True
) -> dict:
    """
    Process a pending payment using the mock payment gateway.

    success=True  -> payment succeeds
    success=False -> payment fails
    """

    db = SessionLocal()

    try:
        return PaymentService.process_payment(
            db=db,
            payment_id=payment_id,
            user_id=user_id,
            success=success
        )

    finally:
        db.close()


# =========================================================
# TOOL 3: VERIFY PAYMENT
# =========================================================

@mcp.tool()
def verify_payment(
    payment_id: str,
    user_id: int
) -> dict:
    """
    Verify and retrieve the current status of a payment.
    """

    db = SessionLocal()

    try:
        return PaymentService.get_payment(
            db=db,
            payment_id=payment_id,
            user_id=user_id
        )

    finally:
        db.close()


# =========================================================
# TOOL 4: GET PAYMENT
# =========================================================

@mcp.tool()
def get_payment(
    payment_id: str,
    user_id: int
) -> dict:
    """
    Retrieve details of a specific payment.
    Checks user authorization.
    """

    db = SessionLocal()

    try:
        return PaymentService.get_payment(
            db=db,
            payment_id=payment_id,
            user_id=user_id
        )

    finally:
        db.close()


# =========================================================
# TOOL 5: GET PAYMENT BY BOOKING
# =========================================================

@mcp.tool()
def get_payment_by_booking(
    booking_id: int,
    user_id: int
) -> dict:
    """
    Retrieve the payment corresponding to a booking.
    Checks user authorization.
    """

    db = SessionLocal()

    try:
        return PaymentService.get_booking_payment(
            db=db,
            booking_id=booking_id,
            user_id=user_id
        )

    finally:
        db.close()


# =========================================================
# TOOL 6: REFUND PAYMENT
# =========================================================

@mcp.tool()
def refund_payment(
    payment_id: str,
    user_id: int
) -> dict:
    """
    Refund a successful payment and cancel the
    corresponding booking.
    """

    db = SessionLocal()

    try:
        return PaymentService.refund_payment(
            db=db,
            payment_id=payment_id,
            user_id=user_id
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
        port=8003,
        streamable_http_path="/mcp"
    )