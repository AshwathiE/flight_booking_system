from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import json

from fastapi.middleware.cors import CORSMiddleware

from backend.mcp_client import (
    search_flights_mcp,
    get_flight_details_mcp,
    check_availability_mcp,
    get_fare_mcp,
)

from agent.flight_agent import search_flights_with_agent
from backend.routes.user_auth import router as user_auth_router
from backend.routes.admin_auth import router as admin_auth_router


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Flight Booking API",
    description="Flight Booking API with MCP and AI Agent",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AUTH ROUTERS
# =========================================================

app.include_router(user_auth_router)
app.include_router(admin_auth_router)


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
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Flight Booking API is running"
    }


# =========================================================
# FLIGHT SEARCH
# =========================================================

@app.post(
    "/search_flights",
    response_model=FlightSearchResponse
)
async def search_flights(request: FlightSearchRequest):

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

@app.get(
    "/flights/{flight_id}",
    response_model=Flight
)
async def get_flight_details(flight_id: str):

    result = await get_flight_details_mcp(flight_id)

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
# FLIGHT AVAILABILITY
# =========================================================

@app.get(
    "/flights/{flight_id}/availability"
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
# FLIGHT FARE
# =========================================================

@app.get(
    "/flights/{flight_id}/fare"
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

@app.post("/ai/search_flights")
async def ai_search_flights(
    request: AIFlightSearchRequest
):
    """
    AI-powered flight search endpoint.

    Returns:
    - message
    - flights
    - recommended_flight
    - recommendation_reason
    - preference
    """

    result = await search_flights_with_agent(
        request.message
    )

    return result