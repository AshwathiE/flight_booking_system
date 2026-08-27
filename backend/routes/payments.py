import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.mcp_client import (
    create_payment_mcp,
    process_payment_mcp,
    verify_payment_mcp,
    get_payment_mcp,
    get_payment_by_booking_mcp,
    refund_payment_mcp,
)

# Router for /payments
router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# Router for /bookings/.../payment
bookings_payment_router = APIRouter(
    prefix="/bookings",
    tags=["Payments"]
)


def parse_mcp_response(mcp_result) -> dict:
    """Helper to parse TextContent JSON returned from MCP client session."""
    for content in getattr(mcp_result, "content", []):
        if hasattr(content, "text") and content.text and content.text.strip():
            try:
                data = json.loads(content.text)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
    return {"success": False, "error": "INVALID_RESPONSE", "message": "Failed to parse MCP response"}


# Request Schemas
class CreatePaymentRequest(BaseModel):
    booking_id: int
    payment_method: str = "CARD"
    currency: str = "INR"


class ProcessPaymentRequest(BaseModel):
    payment_method: str | None = None
    success: bool = True


class RefundPaymentRequest(BaseModel):
    reason: str


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_payment_endpoint(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a pending payment for a booking."""
    mcp_result = await create_payment_mcp(
        booking_id=request.booking_id,
        user_id=current_user.id,
        payment_method=request.payment_method,
    )
    result = parse_mcp_response(mcp_result)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    return result


@router.post("/{payment_id}/process")
async def process_payment_endpoint(
    payment_id: str,
    request: ProcessPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Process a pending payment through the mock gateway."""

    # --------------------------------------------------
    # 1. Verify payment belongs to current user
    # --------------------------------------------------

    verify_auth = await get_payment_mcp(
        payment_id=payment_id,
        user_id=current_user.id
    )

    auth_res = parse_mcp_response(verify_auth)

    if not auth_res.get("success"):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
                if auth_res.get("error") == "UNAUTHORIZED"
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=auth_res
        )

    # --------------------------------------------------
    # 2. Make sure payment is still processable
    # --------------------------------------------------

    if auth_res.get("status") == "SUCCESS":
        return auth_res

    if auth_res.get("status") == "REFUNDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "PAYMENT_REFUNDED",
                "message": "This payment has already been refunded."
            }
        )

    # --------------------------------------------------
    # 3. Process through Payment MCP
    # --------------------------------------------------

    mcp_result = await process_payment_mcp(
        payment_id=payment_id,
        user_id=current_user.id,
        success=True
    )

    result = parse_mcp_response(mcp_result)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    return result


@router.get("/{payment_id}")
async def get_payment_endpoint(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific payment by ID."""
    mcp_result = await get_payment_mcp(
        payment_id=payment_id,
        user_id=current_user.id
    )
    result = parse_mcp_response(mcp_result)
    if not result.get("success"):
        status_code = status.HTTP_403_FORBIDDEN if result.get("error") == "UNAUTHORIZED" else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=result
        )
    return result


@bookings_payment_router.get("/{booking_id}/payment")
async def get_payment_by_booking_endpoint(
    booking_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get payment belonging to a booking."""
    mcp_result = await get_payment_by_booking_mcp(
        booking_id=booking_id,
        user_id=current_user.id
    )
    result = parse_mcp_response(mcp_result)
    if not result.get("success"):
        status_code = status.HTTP_403_FORBIDDEN if result.get("error") == "UNAUTHORIZED" else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=result
        )
    return result


@router.post("/{payment_id}/verify")
async def verify_payment_endpoint(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Verify payment status."""
    # 1. Verify user is authorized to view/verify this payment
    verify_auth = await get_payment_mcp(payment_id=payment_id, user_id=current_user.id)
    auth_res = parse_mcp_response(verify_auth)
    if not auth_res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if auth_res.get("error") == "UNAUTHORIZED" else status.HTTP_400_BAD_REQUEST,
            detail=auth_res
        )

    mcp_result = await verify_payment_mcp(payment_id=payment_id, user_id=current_user.id)
    result = parse_mcp_response(mcp_result)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    return result


@router.post("/{payment_id}/refund")
async def refund_payment_endpoint(
    payment_id: str,
    request: RefundPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Refund a payment."""
    mcp_result = await refund_payment_mcp(
        payment_id=payment_id,
        user_id=current_user.id
    )
    result = parse_mcp_response(mcp_result)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    return result
