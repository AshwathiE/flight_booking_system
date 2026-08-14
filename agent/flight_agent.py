import os
import json
import logging
from datetime import datetime
from typing import Optional, Literal

from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.mcp_client import (
    search_flights_mcp,
    check_availability_mcp,
    get_fare_mcp,
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_YEAR = 2026

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured. "
        "Please add GROQ_API_KEY to your .env file."
    )

client = AsyncGroq(
    api_key=GROQ_API_KEY
)

LLM_MODEL = "llama-3.3-70b-versatile"


# ============================================================
# PYDANTIC MODEL
# LLM OUTPUT SCHEMA
# ============================================================

class FlightSearchRequest(BaseModel):
    """
    Structured flight search parameters extracted by the LLM.
    """

    origin: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    destination: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    total_seats: int = Field(
        default=1,
        ge=1,
    )

    travel_class: Optional[
        Literal[
            "economy",
            "premium economy",
            "business",
            "first class"
        ]
    ] = None

    max_price: Optional[float] = Field(
        default=None,
        gt=0
    )

    preference: Literal[
        "cheapest",
        "earliest",
        "fastest",
        "automatic"
    ] = "automatic"

    @field_validator("origin", "destination")
    @classmethod
    def validate_city(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "City cannot be empty."
            )

        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:

        try:
            datetime.strptime(
                value,
                "%Y-%m-%d"
            )

        except ValueError:
            raise ValueError(
                "Date must be valid YYYY-MM-DD."
            )

        return value

    @field_validator("travel_class", mode="before")
    @classmethod
    def normalize_travel_class(cls, value):
        if value is None:
            return None

        return str(value).strip().lower()


# ============================================================
# LLM SYSTEM PROMPT
# ============================================================

REQUEST_SYSTEM_PROMPT = f"""
You are a flight search parameter extraction assistant.

Extract ONLY the flight search information from the user's request.

Return JSON only.

Required fields:

{{
    "origin": "string",
    "destination": "string",
    "date": "YYYY-MM-DD",
    "total_seats": 1,
    "travel_class": null,
    "max_price": null,
    "preference": "automatic"
}}

Rules:

1. origin
Extract the departure city.

2. destination
Extract the arrival city.

3. date
Convert the user's date to YYYY-MM-DD.

If the year is not provided, use {PROJECT_YEAR}.

If no date is provided, use:
{PROJECT_YEAR}-08-15

4. total_seats
Number of passengers.

If not specified, use 1.

5. travel_class

Allowed values:

- economy
- premium economy
- business
- first class

If not specified, use null.

6. max_price

If the user specifies a maximum price,
return the numeric value.

Otherwise use null.

7. preference

cheapest:
- cheapest
- lowest price
- lowest fare
- cheapest flight
- budget
- affordable

earliest:
- earliest
- first flight
- early morning
- first available

fastest:
- fastest
- quickest
- shortest
- least travel time

automatic:
- if no preference is specified

Do not invent information.
"""


# ============================================================
# UTILITY FUNCTION 1
# PARSE LLM JSON
# ============================================================

def parse_json_response(text: str) -> dict:
    """
    Safely parse the JSON returned by the LLM.

    Handles:
    - normal JSON
    - ```json fenced JSON
    - ``` fenced JSON
    """

    if not text or not text.strip():
        raise ValueError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown code fences if present
    # --------------------------------------------------------

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        data = json.loads(text)

    except json.JSONDecodeError as exc:

        logger.error(
            "Invalid JSON from LLM: %s",
            text
        )

        raise ValueError(
            "LLM returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):

        raise ValueError(
            "LLM response must be a JSON object."
        )

    return data


# ============================================================
# UTILITY FUNCTION 2
# NORMALIZE CITY
# ============================================================

def normalize_city(city: str) -> str:
    """
    Normalize city names before sending them to MCP.
    """

    return " ".join(
        city.strip().split()
    )


# ============================================================
# UTILITY FUNCTION 3
# VALIDATE BUSINESS INPUT
# ============================================================

def validate_search_request(
    request: FlightSearchRequest
) -> None:
    """
    Application-level validation.

    This is separate from Pydantic schema validation.
    """

    if (
        request.origin.lower()
        == request.destination.lower()
    ):
        raise ValueError(
            "Origin and destination cannot be the same."
        )

    search_date = datetime.strptime(
        request.date,
        "%Y-%m-%d"
    )

    if search_date.year < PROJECT_YEAR:
        raise ValueError(
            "Flight search date cannot be in the past."
        )


# ============================================================
# UTILITY FUNCTION 4
# PARSE MCP RESULT
# ============================================================

def parse_mcp_result(result) -> list:
    """
    Convert MCP TextContent JSON into Python objects.
    """

    data = []

    for content in getattr(
        result,
        "content",
        []
    ):

        if not hasattr(
            content,
            "text"
        ):
            continue

        text = content.text

        if not text or not text.strip():
            continue

        try:

            parsed = json.loads(
                text
            )

        except json.JSONDecodeError as exc:

            logger.error(
                "Invalid JSON received from MCP: %s",
                text
            )

            raise ValueError(
                "MCP returned invalid JSON."
            ) from exc

        if isinstance(
            parsed,
            list
        ):
            data.extend(parsed)

        elif isinstance(
            parsed,
            dict
        ):
            data.append(parsed)

        else:

            logger.warning(
                "Unexpected MCP result type: %s",
                type(parsed).__name__
            )

    return data


# ============================================================
# UTILITY FUNCTION 5
# PARSE TIME
# ============================================================

def parse_time(time_str: Optional[str]):
    """
    Convert HH:MM or HH:MM:SS into datetime.
    """

    if not time_str:
        return None

    for fmt in (
        "%H:%M:%S",
        "%H:%M"
    ):

        try:

            return datetime.strptime(
                time_str.strip(),
                fmt
            )

        except ValueError:
            continue

    return None


# ============================================================
# UTILITY FUNCTION 6
# FLIGHT DURATION
# ============================================================

def flight_duration_minutes(
    departure_time: str,
    arrival_time: str
) -> int:
    """
    Calculate flight duration.

    Handles overnight flights.
    """

    departure = parse_time(
        departure_time
    )

    arrival = parse_time(
        arrival_time
    )

    if departure is None or arrival is None:
        return 999999

    duration = (
        arrival - departure
    ).total_seconds() / 60

    if duration < 0:
        duration += 24 * 60

    return int(duration)


# ============================================================
# STEP 1
# LLM UNDERSTANDS USER REQUEST
# ============================================================

async def understand_flight_request(
    user_request: str
) -> FlightSearchRequest:

    if not user_request or not user_request.strip():

        raise ValueError(
            "Flight search request cannot be empty."
        )

    if len(user_request) > 1000:

        raise ValueError(
            "Flight search request is too long."
        )

    user_request = user_request.strip().lower()

    logger.info(
        "Sending flight request to LLM."
    )

    try:

        response = await client.chat.completions.create(

            model=LLM_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": REQUEST_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_request.strip()
                }
            ],

            temperature=0,

            response_format={
                "type": "json_object"
            }
        )

    except Exception as exc:

        logger.exception(
            "LLM request failed."
        )

        raise RuntimeError(
            "Unable to understand flight request."
        ) from exc

    content = (
        response
        .choices[0]
        .message
        .content
    )

    raw_data = parse_json_response(
        content
    )

    # --------------------------------------------------------
    # PYDANTIC VALIDATION
    # --------------------------------------------------------

    try:

        request_data = FlightSearchRequest(
            **raw_data
        )

    except ValidationError as exc:

        logger.error(
            "LLM output failed Pydantic validation: %s",
            exc
        )

        raise ValueError(
            "The flight search information extracted "
            "from the request is invalid."
        ) from exc

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    request_data.origin = normalize_city(
        request_data.origin
    )

    request_data.destination = normalize_city(
        request_data.destination
    )

    # --------------------------------------------------------
    # BUSINESS VALIDATION
    # --------------------------------------------------------

    validate_search_request(
        request_data
    )

    logger.info(
        "Validated search request: %s",
        request_data.model_dump()
    )

    return request_data


# ============================================================
# STEP 2
# CALL MCP SEARCH TOOL
# ============================================================

async def fetch_flights_from_mcp(
    request_data: FlightSearchRequest
) -> list:

    logger.info(
        "Calling search_flights MCP."
    )

    try:

        result = await search_flights_mcp(

            origin=request_data.origin,

            destination=request_data.destination,

            date=request_data.date,

            total_seats=request_data.total_seats,

            travel_class=request_data.travel_class,

            max_price=request_data.max_price
        )

    except Exception as exc:

        logger.exception(
            "MCP flight search failed."
        )

        raise RuntimeError(
            "Flight search service is currently unavailable."
        ) from exc

    flights = parse_mcp_result(
        result
    )

    logger.info(
        "MCP returned %d flights.",
        len(flights)
    )

    return flights


# ============================================================
# STEP 3
# CHECK AVAILABILITY
# ============================================================

async def check_flight_availability(
    flights: list,
    total_seats: int
) -> list:

    available_flights = []

    for flight in flights:

        flight_id = flight.get(
            "flight_id"
        )

        if not flight_id:

            logger.warning(
                "Skipping flight without flight_id."
            )

            continue

        try:

            result = await check_availability_mcp(

                flight_id=flight_id,

                total_seats=total_seats
            )

            availability_data = parse_mcp_result(
                result
            )

        except Exception as exc:

            logger.exception(
                "Availability MCP failed for %s.",
                flight_id
            )

            # IMPORTANT:
            # We do not silently pretend the flight
            # is unavailable.
            #
            # We fail the operation because the
            # availability information is required.

            raise RuntimeError(
                f"Unable to verify availability for flight "
                f"{flight_id}."
            ) from exc

        if not availability_data:

            raise RuntimeError(
                f"No availability information returned "
                f"for flight {flight_id}."
            )

        availability = availability_data[0]

        available_seats = availability.get(
            "available_seats"
        )

        if available_seats is None:

            raise RuntimeError(
                f"Invalid availability response "
                f"for flight {flight_id}."
            )

        try:

            available_seats = int(
                available_seats
            )

        except (
            TypeError,
            ValueError
        ):

            raise RuntimeError(
                f"Invalid seat count returned "
                f"for flight {flight_id}."
            )

        if available_seats < total_seats:

            logger.info(
                "Flight %s does not have enough seats.",
                flight_id
            )

            continue

        flight["available_seats"] = (
            available_seats
        )

        flight["requested_seats"] = (
            total_seats
        )

        flight["availability"] = (
            "Available"
        )

        available_flights.append(
            flight
        )

    return available_flights


# ============================================================
# STEP 4
# GET FARES
# ============================================================

async def fetch_fares(
    flights: list,
    request_data: FlightSearchRequest
) -> list:

    final_flights = []

    for flight in flights:

        flight_id = flight.get(
            "flight_id"
        )

        if not flight_id:
            continue

        # ----------------------------------------------------
        # IMPORTANT TRAVEL CLASS LOGIC
        # ----------------------------------------------------

        requested_class = (
            request_data.travel_class
        )

        database_class = flight.get(
            "travel_class"
        )

        # User explicitly requested a class.
        # We must use that class.
        if requested_class:

            fare_class = requested_class

        # User did not specify a class.
        # Use the class returned by the database.
        elif database_class:

            fare_class = database_class

        else:

            logger.warning(
                "No travel class available for %s.",
                flight_id
            )

            continue

        try:

            result = await get_fare_mcp(

                flight_id=flight_id,

                total_seats=request_data.total_seats,

                travel_class=fare_class
            )

            fare_data = parse_mcp_result(
                result
            )

        except Exception as exc:

            logger.exception(
                "Fare MCP failed for %s.",
                flight_id
            )

            raise RuntimeError(
                f"Unable to calculate fare for flight "
                f"{flight_id}."
            ) from exc

        if not fare_data:

            raise RuntimeError(
                f"No fare information returned "
                f"for flight {flight_id}."
            )

        fare = fare_data[0]

        total_fare = fare.get(
            "total_fare"
        )

        if total_fare is None:

            raise RuntimeError(
                f"Invalid fare information "
                f"for flight {flight_id}."
            )

        try:

            total_fare = float(
                total_fare
            )

        except (
            TypeError,
            ValueError
        ):

            raise RuntimeError(
                f"Invalid total fare for flight "
                f"{flight_id}."
            )

        if total_fare < 0:

            raise RuntimeError(
                f"Invalid negative fare for flight "
                f"{flight_id}."
            )

        fare["total_fare"] = (
            total_fare
        )

        flight["fare"] = fare

        flight["travel_class"] = (
            fare_class
        )

        final_flights.append(
            flight
        )

    return final_flights


# ============================================================
# STEP 5
# PYTHON RECOMMENDATION
# ============================================================

def select_recommendation(
    flights: list,
    preference: str
):

    if not flights:
        return None, None

    # --------------------------------------------------------
    # CHEAPEST
    # --------------------------------------------------------

    if preference == "cheapest":

        recommended = min(
            flights,
            key=lambda flight:
                flight["fare"]["total_fare"]
        )

        reason = "Lowest total fare"

    # --------------------------------------------------------
    # EARLIEST
    # --------------------------------------------------------

    elif preference == "earliest":

        recommended = min(
            flights,
            key=lambda flight:
                parse_time(
                    flight.get(
                        "departure_time"
                    )
                ) or datetime.max
        )

        reason = "Earliest departure"

    # --------------------------------------------------------
    # FASTEST
    # --------------------------------------------------------

    elif preference == "fastest":

        recommended = min(
            flights,
            key=lambda flight:
                flight_duration_minutes(
                    flight.get(
                        "departure_time",
                        ""
                    ),
                    flight.get(
                        "arrival_time",
                        ""
                    )
                )
        )

        reason = "Shortest travel time"

    # --------------------------------------------------------
    # AUTOMATIC
    # --------------------------------------------------------

    else:

        recommended = min(
            flights,
            key=lambda flight: (
                flight["fare"]["total_fare"],
                parse_time(
                    flight.get(
                        "departure_time"
                    )
                ) or datetime.max
            )
        )

        reason = (
            "Best overall option based on "
            "fare and departure time"
        )

    return recommended, reason


# ============================================================
# UTILITY FUNCTION 7
# FORMAT DATE FOR DISPLAY
# ============================================================

def format_date_display(
    date_str: str
) -> str:

    try:

        date = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        )

        return date.strftime(
            "%d-%b-%Y"
        )

    except ValueError:

        return date_str


# ============================================================
# STEP 6
# FORMAT RESPONSE WITHOUT LLM
# ============================================================

def format_flight_response(
    request_data: FlightSearchRequest,
    flights: list,
    recommended_flight: Optional[dict],
    recommendation_reason: Optional[str]
) -> str:

    origin = request_data.origin
    destination = request_data.destination
    date = format_date_display(
        request_data.date
    )

    total_seats = request_data.total_seats

    travel_class = (
        request_data.travel_class
        or "Available classes"
    )

    # --------------------------------------------------------
    # NO FLIGHTS
    # --------------------------------------------------------

    if not flights:

        return (
            f"✈️ No flights were found from "
            f"{origin} to {destination} "
            f"on {date} for "
            f"{total_seats} passenger(s)."
        )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    lines = [

        "✈️ Flight Options",

        "",

        f"{origin} → {destination}",

        f"Date: {date}",

        f"Passengers: {total_seats}",

        f"Class: {travel_class}",

        "",

        "| Airline | Flight | Class | "
        "Departure | Arrival | Seats | Fare |",

        "|---|---|---|---|---|---:|---:|"
    ]

    # --------------------------------------------------------
    # FLIGHT TABLE
    # --------------------------------------------------------

    for flight in flights:

        fare = flight.get(
            "fare",
            {}
        )

        total_fare = fare.get(
            "total_fare"
        )

        fare_display = (
            f"₹{total_fare:,.0f}"
            if total_fare is not None
            else "N/A"
        )

        lines.append(

            f"| {flight.get('airline', 'N/A')} "
            f"| {flight.get('flight_id', 'N/A')} "
            f"| {flight.get('travel_class', 'N/A')} "
            f"| {flight.get('departure_time', 'N/A')} "
            f"| {flight.get('arrival_time', 'N/A')} "
            f"| {flight.get('available_seats', 0)} "
            f"| {fare_display} |"
        )

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    if recommended_flight:

        fare = recommended_flight.get(
            "fare",
            {}
        )

        total_fare = fare.get(
            "total_fare"
        )

        fare_display = (
            f"₹{total_fare:,.0f}"
            if total_fare is not None
            else "N/A"
        )

        lines.extend([

            "",

            "🤖 Recommended Flight",

            (
                f"{recommended_flight.get('airline', 'N/A')} "
                f"{recommended_flight.get('flight_id', 'N/A')}"
            ),

            (
                f"Reason: "
                f"{recommendation_reason}"
            ),

            (
                f"Departure: "
                f"{recommended_flight.get('departure_time', 'N/A')}"
            ),

            (
                f"Arrival: "
                f"{recommended_flight.get('arrival_time', 'N/A')}"
            ),

            (
                f"Class: "
                f"{recommended_flight.get('travel_class', 'N/A')}"
            ),

            (
                f"Total Fare: "
                f"{fare_display}"
            )
        ])

    return "\n".join(lines)


# ============================================================
# MAIN AGENT
# ============================================================

async def search_flights_with_agent(
    user_request: str
) -> dict:

    logger.info(
        "Flight search agent started."
    )

    # ========================================================
    # 1. LLM UNDERSTANDS REQUEST
    # ========================================================

    request_data = await understand_flight_request(
        user_request
    )

    # ========================================================
    # 2. MCP SEARCHES DATABASE
    # ========================================================

    flights = await fetch_flights_from_mcp(
        request_data
    )

    # ========================================================
    # 3. CHECK REAL-TIME AVAILABILITY
    # ========================================================

    flights = await check_flight_availability(
        flights,
        request_data.total_seats
    )

    # ========================================================
    # 4. GET FARES
    # ========================================================

    flights = await fetch_fares(
        flights,
        request_data
    )

    # ========================================================
    # 5. PYTHON SELECTS RECOMMENDATION
    # ========================================================

    recommended_flight, recommendation_reason = (
        select_recommendation(
            flights,
            request_data.preference
        )
    )

    # ========================================================
    # 6. PYTHON FORMATS USER RESPONSE
    # ========================================================

    message = format_flight_response(

        request_data=request_data,

        flights=flights,

        recommended_flight=recommended_flight,

        recommendation_reason=recommendation_reason
    )

    # ========================================================
    # 7. RETURN FINAL API RESPONSE
    # ========================================================

    return {

        "user_request": user_request,

        "search_parameters":
            request_data.model_dump(),

        "flights": flights,

        "recommended_flight":
            recommended_flight,

        "recommendation_reason":
            recommendation_reason,

        "message":
            message
    }