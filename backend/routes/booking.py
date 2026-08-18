import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field
from backend.models.user import User
from backend.models.booking import Booking
from backend.models.flight import Flight
from backend.database.connection import SessionLocal
from backend.services.auth_service import get_current_user
from backend.utils.pdf_generator import generate_ticket_pdf
from backend.mcp_client import (
    create_booking_mcp,
    get_booking_mcp,
    get_user_bookings_mcp,
    cancel_booking_mcp,
    change_booking_mcp,
)

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
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
class CreateBookingRequest(BaseModel):
    flight_id: str
    number_of_seats: int = Field(default=1, ge=1)


class ChangeBookingRequest(BaseModel):
    new_flight_id: str
    new_number_of_seats: int = Field(default=1, ge=1)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    request: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a flight booking for the authenticated user.
    """
    mcp_result = await create_booking_mcp(
        user_id=current_user.id,
        flight_id=request.flight_id,
        number_of_seats=request.number_of_seats
    )
    
    result = parse_mcp_response(mcp_result)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
        
    return result


@router.get("/my-bookings")
async def get_my_bookings_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    Get all bookings for the currently logged in user.
    """
    mcp_result = await get_user_bookings_mcp(user_id=current_user.id)
    result = parse_mcp_response(mcp_result)
    return result


@router.get("/{booking_id}")
async def get_booking_endpoint(
    booking_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get specific booking by ID. Verifies user ownership.
    """
    mcp_result = await get_booking_mcp(
        booking_id=booking_id,
        user_id=current_user.id
    )
    
    result = parse_mcp_response(mcp_result)
    
    if not result.get("success"):
        error_code = result.get("error")
        status_code = status.HTTP_404_NOT_FOUND if error_code == "BOOKING_NOT_FOUND" else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=result)
        
    return result


@router.post("/{booking_id}/cancel")
async def cancel_booking_endpoint(
    booking_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an existing booking belonging to the authenticated user.
    """
    mcp_result = await cancel_booking_mcp(
        booking_id=booking_id,
        user_id=current_user.id
    )
    
    result = parse_mcp_response(mcp_result)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
        
    return result


@router.put("/{booking_id}/change")
async def change_booking_endpoint(
    booking_id: int,
    request: ChangeBookingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Change booking to a new flight or new seat count.
    """
    mcp_result = await change_booking_mcp(
        booking_id=booking_id,
        user_id=current_user.id,
        new_flight_id=request.new_flight_id,
        new_number_of_seats=request.new_number_of_seats
    )
    
    result = parse_mcp_response(mcp_result)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
        
    return result


@router.get("/{booking_id}/ticket/pdf")
async def get_booking_ticket_pdf(
    booking_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Generate and stream flight ticket PDF for the logged-in user.
    """
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
            
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this booking"
            )
            
        flight = db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight details not found for this booking"
            )
            
        pdf_bytes = generate_ticket_pdf(booking, flight, current_user)
        
        headers = {
            'Content-Disposition': f'attachment; filename="ticket_{booking.booking_reference}.pdf"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    finally:
        db.close()
