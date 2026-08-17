import os
import json
import logging
from datetime import datetime, date
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
# PYDANTIC MODEL 1
# LLM EXTRACTION MODEL
#
# IMPORTANT:
# Every field is optional here.
#
# The LLM is ONLY responsible for extracting what the user
# actually said.
#
# Python will decide whether the request is valid.
# ============================================================

class ExtractedFlightRequest(BaseModel):

    origin: Optional[str] = None

    destination: Optional[str] = None

    date: Optional[str] = None

    # Raw date expression from the user.
    #
    # Examples:
    # "20 Aug"
    # "35 Aug"
    # "yesterday"
    # "tomorrow"
    #
    # This helps Python distinguish:
    #
    #   no date provided
    #
    # from:
    #
    #   invalid date provided
    #
    date_raw: Optional[str] = None

    total_seats: Optional[int] = None

    travel_class: Optional[str] = None

    max_price: Optional[float] = None

    preference: Optional[str] = None

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def normalize_city_values(cls, value):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        return value

    @field_validator("travel_class", mode="before")
    @classmethod
    def normalize_travel_class(cls, value):

        if value is None:
            return None

        return str(value).strip().lower()

    @field_validator("preference", mode="before")
    @classmethod
    def normalize_preference(cls, value):

        if value is None:
            return None

        return str(value).strip().lower()


# ============================================================
# PYDANTIC MODEL 2
# VALIDATED BUSINESS REQUEST
#
# This model is created ONLY AFTER Python has checked that
# required information exists.
# ============================================================

class FlightSearchRequest(BaseModel):

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
        ge=1
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
#
# IMPORTANT:
#
# The LLM must NOT invent missing information.
#
# The LLM must NOT decide whether something is valid.
#
# The LLM only extracts what the user said.
# ============================================================

REQUEST_SYSTEM_PROMPT = f"""
You are a flight search parameter extraction assistant.

Your ONLY job is to extract information explicitly mentioned
by the user.

Return JSON only.

Use exactly these fields:

{{
    "origin": null,
    "destination": null,
    "date": null,
    "date_raw": null,
    "total_seats": null,
    "travel_class": null,
    "max_price": null,
    "preference": null
}}

IMPORTANT RULES:

1. origin

Extract the departure city.

If the user did not provide an origin:

"origin": null

Do not invent an origin.


2. destination

Extract the arrival city.

If the user did not provide a destination:

"destination": null

Do not invent a destination.


3. date

Extract the travel date.

If the user gives a valid date and it can be converted,
return it as:

YYYY-MM-DD

If the user gives a relative date such as:

- today
- tomorrow
- yesterday

convert it using the current date:

{datetime.now().strftime("%Y-%m-%d")}

If the user gives a date without a year,
use year {PROJECT_YEAR}.

If the user does not mention any date:

"date": null

If the user provides a date expression that appears invalid,
for example:

"35 Aug"
"February 30"

then:

"date": null

but preserve the user's expression in:

"date_raw": "35 Aug"

This allows Python to detect that the user supplied an invalid date.

If the user does not mention a date at all:

"date_raw": null


4. date_raw

Preserve the date expression used by the user.

Examples:

User:
"Chennai to Delhi on 20 Aug"

Return:

"date_raw": "20 Aug"

User:
"Chennai to Delhi yesterday"

Return:

"date_raw": "yesterday"

User:
"Chennai to Delhi"

Return:

"date_raw": null


5. total_seats

Extract the number of passengers.

Examples:

"2 people" -> 2
"for 3 passengers" -> 3
"5 seats" -> 5

If the user does not specify passengers:

"total_seats": null

DO NOT automatically use 1.

Python will apply the default after validation.


6. travel_class

Allowed values:

- economy
- premium economy
- business
- first class

If not specified:

"travel_class": null


7. max_price

If the user specifies a maximum price,
return the numeric value.

Example:

"under 5000"

return:

5000

If not specified:

"max_price": null


8. preference

Use:

"cheapest"

for:

- cheapest
- lowest price
- lowest fare
- cheapest flight
- budget
- affordable

Use:

"earliest"

for:

- earliest
- first flight
- early morning
- first available

Use:

"fastest"

for:

- fastest
- quickest
- shortest
- least travel time

If no preference is specified:

"preference": null


IMPORTANT:

Do NOT validate the request.

Do NOT decide whether the city exists.

Do NOT decide whether flights exist.

Do NOT decide whether the date is allowed.

Do NOT decide whether the number of passengers is valid.

Do NOT generate default values.

Only extract what the user said.

Return JSON only.
"""


# ============================================================
# UTILITY FUNCTION 1
# PARSE LLM JSON
# ============================================================

def parse_json_response(text: str) -> dict:
    """
    Safely parse JSON returned by the LLM.
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
# NORMALIZE EXTRACTION DATA
#
# This does NOT decide whether the request is valid.
#
# It only cleans the extracted values.
# ============================================================

def normalize_extracted_data(
    data: ExtractedFlightRequest
) -> ExtractedFlightRequest:

    if data.origin:

        data.origin = normalize_city(
            data.origin
        )

    if data.destination:

        data.destination = normalize_city(
            data.destination
        )

    return data


# ============================================================
# UTILITY FUNCTION 4
# CHECK MISSING REQUIRED FIELDS
#
# Python controls this.
# ============================================================

def check_missing_fields(
    data: ExtractedFlightRequest
) -> Optional[dict]:

    # --------------------------------------------------------
    # Origin missing
    # --------------------------------------------------------

    if not data.origin:

        return {
            "status": "needs_information",
            "missing_fields": ["origin"],
            "message": (
                "Please provide the departure city."
            )
        }

    # --------------------------------------------------------
    # Destination missing
    # --------------------------------------------------------

    if not data.destination:

        return {
            "status": "needs_information",
            "missing_fields": ["destination"],
            "message": (
                "Please provide the destination city."
            )
        }

    # --------------------------------------------------------
    # Date missing
    # --------------------------------------------------------

    if not data.date:

        # If date_raw exists, the user actually provided
        # something that could not be converted into a valid date.
        #
        # Example:
        #
        # "35 Aug"
        #
        if data.date_raw:

            return {
                "status": "validation_error",
                "field": "date",
                "message": (
                    f"Invalid travel date "
                    f"'{data.date_raw}'. "
                    f"Please provide a valid future date."
                )
            }

        # No date at all.
        return {
            "status": "needs_information",
            "missing_fields": ["date"],
            "message": (
                "Please provide the travel date."
            )
        }

    return None


# ============================================================
# UTILITY FUNCTION 5
# VALIDATE BUSINESS INPUT
#
# This is Python-controlled validation.
# ============================================================

def validate_search_request(
    data: ExtractedFlightRequest
) -> tuple[Optional[FlightSearchRequest], Optional[dict]]:

    # --------------------------------------------------------
    # Step 1
    # Check missing fields
    # --------------------------------------------------------

    missing_result = check_missing_fields(
        data
    )

    if missing_result:

        return None, missing_result

    # --------------------------------------------------------
    # Step 2
    # Origin and destination cannot be same
    # --------------------------------------------------------

    if (
        data.origin.lower()
        == data.destination.lower()
    ):

        return None, {
            "status": "validation_error",
            "field": "origin_destination",
            "message": (
                "Origin and destination cannot be the same."
            )
        }

    # --------------------------------------------------------
    # Step 3
    # Validate date format
    # --------------------------------------------------------

    try:

        search_date = datetime.strptime(
            data.date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return None, {
            "status": "validation_error",
            "field": "date",
            "message": (
                "Invalid travel date. "
                "Please provide a valid date."
            )
        }

    # --------------------------------------------------------
    # Step 4
    # Date cannot be in the past
    # --------------------------------------------------------

    today = date.today()

    if search_date < today:

        return None, {
            "status": "validation_error",
            "field": "date",
            "message": (
                "Travel date cannot be in the past. "
                "Please provide today or a future date."
            )
        }

    # --------------------------------------------------------
    # Step 5
    # Passenger validation
    #
    # IMPORTANT:
    # If user didn't mention passengers,
    # Python applies default = 1.
    # --------------------------------------------------------

    total_seats = data.total_seats

    if total_seats is None:

        total_seats = 1

    elif total_seats < 1:

        return None, {
            "status": "validation_error",
            "field": "total_seats",
            "message": (
                "Number of passengers must be at least 1."
            )
        }

    # --------------------------------------------------------
    # Step 6
    # Maximum price validation
    # --------------------------------------------------------

    if (
        data.max_price is not None
        and data.max_price <= 0
    ):

        return None, {
            "status": "validation_error",
            "field": "max_price",
            "message": (
                "Maximum price must be greater than 0."
            )
        }

    # --------------------------------------------------------
    # Step 7
    # Travel class validation
    # --------------------------------------------------------

    allowed_classes = {
        "economy",
        "premium economy",
        "business",
        "first class"
    }

    travel_class = data.travel_class

    if travel_class:

        travel_class = travel_class.strip().lower()

        if travel_class not in allowed_classes:

            return None, {
                "status": "validation_error",
                "field": "travel_class",
                "message": (
                    "Invalid travel class. Choose economy, "
                    "premium economy, business, or first class."
                )
            }

    # --------------------------------------------------------
    # Step 8
    # Preference validation
    # --------------------------------------------------------

    preference = data.preference

    if preference is None:

        preference = "automatic"

    allowed_preferences = {
        "cheapest",
        "earliest",
        "fastest",
        "automatic"
    }

    if preference not in allowed_preferences:

        return None, {
            "status": "validation_error",
            "field": "preference",
            "message": (
                "Invalid flight preference."
            )
        }

    # --------------------------------------------------------
    # Step 9
    # Create strict business model
    #
    # ONLY NOW do we create FlightSearchRequest.
    # --------------------------------------------------------

    try:

        request = FlightSearchRequest(
            origin=data.origin,
            destination=data.destination,
            date=data.date,
            total_seats=total_seats,
            travel_class=travel_class,
            max_price=data.max_price,
            preference=preference
        )

    except ValidationError as exc:

        logger.error(
            "Validated request failed Pydantic validation: %s",
            exc
        )

        return None, {
            "status": "validation_error",
            "message": (
                "The flight search information is invalid."
            )
        }

    return request, None


# ============================================================
# UTILITY FUNCTION 6
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

        if (
            text.startswith("Error executing tool")
            or "Exception" in text
            or (
                "error" in text.lower()
                and not text.startswith("{")
                and not text.startswith("[")
            )
        ):

            logger.error(
                "MCP tool returned error string: %s",
                text
            )

            raise RuntimeError(
                f"MCP tool error: {text}"
            )

        try:

            parsed = json.loads(text)

        except json.JSONDecodeError:

            import ast

            try:

                parsed = ast.literal_eval(
                    text
                )

            except Exception as exc:

                logger.error(
                    "Failed to parse MCP response "
                    "as JSON or Python literal: %s",
                    text
                )

                raise ValueError(
                    f"MCP returned invalid data format: {text}"
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
# UTILITY FUNCTION 7
# PARSE TIME
# ============================================================

def parse_time(
    time_str: Optional[str]
):

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
# UTILITY FUNCTION 8
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

    if (
        departure is None
        or arrival is None
    ):

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
#
# IMPORTANT:
#
# The LLM only extracts information.
#
# Python validates it later.
# ============================================================

async def understand_flight_request(
    user_request: str
) -> ExtractedFlightRequest:

    if not user_request or not user_request.strip():

        raise ValueError(
            "Flight search request cannot be empty."
        )

    if len(user_request) > 1000:

        raise ValueError(
            "Flight search request is too long."
        )

    user_request = user_request.strip()

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
                    "content": user_request
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
    # Validate only the structure of the extraction.
    #
    # This is NOT business validation.
    # --------------------------------------------------------

    try:

        extracted_data = ExtractedFlightRequest(
            **raw_data
        )

    except ValidationError as exc:

        logger.error(
            "LLM extraction failed schema validation: %s",
            exc
        )

        raise ValueError(
            "LLM returned invalid flight information."
        ) from exc

    # --------------------------------------------------------
    # Normalize extracted values
    # --------------------------------------------------------

    extracted_data = normalize_extracted_data(
        extracted_data
    )

    logger.info(
        "LLM extracted data: %s",
        extracted_data.model_dump()
    )

    return extracted_data


# ============================================================
# STEP 2
# VALIDATE REQUEST
#
# Python decides:
#
# - missing information
# - invalid date
# - past date
# - invalid passengers
# - invalid class
# - invalid preference
# - same origin/destination
# ============================================================

async def prepare_flight_request(
    user_request: str
):
    """
    LLM extraction followed by Python validation.
    """

    try:

        extracted_data = await understand_flight_request(
            user_request
        )

    except ValueError as exc:

        return None, {
            "status": "validation_error",
            "message": str(exc)
        }

    except RuntimeError as exc:

        return None, {
            "status": "error",
            "message": str(exc)
        }

    request_data, validation_error = (
        validate_search_request(
            extracted_data
        )
    )

    if validation_error:

        return None, validation_error

    logger.info(
        "Python validation successful: %s",
        request_data.model_dump()
    )

    return request_data, None


# ============================================================
# STEP 3
# CALL MCP SEARCH TOOL
#
# MCP is called ONLY after Python validation succeeds.
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
# STEP 4
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
# STEP 5
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
        # TRAVEL CLASS LOGIC
        # ----------------------------------------------------

        requested_class = (
            request_data.travel_class
        )

        database_class = flight.get(
            "travel_class"
        )

        # User explicitly requested a class.
        if requested_class:

            fare_class = requested_class

        # User did not specify a class.
        # Use database class.
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
# STEP 6
# PYTHON RECOMMENDATION
#
# NO LLM HERE.
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
# UTILITY FUNCTION 9
# FORMAT DATE FOR DISPLAY
# ============================================================

def format_date_display(
    date_str: str
) -> str:

    try:

        parsed_date = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        )

        return parsed_date.strftime(
            "%d-%b-%Y"
        )

    except ValueError:

        return date_str


# ============================================================
# STEP 7
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

    date_display = format_date_display(
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
            f"on {date_display} for "
            f"{total_seats} passenger(s)."
        )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    lines = [

        "✈️ Flight Options",

        "",

        f"{origin} → {destination}",

        f"Date: {date_display}",

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
    # 1. LLM EXTRACTION
    #
    # LLM ONLY understands the user's request.
    # ========================================================

    request_data, validation_error = (
        await prepare_flight_request(
            user_request
        )
    )

    # ========================================================
    # 2. STOP IF PYTHON VALIDATION FAILED
    #
    # MCP must NOT be called.
    # ========================================================

    if validation_error:

        logger.info(
            "Flight request rejected: %s",
            validation_error
        )

        return {
            "user_request": user_request,
            **validation_error
        }

    # ========================================================
    # 3. MCP SEARCHES DATABASE
    # ========================================================

    try:

        flights = await fetch_flights_from_mcp(
            request_data
        )

    except RuntimeError as exc:

        logger.exception(
            "Flight search failed."
        )

        return {
            "user_request": user_request,
            "status": "error",
            "message": str(exc)
        }

    # ========================================================
    # 4. NO FLIGHTS FOUND
    #
    # This is not an LLM error.
    #
    # MCP/database is the source of truth.
    # ========================================================

    if not flights:

        message = (
            f"No flights were found from "
            f"{request_data.origin} "
            f"to {request_data.destination} "
            f"on "
            f"{format_date_display(request_data.date)}."
        )

        return {

            "user_request": user_request,

            "status": "no_results",

            "search_parameters":
                request_data.model_dump(),

            "flights": [],

            "recommended_flight": None,

            "recommendation_reason": None,

            "message": message
        }

    # ========================================================
    # 5. CHECK REAL-TIME AVAILABILITY
    # ========================================================

    try:

        flights = await check_flight_availability(
            flights,
            request_data.total_seats
        )

    except RuntimeError as exc:

        logger.exception(
            "Availability check failed."
        )

        return {

            "user_request": user_request,

            "status": "error",

            "search_parameters":
                request_data.model_dump(),

            "message": str(exc)
        }

    # ========================================================
    # 6. NO FLIGHTS WITH ENOUGH SEATS
    # ========================================================

    if not flights:

        message = (
            f"No available flights have enough seats "
            f"for {request_data.total_seats} passenger(s)."
        )

        return {

            "user_request": user_request,

            "status": "no_availability",

            "search_parameters":
                request_data.model_dump(),

            "flights": [],

            "recommended_flight": None,

            "recommendation_reason": None,

            "message": message
        }

    # ========================================================
    # 7. GET FARES
    # ========================================================

    try:

        flights = await fetch_fares(
            flights,
            request_data
        )

    except RuntimeError as exc:

        logger.exception(
            "Fare calculation failed."
        )

        return {

            "user_request": user_request,

            "status": "error",

            "search_parameters":
                request_data.model_dump(),

            "message": str(exc)
        }

    # ========================================================
    # 8. NO VALID FARES
    # ========================================================

    if not flights:

        return {

            "user_request": user_request,

            "status": "no_results",

            "search_parameters":
                request_data.model_dump(),

            "flights": [],

            "recommended_flight": None,

            "recommendation_reason": None,

            "message": (
                "No flights with valid fare information "
                "are currently available."
            )
        }

    # ========================================================
    # 9. PYTHON SELECTS RECOMMENDATION
    #
    # NO LLM.
    # ========================================================

    recommended_flight, recommendation_reason = (
        select_recommendation(
            flights,
            request_data.preference
        )
    )

    # ========================================================
    # 10. PYTHON FORMATS USER RESPONSE
    #
    # NO LLM.
    # ========================================================

    message = format_flight_response(

        request_data=request_data,

        flights=flights,

        recommended_flight=recommended_flight,

        recommendation_reason=recommendation_reason
    )

    # ========================================================
    # 11. FINAL API RESPONSE
    # ========================================================

    return {

        "user_request": user_request,

        "status": "success",

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