from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import json

from backend.mcp_client import (
    search_flights_mcp,
    get_flight_details_mcp,
    check_availability_mcp,
    get_fare_mcp
)

from agent.flight_agent import search_flights_with_agent


router = APIRouter(
    prefix="/flights",
    tags=["Flights"]
)


# =========================================================
# REQUEST MODELS
# =========================================================

class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)
    date: str
    total_seats: int = Field(default=1, ge=1)
    travel_class: str = "Economy"
    max_price: float | None = None


class AIFlightSearchRequest(BaseModel):
    message: str


# =========================================================
# RESPONSE MODELS
# =========================================================

class Flight(BaseModel):
    flight_id: str
    airline: str
    origin: str
    destination: str
    date: str
    departure_time: str
    arrival_time: str
    price: float
    travel_class: str
    available_seats: int


class FlightSearchResponse(BaseModel):
    flights: List[Flight]


# =========================================================
# NORMAL FLIGHT SEARCH
# =========================================================

@router.post(
    "/search",
    response_model=FlightSearchResponse
)
async def search_flights(
    request: FlightSearchRequest
):

    result = await search_flights_mcp(
        origin=request.origin,
        destination=request.destination,
        date=request.date,
        total_seats=request.total_seats,
        travel_class=request.travel_class,
        max_price=request.max_price,
    )

    flights = []

    for content in getattr(result, "content", []):

        if (
            hasattr(content, "text")
            and content.text
            and content.text.strip()
        ):
            try:
                data = json.loads(content.text)

                if isinstance(data, list):
                    flights.extend(data)

                elif isinstance(data, dict):
                    flights.append(data)

            except json.JSONDecodeError:
                continue

    return {
        "flights": flights
    }


# =========================================================
# FLIGHT DETAILS
# =========================================================

@router.get(
    "/{flight_id}",
    response_model=Flight
)
async def get_flight_details(
    flight_id: str
):

    result = await get_flight_details_mcp(
        flight_id
    )

    flights = []

    for content in getattr(result, "content", []):

        if (
            hasattr(content, "text")
            and content.text
            and content.text.strip()
        ):
            try:
                data = json.loads(content.text)

                if isinstance(data, list):
                    flights.extend(data)

                elif isinstance(data, dict):
                    flights.append(data)

            except json.JSONDecodeError:
                continue

    if not flights or (
        isinstance(flights[0], dict)
        and "error" in flights[0]
    ):

        detail = (
            flights[0].get(
                "error",
                "Flight details not found"
            )
            if flights
            and isinstance(flights[0], dict)
            else "Flight details not found"
        )

        raise HTTPException(
            status_code=404,
            detail=detail
        )

    return flights[0]


# =========================================================
# AVAILABILITY
# =========================================================

@router.get(
    "/{flight_id}/availability"
)
async def check_flight_availability(
    flight_id: str,
    total_seats: int = 1
):

    result = await check_availability_mcp(
        flight_id=flight_id,
        total_seats=total_seats
    )

    for content in getattr(result, "content", []):

        if (
            hasattr(content, "text")
            and content.text
            and content.text.strip()
        ):
            try:
                return json.loads(content.text)

            except json.JSONDecodeError:
                continue

    return {
        "error": "No availability information returned"
    }


# =========================================================
# FARE
# =========================================================

@router.get(
    "/{flight_id}/fare"
)
async def get_flight_fare(
    flight_id: str,
    total_seats: int = 1,
    travel_class: str = "Economy"
):

    result = await get_fare_mcp(
        flight_id=flight_id,
        total_seats=total_seats,
        travel_class=travel_class
    )

    for content in getattr(result, "content", []):

        if (
            hasattr(content, "text")
            and content.text
            and content.text.strip()
        ):
            try:
                return json.loads(content.text)

            except json.JSONDecodeError:
                continue

    return {
        "error": "No fare information returned"
    }


# =========================================================
# AI FLIGHT SEARCH
# =========================================================

@router.post("/ai/search")
async def ai_search_flights(
    request: AIFlightSearchRequest
):
    result = await search_flights_with_agent(
        request.message
    )

    return result