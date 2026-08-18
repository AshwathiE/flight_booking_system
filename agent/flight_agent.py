import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, Any, Tuple

from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.utils.datetime_utils import (
    get_current_date_kolkata,
    get_current_datetime_kolkata,
)

from backend.mcp_client import (
    search_flights_mcp,
    get_flight_details_mcp,
    check_availability_mcp,
    get_fare_mcp,
    create_booking_mcp,
    get_booking_mcp,
    get_user_bookings_mcp,
    cancel_booking_mcp,
    change_booking_mcp,
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

PROJECT_YEAR = 2026
LLM_MODEL = "openai/gpt-oss-120b"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured. "
        "Please add GROQ_API_KEY to your .env file."
    )

client = AsyncGroq(api_key=GROQ_API_KEY)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("flight_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# ============================================================
# MCP TOOL WHITELIST
# ============================================================

ALLOWED_TOOLS = {
    "search_flights",
    "get_flight_details",
    "check_availability",
    "get_fare",
    "create_booking",
    "get_booking",
    "get_user_bookings",
    "cancel_booking",
    "change_booking",
}


# ============================================================
# MCP TOOL DISPATCH MAP
# ============================================================

TOOL_MAP = {
    "search_flights": search_flights_mcp,
    "get_flight_details": get_flight_details_mcp,
    "check_availability": check_availability_mcp,
    "get_fare": get_fare_mcp,
    "create_booking": create_booking_mcp,
    "get_booking": get_booking_mcp,
    "get_user_bookings": get_user_bookings_mcp,
    "cancel_booking": cancel_booking_mcp,
    "change_booking": change_booking_mcp,
}


# ============================================================
# PYDANTIC MODEL
# LLM AGENT DECISION
# ============================================================

class AgentDecision(BaseModel):
    intent: Literal[
        "SEARCH_FLIGHTS",
        "GET_FLIGHT_DETAILS",
        "CHECK_AVAILABILITY",
        "GET_FARE",
        "CREATE_BOOKING",
        "GET_BOOKING",
        "GET_USER_BOOKINGS",
        "CANCEL_BOOKING",
        "CHANGE_BOOKING",
        "UNKNOWN",
    ]

    tool: Optional[str] = None

    parameters: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# PYDANTIC MODEL
# VALIDATED FLIGHT SEARCH REQUEST
# ============================================================

class FlightSearchRequest(BaseModel):
    origin: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    destination: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
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
            "first class",
        ]
    ] = None

    max_price: Optional[float] = Field(
        default=None,
        gt=0,
    )

    preference: Literal[
        "cheapest",
        "earliest",
        "fastest",
        "automatic",
    ] = "automatic"

    @field_validator("origin", "destination")
    @classmethod
    def validate_city(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("City cannot be empty.")

        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
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

CURRENT_DATE = get_current_date_kolkata()

AGENT_SYSTEM_PROMPT = f"""
You are the Flight Booking AI Agent.

Your responsibility is to understand the user's natural language request,
identify the user's intent, select exactly one appropriate tool from the
allowed flight-booking tools, and extract the parameters required by that tool.

You must not access databases directly.
You must not generate SQL.
You must not invent flights, prices, availability, bookings, or payment information.
You must not execute tools yourself.
You must only return a structured tool decision as valid JSON.

Available tools are:

- search_flights:
  Search for flights between cities on a date.
  Optional:
  total_seats, travel_class, max_price, preference

- get_flight_details:
  Retrieve complete details for a specific flight.
  Parameter:
  flight_id

- check_availability:
  Check seat availability on a flight.
  Parameters:
  flight_id, total_seats

- get_fare:
  Calculate fare and pricing for a flight.
  Parameters:
  flight_id, total_seats, travel_class

- create_booking:
  Book seats on a flight.
  Parameters:
  flight_id, number_of_seats, user_id

- get_booking:
  Retrieve booking details.
  Parameters:
  booking_id or booking_reference

- get_user_bookings:
  Retrieve all bookings for a user.
  Parameter:
  user_id

- cancel_booking:
  Cancel an existing booking.
  Parameters:
  booking_id or booking_reference, user_id

- change_booking:
  Change flight or seats for a booking.
  Parameters:
  booking_id, new_flight_id, new_number_of_seats, user_id


Allowed intents:

- SEARCH_FLIGHTS
- GET_FLIGHT_DETAILS
- CHECK_AVAILABILITY
- GET_FARE
- CREATE_BOOKING
- GET_BOOKING
- GET_USER_BOOKINGS
- CANCEL_BOOKING
- CHANGE_BOOKING
- UNKNOWN


Tool mapping:

SEARCH_FLIGHTS -> search_flights
GET_FLIGHT_DETAILS -> get_flight_details
CHECK_AVAILABILITY -> check_availability
GET_FARE -> get_fare
CREATE_BOOKING -> create_booking
GET_BOOKING -> get_booking
GET_USER_BOOKINGS -> get_user_bookings
CANCEL_BOOKING -> cancel_booking
CHANGE_BOOKING -> change_booking
UNKNOWN -> null


Choose a tool only when the user's request clearly requires it.

If the request is unrelated to flight booking, greetings,
general conversation, or weather, return:

intent = UNKNOWN
tool = null


If required information is missing, still identify the intended tool
and extract whatever information is available.

Do not invent missing values.

Do not guess critical information such as:

- origin
- destination
- travel date
- flight ID
- booking reference
- booking ID
- number of seats


Relative Date Resolution:

Current date in India/Kolkata:
{CURRENT_DATE.strftime("%Y-%m-%d")}

Year:
{PROJECT_YEAR}

Rules:

- "today" -> today's date
- "tomorrow" -> tomorrow's date
- If date is without year, assume year {PROJECT_YEAR}


Return ONLY a JSON object:

{{
    "intent": "INTENT_NAME",
    "tool": "tool_name_or_null",
    "parameters": {{
        ...
    }}
}}


FEW-SHOT EXAMPLES:


Example 1:

User:
"Find flights from Chennai to Delhi tomorrow."

Output:

{{
    "intent": "SEARCH_FLIGHTS",
    "tool": "search_flights",
    "parameters": {{
        "origin": "Chennai",
        "destination": "Delhi",
        "date": "tomorrow",
        "date_raw": "tomorrow",
        "total_seats": 1
    }}
}}


Example 2:

User:
"Are there 3 seats available on flight 6E207?"

Output:

{{
    "intent": "CHECK_AVAILABILITY",
    "tool": "check_availability",
    "parameters": {{
        "flight_id": "6E207",
        "total_seats": 3
    }}
}}


Example 3:

User:
"How much does flight 6E207 cost in business class?"

Output:

{{
    "intent": "GET_FARE",
    "tool": "get_fare",
    "parameters": {{
        "flight_id": "6E207",
        "travel_class": "business"
    }}
}}


Example 4:

User:
"Give me the details of flight 6E207."

Output:

{{
    "intent": "GET_FLIGHT_DETAILS",
    "tool": "get_flight_details",
    "parameters": {{
        "flight_id": "6E207"
    }}
}}


Example 5:

User:
"Book 2 seats on flight 6E207."

Output:

{{
    "intent": "CREATE_BOOKING",
    "tool": "create_booking",
    "parameters": {{
        "flight_id": "6E207",
        "number_of_seats": 2
    }}
}}


Example 6:

User:
"Cancel booking 12."

Output:

{{
    "intent": "CANCEL_BOOKING",
    "tool": "cancel_booking",
    "parameters": {{
        "booking_id": 12
    }}
}}


Example 7:

User:
"Change booking 15 to flight AI202 for 3 seats."

Output:

{{
    "intent": "CHANGE_BOOKING",
    "tool": "change_booking",
    "parameters": {{
        "booking_id": 15,
        "new_flight_id": "AI202",
        "new_number_of_seats": 3
    }}
}}


Example 8:

User:
"Hello, how are you?"

Output:

{{
    "intent": "UNKNOWN",
    "tool": null,
    "parameters": {{}}
}}
"""


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(text: str) -> dict:
    """
    Safely parse JSON returned by the LLM.
    """

    if not text or not text.strip():
        raise ValueError("LLM returned an empty response.")

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        data = json.loads(text)

    except json.JSONDecodeError as exc:
        logger.error(
            "❌ [JSON PARSER] Invalid JSON received from LLM:\n%s",
            text,
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
# CITY NORMALIZATION
# ============================================================

def normalize_city(city: str) -> str:
    """
    Normalize common city names.
    """

    if not city:
        return ""

    cleaned = " ".join(
        city.strip().split()
    )

    mapping = {
        "madras": "Chennai",
        "bombay": "Mumbai",
        "calcutta": "Kolkata",
        "bangalore": "Bengaluru",
    }

    normalized = mapping.get(
        cleaned.lower(),
        cleaned.title(),
    )

    if cleaned.lower() != normalized.lower():
        logger.info(
            "📍 [CITY NORMALIZER] '%s' normalized to '%s'",
            city,
            normalized,
        )

    return normalized


# ============================================================
# DATE RESOLUTION
# ============================================================

def resolve_date_string(
    date_str: Optional[str],
) -> Optional[str]:
    """
    Convert natural language or common date formats
    into YYYY-MM-DD.
    """

    if not date_str:
        return None

    cleaned = str(date_str).strip().lower()

    today = get_current_date_kolkata()

    resolved = None

    if cleaned in ("today", "now"):

        resolved = today.strftime("%Y-%m-%d")

    elif cleaned == "tomorrow":

        resolved = (
            today + timedelta(days=1)
        ).strftime("%Y-%m-%d")

    elif cleaned == "yesterday":

        resolved = (
            today - timedelta(days=1)
        ).strftime("%Y-%m-%d")

    elif cleaned.startswith(
        "day after tomorrow"
    ):

        resolved = (
            today + timedelta(days=2)
        ).strftime("%Y-%m-%d")

    if resolved:

        logger.info(
            "📅 [DATE RESOLVER] Relative date '%s' resolved to '%s'",
            date_str,
            resolved,
        )

        return resolved

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%d %b",
        "%d %B",
        "%b %d",
        "%B %d",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                cleaned,
                fmt,
            )

            if "%Y" not in fmt and "%y" not in fmt:
                parsed = parsed.replace(
                    year=PROJECT_YEAR
                )

            resolved = parsed.strftime(
                "%Y-%m-%d"
            )

            logger.info(
                "📅 [DATE RESOLVER] Date expression '%s' parsed to '%s'",
                date_str,
                resolved,
            )

            return resolved

        except ValueError:
            continue

    return date_str


# ============================================================
# TIME PARSER
# ============================================================

def parse_time(time_str: Optional[str]):
    """
    Parse HH:MM or HH:MM:SS.
    """

    if not time_str:
        return None

    for fmt in (
        "%H:%M:%S",
        "%H:%M",
    ):

        try:
            return datetime.strptime(
                time_str.strip(),
                fmt,
            )

        except ValueError:
            continue

    return None


# ============================================================
# FLIGHT DURATION
# ============================================================

def flight_duration_minutes(
    departure_time: str,
    arrival_time: str,
) -> int:
    """
    Calculate flight duration in minutes.
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
# DATE DISPLAY
# ============================================================

def format_date_display(
    date_str: str,
) -> str:
    """
    Convert YYYY-MM-DD into DD-Mon-YYYY.
    """

    try:

        parsed_date = datetime.strptime(
            date_str,
            "%Y-%m-%d",
        )

        return parsed_date.strftime(
            "%d-%b-%Y"
        )

    except ValueError:

        return date_str


# ============================================================
# MCP RESULT PARSER
# ============================================================

def parse_mcp_result(result) -> list:
    """
    Convert MCP TextContent into Python objects.
    """

    data = []

    for content in getattr(
        result,
        "content",
        [],
    ):

        if not hasattr(content, "text"):
            continue

        text = content.text

        if not text or not text.strip():
            continue

        if (
            text.startswith(
                "Error executing tool"
            )
            or "Exception" in text
            or (
                "error" in text.lower()
                and not text.startswith("{")
                and not text.startswith("[")
            )
        ):

            logger.error(
                "❌ [MCP ERROR] Tool returned error string: %s",
                text,
            )

            raise RuntimeError(
                f"MCP tool error: {text}"
            )

        try:

            parsed = json.loads(text)

        except json.JSONDecodeError:

            import ast

            try:

                parsed = ast.literal_eval(text)

            except Exception as exc:

                logger.error(
                    "❌ [MCP ERROR] Failed to parse MCP response: %s",
                    text,
                )

                raise ValueError(
                    f"MCP returned invalid data format: {text}"
                ) from exc

        if isinstance(parsed, list):

            data.extend(parsed)

        elif isinstance(parsed, dict):

            data.append(parsed)

        else:

            logger.warning(
                "⚠️ [MCP WARNING] Unexpected MCP result type: %s",
                type(parsed).__name__,
            )

    return data


# ============================================================
# LLM TOOL DECISION
# ============================================================

async def decide_tool(
    user_message: str,
) -> AgentDecision:
    """
    Ask the LLM to identify intent, tool,
    and parameters.
    """

    if not user_message or not user_message.strip():

        logger.info(
            "ℹ️ [AI AGENT] Empty user message, defaulting to UNKNOWN"
        )

        return AgentDecision(
            intent="UNKNOWN",
            tool=None,
            parameters={},
        )

    logger.info(
        "🧠 [LLM INFERENCE] Sending request to model '%s'...",
        LLM_MODEL,
    )

    logger.info(
        "📝 [USER PROMPT] \"%s\"",
        user_message.strip(),
    )

    try:

        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message.strip(),
                },
            ],
            temperature=0,
            response_format={
                "type": "json_object"
            },
        )

    except Exception as exc:

        logger.exception(
            "❌ [LLM ERROR] Groq inference call failed."
        )

        raise RuntimeError(
            "Unable to understand request with AI Agent."
        ) from exc

    content = response.choices[0].message.content

    logger.info(
        "📥 [LLM RAW OUTPUT] %s",
        content.strip(),
    )

    raw_data = parse_json_response(
        content
    )

    try:

        decision = AgentDecision(
            **raw_data
        )

    except ValidationError as exc:

        logger.error(
            "❌ [AGENT SCHEMA ERROR] Schema validation failed: %s",
            exc,
        )

        raise ValueError(
            "AI Agent returned invalid decision format."
        ) from exc

    logger.info(
        "🎯 [AGENT DECISION] Intent='%s' | Selected Tool='%s'",
        decision.intent,
        decision.tool,
    )

    logger.info(
        "📋 [RAW EXTRACTED PARAMS] %s",
        decision.parameters,
    )

    return decision


# ============================================================
# AGENT DECISION VALIDATION
# ============================================================

def validate_agent_decision(
    decision: AgentDecision,
    context_user_id: Optional[int] = None,
) -> Tuple[
    Dict[str, Any],
    Optional[Dict[str, Any]],
]:
    """
    Validate tool selection, parameters,
    and business rules.
    """

    logger.info(
        "🔍 [PYTHON VALIDATOR] Validating decision "
        "(Intent: %s, Tool: %s)...",
        decision.intent,
        decision.tool,
    )

    # --------------------------------------------------------
    # TOOL WHITELIST
    # --------------------------------------------------------

    if (
        decision.tool
        and decision.tool not in ALLOWED_TOOLS
    ):

        logger.warning(
            "🚨 [SECURITY WARNING] Rejected unauthorized tool: '%s'",
            decision.tool,
        )

        return {}, {
            "status": "validation_error",
            "field": "tool",
            "message": (
                f"Unauthorized or unknown tool: "
                f"{decision.tool}"
            ),
        }

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    if (
        decision.intent == "UNKNOWN"
        or not decision.tool
    ):

        return {}, {
            "status": "needs_information",
            "intent": "UNKNOWN",
            "message": (
                "Hello! I am your Flight Booking AI Assistant. "
                "You can ask me to search flights, check flight details, "
                "check seat availability, get fares, or manage bookings."
            ),
        }

    params = decision.parameters or {}

    # ========================================================
    # SEARCH FLIGHTS
    # ========================================================

    if decision.tool == "search_flights":

        origin = params.get("origin")
        destination = params.get("destination")
        date_val = params.get("date")
        date_raw = params.get("date_raw")

        if not origin:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["origin"],
                "message": "Please provide the departure city.",
            }

        if not destination:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["destination"],
                "message": "Please provide the destination city.",
            }

        norm_origin = normalize_city(
            str(origin)
        )

        norm_dest = normalize_city(
            str(destination)
        )

        if (
            norm_origin.lower()
            == norm_dest.lower()
        ):

            return {}, {
                "status": "validation_error",
                "field": "origin_destination",
                "message": (
                    "Origin and destination cannot be the same."
                ),
            }

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        resolved_date = resolve_date_string(
            date_val or date_raw
        )

        if not resolved_date:

            if date_raw:

                return {}, {
                    "status": "validation_error",
                    "field": "date",
                    "message": (
                        f"Invalid travel date '{date_raw}'. "
                        "Please provide a valid future date."
                    ),
                }

            return {}, {
                "status": "needs_information",
                "missing_fields": ["date"],
                "message": "Please provide the travel date.",
            }

        try:

            parsed_dt = datetime.strptime(
                resolved_date,
                "%Y-%m-%d",
            ).date()

        except ValueError:

            return {}, {
                "status": "validation_error",
                "field": "date",
                "message": (
                    f"Invalid travel date '{resolved_date}'. "
                    "Please provide date in YYYY-MM-DD format."
                ),
            }

        today_kolkata = get_current_date_kolkata()

        if parsed_dt < today_kolkata:

            return {}, {
                "status": "validation_error",
                "field": "date",
                "message": (
                    "Travel date cannot be in the past. "
                    "Please provide today or a future date."
                ),
            }

        # ----------------------------------------------------
        # SEATS
        # ----------------------------------------------------

        total_seats = params.get(
            "total_seats"
        )

        if total_seats is None:

            total_seats = 1

        else:

            try:

                total_seats = int(
                    total_seats
                )

            except (
                ValueError,
                TypeError,
            ):

                return {}, {
                    "status": "validation_error",
                    "field": "total_seats",
                    "message": (
                        "Number of passengers "
                        "must be a valid integer."
                    ),
                }

            if total_seats < 1:

                return {}, {
                    "status": "validation_error",
                    "field": "total_seats",
                    "message": (
                        "Number of passengers "
                        "must be at least 1."
                    ),
                }

        # ----------------------------------------------------
        # TRAVEL CLASS
        # ----------------------------------------------------

        travel_class = params.get(
            "travel_class"
        )

        if travel_class:

            travel_class = (
                str(travel_class)
                .strip()
                .lower()
            )

            allowed_classes = {
                "economy",
                "premium economy",
                "business",
                "first class",
            }

            if travel_class not in allowed_classes:

                return {}, {
                    "status": "validation_error",
                    "field": "travel_class",
                    "message": (
                        "Invalid travel class. "
                        "Choose economy, premium economy, "
                        "business, or first class."
                    ),
                }

            travel_class = travel_class.title()

        else:

            travel_class = None

        # ----------------------------------------------------
        # MAX PRICE
        # ----------------------------------------------------

        max_price = params.get(
            "max_price"
        )

        if max_price is not None:

            try:

                max_price = float(
                    max_price
                )

                if max_price <= 0:

                    return {}, {
                        "status": "validation_error",
                        "field": "max_price",
                        "message": (
                            "Maximum price must be greater than 0."
                        ),
                    }

            except (
                ValueError,
                TypeError,
            ):

                return {}, {
                    "status": "validation_error",
                    "field": "max_price",
                    "message": (
                        "Maximum price must be "
                        "a valid positive number."
                    ),
                }

        # ----------------------------------------------------
        # PREFERENCE
        # ----------------------------------------------------

        preference = params.get(
            "preference",
            "automatic",
        )

        if preference:

            preference = (
                str(preference)
                .strip()
                .lower()
            )

            if preference not in {
                "cheapest",
                "earliest",
                "fastest",
                "automatic",
            }:

                preference = "automatic"

        validated = {
            "origin": norm_origin,
            "destination": norm_dest,
            "date": resolved_date,
            "total_seats": total_seats,
            "travel_class": travel_class,
            "max_price": max_price,
            "preference": preference,
        }

        logger.info(
            "✅ [VALIDATION SUCCESS] search_flights: %s",
            validated,
        )

        return validated, None

    # ========================================================
    # GET FLIGHT DETAILS
    # ========================================================

    if decision.tool == "get_flight_details":

        flight_id = params.get(
            "flight_id"
        )

        if not flight_id or not str(
            flight_id
        ).strip():

            return {}, {
                "status": "needs_information",
                "missing_fields": ["flight_id"],
                "message": (
                    "Please provide a valid flight ID "
                    "(e.g. 6E207)."
                ),
            }

        validated = {
            "flight_id": str(
                flight_id
            ).strip().upper()
        }

        return validated, None

    # ========================================================
    # CHECK AVAILABILITY
    # ========================================================

    if decision.tool == "check_availability":

        flight_id = params.get(
            "flight_id"
        )

        if not flight_id or not str(
            flight_id
        ).strip():

            return {}, {
                "status": "needs_information",
                "missing_fields": ["flight_id"],
                "message": (
                    "Please provide a valid flight ID "
                    "to check availability."
                ),
            }

        total_seats = params.get(
            "total_seats",
            1,
        )

        try:

            total_seats = int(
                total_seats
            )

            if total_seats < 1:

                return {}, {
                    "status": "validation_error",
                    "field": "total_seats",
                    "message": (
                        "Number of seats must be at least 1."
                    ),
                }

        except (
            ValueError,
            TypeError,
        ):

            return {}, {
                "status": "validation_error",
                "field": "total_seats",
                "message": "Invalid seat count.",
            }

        return {
            "flight_id": str(
                flight_id
            ).strip().upper(),
            "total_seats": total_seats,
        }, None

    # ========================================================
    # GET FARE
    # ========================================================

    if decision.tool == "get_fare":

        flight_id = params.get(
            "flight_id"
        )

        if not flight_id or not str(
            flight_id
        ).strip():

            return {}, {
                "status": "needs_information",
                "missing_fields": ["flight_id"],
                "message": (
                    "Please provide a valid flight ID "
                    "to calculate fare."
                ),
            }

        total_seats = params.get(
            "total_seats",
            1,
        )

        try:

            total_seats = int(
                total_seats
            )

            if total_seats < 1:

                return {}, {
                    "status": "validation_error",
                    "field": "total_seats",
                    "message": (
                        "Number of seats must be at least 1."
                    ),
                }

        except (
            ValueError,
            TypeError,
        ):

            total_seats = 1

        travel_class = params.get(
            "travel_class",
            "Economy",
        )

        if travel_class:

            travel_class = str(
                travel_class
            ).strip().title()

        return {
            "flight_id": str(
                flight_id
            ).strip().upper(),
            "total_seats": total_seats,
            "travel_class": travel_class,
        }, None

    # ========================================================
    # CREATE BOOKING
    # ========================================================

    if decision.tool == "create_booking":

        flight_id = params.get(
            "flight_id"
        )

        if not flight_id or not str(
            flight_id
        ).strip():

            return {}, {
                "status": "needs_information",
                "missing_fields": ["flight_id"],
                "message": (
                    "Please provide the flight ID "
                    "to create a booking."
                ),
            }

        number_of_seats = params.get(
            "number_of_seats",
            params.get(
                "total_seats",
                1,
            ),
        )

        try:

            number_of_seats = int(
                number_of_seats
            )

            if number_of_seats < 1:

                return {}, {
                    "status": "validation_error",
                    "field": "number_of_seats",
                    "message": (
                        "Number of seats must be at least 1."
                    ),
                }

        except (
            ValueError,
            TypeError,
        ):

            return {}, {
                "status": "validation_error",
                "field": "number_of_seats",
                "message": "Invalid seat number.",
            }

        user_id = (
            params.get("user_id")
            or context_user_id
            or 1
        )

        try:

            user_id = int(
                user_id
            )

        except (
            ValueError,
            TypeError,
        ):

            user_id = 1

        return {
            "user_id": user_id,
            "flight_id": str(
                flight_id
            ).strip().upper(),
            "number_of_seats": number_of_seats,
        }, None

    # ========================================================
    # GET BOOKING
    # ========================================================

    if decision.tool == "get_booking":

        booking_id = params.get(
            "booking_id"
        )

        if not booking_id:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["booking_id"],
                "message": (
                    "Please provide a valid booking ID."
                ),
            }

        try:

            booking_id = int(
                str(booking_id)
                .replace("BK", "")
                .strip()
            )

        except ValueError:

            return {}, {
                "status": "validation_error",
                "field": "booking_id",
                "message": (
                    "Booking ID must be a numeric identifier."
                ),
            }

        user_id = (
            params.get("user_id")
            or context_user_id
        )

        return {
            "booking_id": booking_id,
            "user_id": (
                int(user_id)
                if user_id is not None
                else None
            ),
        }, None

    # ========================================================
    # GET USER BOOKINGS
    # ========================================================

    if decision.tool == "get_user_bookings":

        user_id = (
            params.get("user_id")
            or context_user_id
            or 1
        )

        try:

            user_id = int(
                user_id
            )

        except (
            ValueError,
            TypeError,
        ):

            user_id = 1

        return {
            "user_id": user_id
        }, None

    # ========================================================
    # CANCEL BOOKING
    # ========================================================

    if decision.tool == "cancel_booking":

        booking_id = params.get(
            "booking_id"
        )

        if not booking_id:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["booking_id"],
                "message": (
                    "Please provide the booking ID "
                    "to cancel."
                ),
            }

        try:

            booking_id = int(
                str(booking_id)
                .replace("BK", "")
                .strip()
            )

        except ValueError:

            return {}, {
                "status": "validation_error",
                "field": "booking_id",
                "message": (
                    "Booking ID must be a numeric identifier."
                ),
            }

        user_id = (
            params.get("user_id")
            or context_user_id
            or 1
        )

        try:

            user_id = int(
                user_id
            )

        except (
            ValueError,
            TypeError,
        ):

            user_id = 1

        return {
            "booking_id": booking_id,
            "user_id": user_id,
        }, None

    # ========================================================
    # CHANGE BOOKING
    # ========================================================

    if decision.tool == "change_booking":

        booking_id = params.get(
            "booking_id"
        )

        new_flight_id = params.get(
            "new_flight_id"
        )

        new_number_of_seats = params.get(
            "new_number_of_seats",
            params.get(
                "number_of_seats",
                1,
            ),
        )

        if not booking_id:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["booking_id"],
                "message": (
                    "Please provide the booking ID "
                    "to change."
                ),
            }

        if not new_flight_id:

            return {}, {
                "status": "needs_information",
                "missing_fields": ["new_flight_id"],
                "message": (
                    "Please provide the new flight ID."
                ),
            }

        try:

            booking_id = int(
                str(booking_id)
                .replace("BK", "")
                .strip()
            )

            new_number_of_seats = int(
                new_number_of_seats
            )

            if new_number_of_seats < 1:

                return {}, {
                    "status": "validation_error",
                    "field": "new_number_of_seats",
                    "message": (
                        "Number of seats must be at least 1."
                    ),
                }

        except (
            ValueError,
            TypeError,
        ):

            return {}, {
                "status": "validation_error",
                "field": "change_booking_params",
                "message": (
                    "Invalid numeric parameter "
                    "for change booking."
                ),
            }

        user_id = (
            params.get("user_id")
            or context_user_id
            or 1
        )

        return {
            "booking_id": booking_id,
            "user_id": int(user_id),
            "new_flight_id": str(
                new_flight_id
            ).strip().upper(),
            "new_number_of_seats": new_number_of_seats,
        }, None

    # ========================================================
    # DEFAULT
    # ========================================================

    return params, None


# ============================================================
# FETCH FLIGHTS
# ============================================================

async def fetch_flights_from_mcp(
    request_data: FlightSearchRequest,
) -> list:
    """
    Call search_flights MCP tool.
    """

    logger.info(
        "🔎 [MCP SEARCH] %s -> %s | Date: %s | Seats: %d | "
        "Class: %s | MaxPrice: %s",
        request_data.origin,
        request_data.destination,
        request_data.date,
        request_data.total_seats,
        request_data.travel_class,
        request_data.max_price,
    )

    try:

        result = await TOOL_MAP[
            "search_flights"
        ](
            origin=request_data.origin,
            destination=request_data.destination,
            date=request_data.date,
            total_seats=request_data.total_seats,
            travel_class=request_data.travel_class,
            max_price=request_data.max_price,
        )

    except Exception as exc:

        logger.exception(
            "❌ [MCP SEARCH ERROR] "
            "Flight search MCP failed."
        )

        raise RuntimeError(
            "Flight search service is currently unavailable."
        ) from exc

    flights = parse_mcp_result(
        result
    )

    logger.info(
        "📊 [MCP SEARCH RESULT] Retrieved %d flight(s).",
        len(flights),
    )

    return flights


# ============================================================
# CHECK FLIGHT AVAILABILITY
# ============================================================

async def check_flight_availability(
    flights: list,
    total_seats: int,
) -> list:
    """
    Verify seat availability for each flight.
    """

    logger.info(
        "💺 [MCP AVAILABILITY] Checking %d seat(s) "
        "for %d flight(s)...",
        total_seats,
        len(flights),
    )

    available_flights = []

    tool_fn = TOOL_MAP[
        "check_availability"
    ]

    for flight in flights:

        flight_id = flight.get(
            "flight_id"
        )

        if not flight_id:
            continue

        try:

            result = await tool_fn(
                flight_id=flight_id,
                total_seats=total_seats,
            )

            availability_data = parse_mcp_result(
                result
            )

        except Exception as exc:

            logger.exception(
                "❌ [MCP AVAILABILITY ERROR] "
                "Failed for flight %s.",
                flight_id,
            )

            raise RuntimeError(
                f"Unable to verify availability "
                f"for flight {flight_id}."
            ) from exc

        if not availability_data:
            continue

        availability = availability_data[0]

        available_seats = availability.get(
            "available_seats"
        )

        if (
            available_seats is not None
            and int(available_seats) >= total_seats
        ):

            flight["available_seats"] = int(
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

    logger.info(
        "✅ [MCP AVAILABILITY RESULT] "
        "%d flight(s) available.",
        len(available_flights),
    )

    return available_flights


# ============================================================
# FETCH FARES
# ============================================================

async def fetch_fares(
    flights: list,
    request_data: FlightSearchRequest,
) -> list:
    """
    Calculate and attach fares to flights.
    """

    logger.info(
        "💳 [MCP FARE] Calculating fares "
        "for %d flight(s)...",
        len(flights),
    )

    final_flights = []

    tool_fn = TOOL_MAP[
        "get_fare"
    ]

    for flight in flights:

        flight_id = flight.get(
            "flight_id"
        )

        if not flight_id:
            continue

        fare_class = (
            request_data.travel_class
            or flight.get("travel_class")
            or "Economy"
        )

        try:

            result = await tool_fn(
                flight_id=flight_id,
                total_seats=request_data.total_seats,
                travel_class=fare_class,
            )

            fare_data = parse_mcp_result(
                result
            )

        except Exception as exc:

            logger.exception(
                "❌ [MCP FARE ERROR] "
                "Failed for flight %s.",
                flight_id,
            )

            raise RuntimeError(
                f"Unable to calculate fare "
                f"for flight {flight_id}."
            ) from exc

        if not fare_data:
            continue

        fare = fare_data[0]

        if fare.get("error"):
            continue

        base_fare = float(
            fare.get(
                "base_fare",
                0,
            )
        )

        tax = float(
            fare.get(
                "tax",
                0,
            )
        )

        service_fee = float(
            fare.get(
                "service_fee",
                0,
            )
        )

        total_fare = float(
            fare.get(
                "total_fare",
                0,
            )
        )

        fare["base_fare"] = round(
            base_fare,
            2,
        )

        fare["tax"] = round(
            tax,
            2,
        )

        fare["service_fee"] = round(
            service_fee,
            2,
        )

        fare["total_fare"] = round(
            total_fare,
            2,
        )

        flight["fare"] = fare
        flight["travel_class"] = fare_class

        final_flights.append(
            flight
        )

    logger.info(
        "✅ [MCP FARE RESULT] "
        "%d flight(s) received fares.",
        len(final_flights),
    )

    return final_flights


# ============================================================
# FLIGHT RECOMMENDATION
# ============================================================

def select_recommendation(
    flights: list,
    preference: str,
):
    """
    Python-controlled recommendation.
    """

    if not flights:
        return None, None

    if preference == "cheapest":

        recommended = min(
            flights,
            key=lambda f: f.get(
                "fare",
                {},
            ).get(
                "total_fare",
                float("inf"),
            ),
        )

        reason = "Lowest total fare"

    elif preference == "earliest":

        recommended = min(
            flights,
            key=lambda f: (
                parse_time(
                    f.get(
                        "departure_time"
                    )
                )
                or datetime.max
            ),
        )

        reason = "Earliest departure"

    elif preference == "fastest":

        recommended = min(
            flights,
            key=lambda f: flight_duration_minutes(
                f.get(
                    "departure_time",
                    "",
                ),
                f.get(
                    "arrival_time",
                    "",
                ),
            ),
        )

        reason = "Shortest travel time"

    else:

        recommended = min(
            flights,
            key=lambda f: (
                f.get(
                    "fare",
                    {},
                ).get(
                    "total_fare",
                    float("inf"),
                ),
                parse_time(
                    f.get(
                        "departure_time"
                    )
                )
                or datetime.max,
            ),
        )

        reason = (
            "Best overall option based on "
            "fare and departure time"
        )

    logger.info(
        "⭐ [RECOMMENDATION] Preference='%s' | "
        "Flight=%s | Reason=%s",
        preference,
        recommended.get(
            "flight_id"
        ),
        reason,
    )

    return recommended, reason


# ============================================================
# FORMAT FLIGHT RESPONSE
# ============================================================

def format_flight_response(
    request_data: FlightSearchRequest,
    flights: list,
    recommended_flight: Optional[dict],
    recommendation_reason: Optional[str],
) -> str:
    """
    Format flight search results.
    """

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

    if not flights:

        return (
            f"✈️ No flights were found from "
            f"{origin} to {destination} on "
            f"{date_display} for "
            f"{total_seats} passenger(s)."
        )

    lines = [
        "✈️ Flight Options",
        "",
        f"{origin} → {destination}",
        f"Date: {date_display}",
        f"Passengers: {total_seats}",
        f"Class: {travel_class}",
        "",
        "| Airline | Flight | Class | Departure | Arrival | Seats | Fare |",
        "|---|---|---|---|---|---:|---:|",
    ]

    for flight in flights:

        fare = flight.get(
            "fare",
            {},
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

    if recommended_flight:

        fare = recommended_flight.get(
            "fare",
            {},
        )

        total_fare = fare.get(
            "total_fare"
        )

        fare_display = (
            f"₹{total_fare:,.0f}"
            if total_fare is not None
            else "N/A"
        )

        lines.extend(
            [
                "",
                "🤖 Recommended Flight",
                (
                    f"{recommended_flight.get('airline', 'N/A')} "
                    f"{recommended_flight.get('flight_id', 'N/A')}"
                ),
                f"Reason: {recommendation_reason}",
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
                f"Total Fare: {fare_display}",
            ]
        )

    return "\n".join(lines)


# ============================================================
# MAIN AGENT EXECUTOR
# ============================================================

async def execute_agent_request(
    user_request: str,
    context_user_id: Optional[int] = None,
) -> dict:
    """
    Main Flight Booking AI Agent execution flow:

    1. LLM decides intent and tool.
    2. Python validates parameters.
    3. MCP tool is executed.
    4. Response is formatted.
    """

    logger.info("=" * 70)

    logger.info(
        "🤖 [AI AGENT INVOCATION] Request: \"%s\"",
        user_request,
    )

    # ========================================================
    # STEP 1: LLM DECISION
    # ========================================================

    try:

        decision = await decide_tool(
            user_request
        )

    except Exception as exc:

        logger.exception(
            "❌ [AI AGENT FAILED] Tool decision error."
        )

        logger.info("=" * 70)

        return {
            "user_request": user_request,
            "status": "error",
            "message": str(exc),
        }

    # ========================================================
    # STEP 2: PYTHON VALIDATION
    # ========================================================

    validated_params, validation_error = (
        validate_agent_decision(
            decision,
            context_user_id=context_user_id,
        )
    )

    if validation_error:

        logger.info(
            "🛑 [VALIDATION STOP] %s",
            validation_error.get(
                "message"
            ),
        )

        logger.info("=" * 70)

        return {
            "user_request": user_request,
            "intent": decision.intent,
            "tool": decision.tool,
            **validation_error,
        }

    # ========================================================
    # STEP 3: MCP TOOL DISPATCH
    # ========================================================

    tool_name = decision.tool

    tool_function = TOOL_MAP.get(
        tool_name
    )

    if not tool_function:

        logger.error(
            "❌ [DISPATCH ERROR] Tool '%s' has no handler.",
            tool_name,
        )

        logger.info("=" * 70)

        return {
            "user_request": user_request,
            "status": "validation_error",
            "message": (
                f"Tool '{tool_name}' is not supported."
            ),
        }

    logger.info(
        "🚀 [MCP DISPATCH] Tool='%s' Params=%s",
        tool_name,
        validated_params,
    )

    # ========================================================
    # SEARCH FLIGHTS PIPELINE
    # ========================================================

    if tool_name == "search_flights":

        search_req = FlightSearchRequest(
            origin=validated_params[
                "origin"
            ],
            destination=validated_params[
                "destination"
            ],
            date=validated_params[
                "date"
            ],
            total_seats=validated_params[
                "total_seats"
            ],
            travel_class=validated_params[
                "travel_class"
            ],
            max_price=validated_params[
                "max_price"
            ],
            preference=validated_params[
                "preference"
            ],
        )

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        try:

            flights = await fetch_flights_from_mcp(
                search_req
            )

        except RuntimeError as exc:

            logger.info("=" * 70)

            return {
                "user_request": user_request,
                "status": "error",
                "message": str(exc),
            }

        if not flights:

            message = (
                f"No flights found from "
                f"{search_req.origin} to "
                f"{search_req.destination} on "
                f"{format_date_display(search_req.date)}."
            )

            return {
                "user_request": user_request,
                "status": "no_results",
                "search_parameters": (
                    search_req.model_dump()
                ),
                "flights": [],
                "recommended_flight": None,
                "recommendation_reason": None,
                "message": message,
            }

        # ----------------------------------------------------
        # AVAILABILITY
        # ----------------------------------------------------

        try:

            flights = await check_flight_availability(
                flights,
                search_req.total_seats,
            )

        except RuntimeError as exc:

            return {
                "user_request": user_request,
                "status": "error",
                "search_parameters": (
                    search_req.model_dump()
                ),
                "message": str(exc),
            }

        if not flights:

            message = (
                f"No available flights have enough "
                f"seats for {search_req.total_seats} "
                f"passenger(s)."
            )

            return {
                "user_request": user_request,
                "status": "no_availability",
                "search_parameters": (
                    search_req.model_dump()
                ),
                "flights": [],
                "recommended_flight": None,
                "recommendation_reason": None,
                "message": message,
            }

        # ----------------------------------------------------
        # FARES
        # ----------------------------------------------------

        try:

            flights = await fetch_fares(
                flights,
                search_req,
            )

        except RuntimeError as exc:

            return {
                "user_request": user_request,
                "status": "error",
                "search_parameters": (
                    search_req.model_dump()
                ),
                "message": str(exc),
            }

        # ----------------------------------------------------
        # RECOMMENDATION
        # ----------------------------------------------------

        recommended_flight, recommendation_reason = (
            select_recommendation(
                flights,
                search_req.preference,
            )
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        message = format_flight_response(
            search_req,
            flights,
            recommended_flight,
            recommendation_reason,
        )

        logger.info(
            "✨ [COMPLETION] Flight search completed. "
            "Found %d valid flights.",
            len(flights),
        )

        logger.info("=" * 70)

        return {
            "user_request": user_request,
            "status": "success",
            "intent": decision.intent,
            "tool": decision.tool,
            "search_parameters": (
                search_req.model_dump()
            ),
            "flights": flights,
            "recommended_flight": recommended_flight,
            "recommendation_reason": (
                recommendation_reason
            ),
            "message": message,
        }

    # ========================================================
    # OTHER MCP TOOLS
    # ========================================================

    try:

        mcp_result = await tool_function(
            **validated_params
        )

        result_data = parse_mcp_result(
            mcp_result
        )

    except Exception as exc:

        logger.exception(
            "❌ [MCP EXECUTION ERROR] Tool '%s' failed.",
            tool_name,
        )

        logger.info("=" * 70)

        return {
            "user_request": user_request,
            "status": "error",
            "intent": decision.intent,
            "tool": tool_name,
            "message": (
                f"MCP execution failed: {str(exc)}"
            ),
        }

    # ========================================================
    # MCP PAYLOAD
    # ========================================================

    payload = (
        result_data[0]
        if result_data
        else {}
    )

    logger.info(
        "📥 [MCP RAW RESULT] %s",
        payload,
    )

    # ========================================================
    # MCP ERROR
    # ========================================================

    if (
        isinstance(payload, dict)
        and payload.get("error")
    ):

        logger.warning(
            "⚠️ [MCP RETURNED ERROR] %s",
            payload.get("error"),
        )

        return {
            "user_request": user_request,
            "status": "error",
            "intent": decision.intent,
            "tool": tool_name,
            "data": payload,
            "message": payload.get(
                "message",
                payload.get("error"),
            ),
        }

    # ========================================================
    # RESPONSE FORMATTING
    # ========================================================

    if tool_name == "get_flight_details":

        msg = (
            f"✈️ Flight Details for "
            f"{payload.get('flight_id', 'N/A')} "
            f"({payload.get('airline', 'N/A')}):\n"
            f"• Route: "
            f"{payload.get('origin', 'N/A')} → "
            f"{payload.get('destination', 'N/A')}\n"
            f"• Date: "
            f"{format_date_display(str(payload.get('date', '')))}\n"
            f"• Time: "
            f"{payload.get('departure_time', 'N/A')} - "
            f"{payload.get('arrival_time', 'N/A')}\n"
            f"• Travel Class: "
            f"{payload.get('travel_class', 'N/A')}\n"
            f"• Available Seats: "
            f"{payload.get('available_seats', 0)}\n"
            f"• Base Price: "
            f"₹{payload.get('price', 0):,.0f}"
        )

    elif tool_name == "check_availability":

        available = payload.get(
            "available",
            False,
        )

        status_str = (
            "Available"
            if available
            else "Not Available"
        )

        msg = (
            f"💺 Seat Availability for Flight "
            f"{payload.get('flight_id', 'N/A')}:\n"
            f"• Status: {status_str}\n"
            f"• Requested Seats: "
            f"{payload.get('requested_seats', 1)}\n"
            f"• Available Seats: "
            f"{payload.get('available_seats', 0)}"
        )

    elif tool_name == "get_fare":

        msg = (
            f"💳 Fare Quote for Flight "
            f"{payload.get('flight_id', 'N/A')} "
            f"({payload.get('travel_class', 'Economy')}):\n"
            f"• Seats: "
            f"{payload.get('total_seats', 1)}\n"
            f"• Base Fare: "
            f"₹{payload.get('base_fare', 0):,.0f}\n"
            f"• Taxes (5%): "
            f"₹{payload.get('tax', 0):,.0f}\n"
            f"• Service Fee: "
            f"₹{payload.get('service_fee', 0):,.0f}\n"
            f"• Total Fare: "
            f"₹{payload.get('total_fare', 0):,.0f}"
        )

    elif tool_name == "create_booking":

        msg = (
            "🎉 Booking Confirmed!\n"
            f"• Booking Reference: "
            f"{payload.get('booking_reference', 'N/A')}\n"
            f"• Booking ID: "
            f"{payload.get('booking_id', 'N/A')}\n"
            f"• Flight ID: "
            f"{payload.get('flight_id', 'N/A')}\n"
            f"• Seats: "
            f"{payload.get('number_of_seats', 1)}\n"
            f"• Total Price: "
            f"₹{payload.get('total_price', 0):,.0f}\n"
            f"• Status: "
            f"{payload.get('status', 'CONFIRMED')}"
        )

    elif tool_name == "get_booking":

        msg = (
            f"🎫 Booking Details for #"
            f"{payload.get('id', payload.get('booking_id', 'N/A'))}:\n"
            f"• Reference: "
            f"{payload.get('booking_reference', 'N/A')}\n"
            f"• Flight ID: "
            f"{payload.get('flight_id', 'N/A')}\n"
            f"• Seats: "
            f"{payload.get('number_of_seats', 1)}\n"
            f"• Total Price: "
            f"₹{payload.get('total_price', 0):,.0f}\n"
            f"• Status: "
            f"{payload.get('status', 'N/A')}"
        )

    elif tool_name == "cancel_booking":

        msg = (
            f"🚫 Booking #"
            f"{payload.get('booking_id', 'N/A')} "
            "has been successfully cancelled.\n"
            f"• Status: "
            f"{payload.get('status', 'CANCELLED')}\n"
            f"• Seats Released: "
            f"{payload.get('seats_released', payload.get('number_of_seats', 'N/A'))}"
        )

    elif tool_name == "change_booking":

        msg = (
            f"🔄 Booking #"
            f"{payload.get('booking_id', 'N/A')} "
            "updated successfully:\n"
            f"• New Flight: "
            f"{payload.get('flight_id', 'N/A')}\n"
            f"• New Seats: "
            f"{payload.get('number_of_seats', 'N/A')}\n"
            f"• Updated Total: "
            f"₹{payload.get('total_price', 0):,.0f}\n"
            f"• Status: "
            f"{payload.get('status', 'CONFIRMED')}"
        )

    else:

        msg = (
            f"Operation {tool_name} "
            "completed successfully."
        )

    logger.info(
        "✨ [COMPLETION] Tool '%s' executed successfully.",
        tool_name,
    )

    logger.info("=" * 70)

    return {
        "user_request": user_request,
        "status": "success",
        "intent": decision.intent,
        "tool": tool_name,
        "data": payload,
        "message": msg,
    }


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

async def search_flights_with_agent(
    user_request: str,
) -> dict:
    """
    Existing interface wrapper.
    """

    return await execute_agent_request(
        user_request
    )