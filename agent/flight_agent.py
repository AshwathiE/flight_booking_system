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
    create_payment_mcp,
    process_payment_mcp,
    verify_payment_mcp,
    get_payment_mcp,
    get_payment_by_booking_mcp,
    refund_payment_mcp,
    discover_payment_tools,
    discover_flight_tools,
    discover_booking_tools,
    discover_all_tools,
    PAYMENT_MCP_SERVER_URL,
    MCP_SERVERS,
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
# MCP STARTUP VALIDATION
# ============================================================
async def validate_payment_mcp_startup() -> bool:
    """
    Validate Payment MCP Server connection and discover its tools.
    """
    logger.info("Connecting to Payment MCP Server at %s...", PAYMENT_MCP_SERVER_URL)
    try:
        tools = await discover_payment_tools()
        logger.info("Connected to Payment MCP Server successfully!")
        logger.info("Payment MCP tools discovered:")
        for tool in tools:
            logger.info("  - %s", tool)
        return True
    except Exception as exc:
        logger.error("❌ Failed to connect to Payment MCP Server: %s", exc)
        return False
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
    "create_payment",
    "process_payment",
    "verify_payment",
    "get_payment",
    "get_payment_by_booking",
    "refund_payment",
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
    "create_payment": create_payment_mcp,
    "process_payment": process_payment_mcp,
    "verify_payment": verify_payment_mcp,
    "get_payment": get_payment_mcp,
    "get_payment_by_booking": get_payment_by_booking_mcp,
    "refund_payment": refund_payment_mcp,
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
        "CREATE_PAYMENT",
        "PROCESS_PAYMENT",
        "VERIFY_PAYMENT",
        "GET_PAYMENT",
        "GET_PAYMENT_BY_BOOKING",
        "REFUND_PAYMENT",
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
Your job is to understand the user's request and select exactly ONE
appropriate tool.
Never access the database directly.
Never generate SQL.
Never invent booking IDs, payment IDs, prices, payment status,
transaction IDs, or flight information.
MCP tool results are the source of truth.
AVAILABLE TOOLS
Flight:
- search_flights
- get_flight_details
- check_availability
- get_fare
Booking:
- create_booking
- get_booking
- get_user_bookings
- cancel_booking
- change_booking
Payment:
- create_payment
- process_payment
- verify_payment
- get_payment
- get_payment_by_booking
- refund_payment
INTENTS
SEARCH_FLIGHTS
GET_FLIGHT_DETAILS
CHECK_AVAILABILITY
GET_FARE
CREATE_BOOKING
GET_BOOKING
GET_USER_BOOKINGS
CANCEL_BOOKING
CHANGE_BOOKING
CREATE_PAYMENT
PROCESS_PAYMENT
VERIFY_PAYMENT
GET_PAYMENT
GET_PAYMENT_BY_BOOKING
REFUND_PAYMENT
UNKNOWN
CURRENT DATE
Today is {CURRENT_DATE}.
Use this date when interpreting relative dates such as:
- today
- tomorrow
- day after tomorrow
- next Monday
- this weekend
Never select or return flights from the past.
IMPORTANT PAYMENT RULES
1. The user never provides the payment amount.
2. Never generate an amount.
3. The payment amount must always come from the booking's
   total_price through the Payment MCP Server.
4. The user may choose:
   - UPI
   - CARD
   - NET_BANKING

5. When the user says:
   "pay for booking 65 using card"
    return:
   {{
     "intent": "CREATE_PAYMENT",
     "tool": "create_payment",
     "parameters": {{
       "booking_id": 65,
       "payment_method": "CARD"
     }}
   }}
6. When the user says:
   "pay for booking 65"
   return:
   {{
     "intent": "CREATE_PAYMENT",
     "tool": "create_payment",
     "parameters": {{
       "booking_id": 65
     }}
   }}
7. When the user says:
   "pay using card"
   return:
   {{
     "intent": "CREATE_PAYMENT",
     "tool": "create_payment",
     "parameters": {{
       "payment_method": "CARD"
     }}
   }}

8. Never generate a payment_id.

9. Never generate a transaction_id.

10. Never generate a refund_id.

11. Never generate a payment amount.

12. Never claim that payment succeeded unless the Payment MCP Server
    returns a successful payment result.

13. If create_payment returns a payment_id, that payment_id must come
    from the MCP Server.

14. process_payment must use a payment_id returned by the MCP Server
    or explicitly provided by the user.

15. Never invent a payment_id.

16. A ticket must NEVER be offered as downloadable before payment
    succeeds.

17. A booking created by create_booking initially has:

    status = PENDING_PAYMENT
    payment_status = PENDING

18. Payment flow is:

    CREATE_BOOKING
          ↓
    PENDING_PAYMENT
          ↓
    CREATE_PAYMENT
          ↓
    PROCESS_PAYMENT
          ↓
    SUCCESS
          ↓
    CONFIRMED
          ↓
    TICKET_AVAILABLE

19. If payment fails:

    PAYMENT_FAILED
          ↓
    booking remains PENDING_PAYMENT
          ↓
    ticket remains NOT_AVAILABLE

20. Refund is allowed only for successful payments.
GENERAL TOOL RULES
1. Select exactly ONE tool.
2. Do not call multiple tools.
3. Do not perform database operations yourself.
4. Do not calculate prices yourself.

5. Do not invent flight information.

6. Do not invent booking information.

7. Do not invent payment information.

8. Use information returned by MCP tools as the source of truth.

9. If required information is missing, do not guess it.

10. If the request cannot be mapped to an available tool, use:

    {{
      "intent": "UNKNOWN",
      "tool": "UNKNOWN",
      "parameters": {{}}
    }}


OUTPUT FORMAT

Return ONLY valid JSON.

Do not include:
- Markdown
- ```json
- explanations
- comments
- additional text

The response must have exactly this structure:

{{
  "intent": "...",
  "tool": "...",
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
    # CREATE PAYMENT
    # ========================================================

    if decision.tool == "create_payment":
        booking_id = params.get("booking_id")
        amount = params.get("amount")
        currency = params.get("currency", "INR")

        if booking_id:
            try:
                booking_id = int(str(booking_id).replace("BK", "").strip())
            except ValueError:
                return {}, {
                    "status": "validation_error",
                    "field": "booking_id",
                    "message": "Booking ID must be a numeric identifier."
                }
        else:
            booking_id = None

        if amount is not None:
            try:
                amount = float(amount)
                if amount <= 0:
                    return {}, {
                        "status": "validation_error",
                        "field": "amount",
                        "message": "Amount must be greater than 0."
                    }
            except (ValueError, TypeError):
                return {}, {
                    "status": "validation_error",
                    "field": "amount",
                    "message": "Amount must be a valid number."
                }

        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1

        return {
            "booking_id": booking_id,
            "user_id": user_id,
            "amount": amount,
            "currency": str(currency).strip().upper()
        }, None

    # ========================================================
    # PROCESS PAYMENT
    # ========================================================

    if decision.tool == "process_payment":
        payment_id = params.get("payment_id")
        booking_id = params.get("booking_id")
        payment_method = params.get("payment_method")

        if booking_id:
            try:
                booking_id = int(str(booking_id).replace("BK", "").strip())
            except ValueError:
                return {}, {
                    "status": "validation_error",
                    "field": "booking_id",
                    "message": "Booking ID must be a numeric identifier."
                }
        else:
            booking_id = None

        if not payment_method:
            return {}, {
                "status": "needs_information",
                "missing_fields": ["payment_method"],
                "message": "Which payment method would you like to use: UPI, CARD, or NET_BANKING?"
            }

        payment_method_str = str(payment_method).strip().upper()
        base_method = payment_method_str.split('_')[0]
        if base_method not in ["UPI", "CARD", "NET_BANKING"]:
            return {}, {
                "status": "validation_error",
                "field": "payment_method",
                "message": "Invalid payment method. Supported: UPI, CARD, NET_BANKING."
            }

        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1

        return {
            "payment_id": str(payment_id).strip() if payment_id else None,
            "booking_id": booking_id,
            "payment_method": payment_method_str,
            "user_id": user_id
        }, None

    # ========================================================
    # VERIFY PAYMENT
    # ========================================================

    if decision.tool == "verify_payment":
        payment_id = params.get("payment_id")
        booking_id = params.get("booking_id")
        if not payment_id and not booking_id:
            return {}, {
                "status": "needs_information",
                "missing_fields": ["payment_id"],
                "message": "Please provide the payment ID or booking ID to verify."
            }

        if booking_id:
            try:
                booking_id = int(str(booking_id).replace("BK", "").strip())
            except ValueError:
                return {}, {
                    "status": "validation_error",
                    "field": "booking_id",
                    "message": "Booking ID must be a numeric identifier."
                }

        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1

        return {
            "payment_id": str(payment_id).strip() if payment_id else None,
            "booking_id": booking_id,
            "user_id": user_id
        }, None

    # ========================================================
    # GET PAYMENT
    # ========================================================

    if decision.tool == "get_payment":
        payment_id = params.get("payment_id")
        if not payment_id:
            return {}, {
                "status": "needs_information",
                "missing_fields": ["payment_id"],
                "message": "Please provide the payment ID."
            }
        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1
        return {
            "payment_id": str(payment_id).strip(),
            "user_id": user_id
        }, None

    # ========================================================
    # GET PAYMENT BY BOOKING
    # ========================================================

    if decision.tool == "get_payment_by_booking":
        booking_id = params.get("booking_id")
        if not booking_id:
            return {}, {
                "status": "needs_information",
                "missing_fields": ["booking_id"],
                "message": "Please provide the booking ID."
            }
        try:
            booking_id = int(str(booking_id).replace("BK", "").strip())
        except ValueError:
            return {}, {
                "status": "validation_error",
                "field": "booking_id",
                "message": "Booking ID must be a numeric identifier."
            }
        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1
        return {
            "booking_id": booking_id,
            "user_id": user_id
        }, None

    # ========================================================
    # REFUND PAYMENT
    # ========================================================

    if decision.tool == "refund_payment":
        payment_id = params.get("payment_id")
        booking_id = params.get("booking_id")
        reason = params.get("reason", "Customer request")
        if not payment_id and not booking_id:
            return {}, {
                "status": "needs_information",
                "missing_fields": ["payment_id"],
                "message": "Please provide the payment ID or booking ID to refund."
            }
        if booking_id:
            try:
                booking_id = int(str(booking_id).replace("BK", "").strip())
            except ValueError:
                return {}, {
                    "status": "validation_error",
                    "field": "booking_id",
                    "message": "Booking ID must be a numeric identifier."
                }
        user_id = context_user_id or params.get("user_id") or 1
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = 1
        return {
            "payment_id": str(payment_id).strip() if payment_id else None,
            "booking_id": booking_id,
            "reason": str(reason).strip(),
            "user_id": user_id
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

async def resolve_pending_booking_id(user_id: int) -> Optional[int]:
    """
    Find user's pending booking from the Booking MCP.
    Returns:
        booking_id (int) if there is exactly one pending booking.
        None if there are none or multiple pending bookings.
    """
    try:
        res = await get_user_bookings_mcp(user_id=user_id)
        result_data = parse_mcp_result(res)
        if result_data and isinstance(result_data[0], dict) and result_data[0].get("success"):
            bookings = result_data[0].get("bookings", [])
            pending_bookings = [b for b in bookings if b.get("status") == "PENDING_PAYMENT"]
            if len(pending_bookings) == 1:
                return pending_bookings[0].get("booking_id")
    except Exception as exc:
        logger.error("Failed to resolve pending booking ID: %s", exc)
    return None


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
        if tool_name in ["create_payment", "process_payment"]:
            payment_id = validated_params.get("payment_id")
            booking_id = validated_params.get("booking_id")
            payment_method = validated_params.get("payment_method") or "CARD"
            user_id = validated_params.get("user_id", context_user_id or 1)

            if tool_name == "process_payment" and payment_id:
                process_res = await TOOL_MAP["process_payment"](
                    payment_id=payment_id,
                    payment_method=payment_method,
                )
                process_data = parse_mcp_result(process_res)
                payment_data = process_data[0] if process_data else {}
                if not payment_data:
                    return {
                        "user_request": user_request,
                        "status": "error",
                        "intent": decision.intent,
                        "tool": tool_name,
                        "message": "Payment processing returned no result.",
                    }

                payment_status = payment_data.get("status")
                if payment_status == "SUCCESS":
                    message = (
                        f"Payment successful. Payment ID: {payment_id}. "
                        f"Transaction ID: {payment_data.get('transaction_id')}"
                    )
                else:
                    message = (
                        f"Payment failed for {payment_id}: "
                        f"{payment_data.get('failure_reason') or payment_data.get('message') or 'Unknown payment error.'}"
                    )

                return {
                    "user_request": user_request,
                    "status": "success",
                    "intent": decision.intent,
                    "tool": tool_name,
                    "payment_id": payment_id,
                    "data": payment_data,
                    "message": message,
                }

            # Resolve booking_id from context if not provided
            if not booking_id and not payment_id:
                booking_id = await resolve_pending_booking_id(user_id=user_id)
                if not booking_id:
                    # Fetch bookings to see why (none or multiple)
                    res = await TOOL_MAP["get_user_bookings"](user_id=user_id)
                    res_data = parse_mcp_result(res)
                    pending_ids = []
                    if res_data and isinstance(res_data[0], dict) and res_data[0].get("success"):
                        bookings = res_data[0].get("bookings", [])
                        pending_ids = [b.get("booking_id") for b in bookings if b.get("status") == "PENDING_PAYMENT"]
                    
                    if len(pending_ids) > 1:
                        return {
                            "user_request": user_request,
                            "status": "needs_information",
                            "missing_fields": ["booking_id"],
                            "message": f"You have multiple pending bookings: {', '.join(f'BK{bid}' for bid in pending_ids)}. Please specify which booking ID you want to pay for."
                        }
                    else:
                        return {
                            "user_request": user_request,
                            "status": "error",
                            "intent": decision.intent,
                            "tool": tool_name,
                            "message": "You do not have any pending bookings that require payment."
                        }

            # Retrieve booking_id from payment_id if booking_id not given but payment_id is
            if not booking_id and payment_id:
                payment_res = await TOOL_MAP["get_payment"](payment_id=payment_id, user_id=user_id)
                payment_data = parse_mcp_result(payment_res)
                if payment_data and not payment_data[0].get("error"):
                    booking_id = payment_data[0].get("booking_id")

            # Check for existing payment
            payment_payload = None
            if booking_id:
                by_booking_res = await TOOL_MAP["get_payment_by_booking"](booking_id=booking_id, user_id=user_id)
                by_booking_data = parse_mcp_result(by_booking_res)
                if by_booking_data and not by_booking_data[0].get("error"):
                    existing_payment = by_booking_data[0]
                    # If existing payment exists and success, do not create/process another payment
                    if existing_payment.get("status") == "SUCCESS":
                        return {
                            "user_request": user_request,
                            "status": "success",
                            "intent": decision.intent,
                            "tool": tool_name,
                            "data": existing_payment,
                            "message": (
                                f"Payment has already succeeded for booking {booking_id}.\n"
                                f"Payment ID: {existing_payment.get('payment_id')}\n"
                                f"Transaction ID: {existing_payment.get('transaction_id')}\n"
                                f"Amount: ₹{existing_payment.get('amount', 0):,.0f}"
                            ),
                        }
                    # If existing payment is pending/processing, reuse its payment_id
                    elif existing_payment.get("status") in ["PENDING", "PROCESSING"]:
                        payment_id = existing_payment.get("payment_id")
                        payment_payload = existing_payment

            # If no usable payment exists, create a new one
            if not payment_id and booking_id:
                # First let's get the booking to verify it exists and is authorized
                booking_res = await TOOL_MAP["get_booking"](booking_id=booking_id, user_id=user_id)
                booking_data = parse_mcp_result(booking_res)
                if not booking_data or booking_data[0].get("error"):
                    err = booking_data[0] if booking_data else {}
                    err_msg = err.get("message") or err.get("error") or f"Booking {booking_id} not found."
                    return {
                        "user_request": user_request,
                        "status": "error",
                        "intent": decision.intent,
                        "tool": tool_name,
                        "data": err,
                        "message": err_msg,
                    }

                # Now call create_payment MCP
                create_res = await TOOL_MAP["create_payment"](
                    booking_id=booking_id,
                    user_id=user_id,
                    payment_method=payment_method,
                )
                create_data = parse_mcp_result(create_res)
                if not create_data or create_data[0].get("error"):
                    err = create_data[0] if create_data else {}
                    err_msg = err.get("message") or err.get("error") or "Failed to create payment record."
                    return {
                        "user_request": user_request,
                        "status": "error",
                        "intent": decision.intent,
                        "tool": tool_name,
                        "data": err,
                        "message": err_msg,
                    }
                payment_payload = create_data[0]
                payment_id = payment_payload.get("payment_id")

            if not payment_payload:
                return {
                    "user_request": user_request,
                    "status": "error",
                    "intent": decision.intent,
                    "tool": tool_name,
                    "message": "Failed to retrieve or create payment details."
                }

            # We DO NOT call process_payment_mcp here anymore!
            # Instead, return a structured response indicating payment is required.
            amount = payment_payload.get("amount", 0)
            currency = payment_payload.get("currency", "INR")
            method = payment_payload.get("payment_method", payment_method)
            p_status = payment_payload.get("status", "PENDING")
            b_status = payment_payload.get("booking_status", "PENDING_PAYMENT")
            t_status = payment_payload.get("ticket_status", "NOT_AVAILABLE")

            # We format a response that includes redirect info
            msg = (
                f"💳 Booking BK{booking_id} requires payment.\n"
                f"• Payment ID: {payment_id}\n"
                f"• Amount: {currency} {amount:,.2f}\n"
                f"• Payment Method: {method}\n"
                f"• Payment Status: {p_status}\n\n"
                f"Please click 'Proceed to Payment' to complete the transaction."
            )

            return {
                "status": "payment_required",
                "intent": decision.intent,
                "booking_id": booking_id,
                "payment_id": payment_id,
                "amount": amount,
                "currency": currency,
                "payment_method": method,
                "booking_status": b_status,
                "payment_status": p_status,
                "ticket_status": t_status,
                "redirect_to_payment": True,
                "message": msg,
                "data": payment_payload
            }

        elif tool_name == "verify_payment":
            payment_id = validated_params.get("payment_id")
            booking_id = validated_params.get("booking_id")
            user_id = validated_params.get("user_id", context_user_id or 1)

            if not payment_id and booking_id:
                by_booking_res = await TOOL_MAP["get_payment_by_booking"](booking_id=booking_id, user_id=user_id)
                by_booking_data = parse_mcp_result(by_booking_res)
                if by_booking_data and not by_booking_data[0].get("error"):
                    payment_id = by_booking_data[0].get("payment_id")
                else:
                    err = by_booking_data[0] if by_booking_data else {}
                    err_msg = err.get("message") or err.get("error") or f"No payment found for booking {booking_id}."
                    return {
                        "user_request": user_request,
                        "status": "error",
                        "intent": decision.intent,
                        "tool": tool_name,
                        "data": err,
                        "message": err_msg,
                    }

            mcp_result = await TOOL_MAP["verify_payment"](
                payment_id=payment_id,
                 user_id=user_id,
            )

        elif tool_name == "refund_payment":
            payment_id = validated_params.get("payment_id")
            booking_id = validated_params.get("booking_id")
            reason = validated_params.get("reason", "Customer request")
            user_id = validated_params.get("user_id", context_user_id or 1)

            if not payment_id and booking_id:
                by_booking_res = await TOOL_MAP["get_payment_by_booking"](booking_id=booking_id, user_id=user_id)
                by_booking_data = parse_mcp_result(by_booking_res)
                if by_booking_data and not by_booking_data[0].get("error"):
                    payment_id = by_booking_data[0].get("payment_id")
                else:
                    err = by_booking_data[0] if by_booking_data else {}
                    err_msg = err.get("message") or err.get("error") or f"No payment found for booking {booking_id}."
                    return {
                        "user_request": user_request,
                        "status": "error",
                        "intent": decision.intent,
                        "tool": tool_name,
                        "data": err,
                        "message": err_msg,
                    }

            mcp_result = await TOOL_MAP["refund_payment"](
                payment_id=payment_id,
                user_id=user_id
            )

        else:
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
            "message": f"MCP execution failed: {str(exc)}",
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

    if isinstance(payload, dict) and payload.get("error"):
        error_code = payload.get("error", "ERROR")
        error_msg_map = {
            "BOOKING_NOT_FOUND": "The specified booking was not found.",
            "PAYMENT_NOT_FOUND": "Payment record was not found.",
            "UNAUTHORIZED": "You are not authorized to perform this payment action.",
            "INVALID_AMOUNT": "Payment amount does not match the actual booking total.",
            "INVALID_PAYMENT_METHOD": "Invalid payment method. Supported methods are: UPI, CARD, NET_BANKING.",
            "PAYMENT_ALREADY_COMPLETED": "This payment has already been completed successfully.",
            "DUPLICATE_PAYMENT": "A payment for this booking is already in progress or completed.",
            "PAYMENT_NOT_PAID": "Cannot refund a payment that has not succeeded.",
            "PAYMENT_ALREADY_REFUNDED": "This payment has already been refunded.",
            "REFUND_FAILED": "Refund operation failed. Please try again or contact support.",
            "BOOKING_ALREADY_CANCELLED": "Cannot process payment for a cancelled booking.",
        }

        user_friendly_msg = payload.get("message") or error_msg_map.get(error_code) or f"Operation failed ({error_code})."

        logger.warning(
            "⚠️ [MCP RETURNED ERROR] %s: %s",
            error_code,
            user_friendly_msg,
        )

        return {
            "user_request": user_request,
            "status": "error",
            "intent": decision.intent,
            "tool": tool_name,
            "data": payload,
            "message": user_friendly_msg,
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
        available = payload.get("available", False)
        status_str = "Available" if available else "Not Available"
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
        booking_status = payload.get('status', 'PENDING_PAYMENT')
        payment_status = payload.get('payment_status', 'PENDING')
        booking_id_val = payload.get('booking_id', 'N/A')
        msg = (
            "✈️ Booking Created — Payment Required\n"
            f"• Booking Reference: "
            f"{payload.get('booking_reference', 'N/A')}\n"
            f"• Booking ID: {booking_id_val}\n"
            f"• Flight ID: "
            f"{payload.get('flight_id', 'N/A')}\n"
            f"• Seats: "
            f"{payload.get('number_of_seats', 1)}\n"
            f"• Total Price: "
            f"₹{payload.get('total_price', 0):,.0f}\n"
            f"• Booking Status: {booking_status}\n"
            f"• Payment Status: {payment_status}\n\n"
            "Your seats have been reserved. Please complete payment to CONFIRM your booking.\n"
            "To pay, say: \"Pay for booking {booking_id_val} using UPI\" (or CARD/NET_BANKING)."
        )

    elif tool_name == "get_booking":
        bk_status = payload.get('status', 'N/A')
        pay_status = payload.get('payment_status', 'N/A')
        pay_note = ""
        if bk_status == "PENDING_PAYMENT":
            bk_id_v = payload.get('id', payload.get('booking_id', ''))
            pay_note = (
                f"\n\n⚠️ Payment Required: This booking is not yet confirmed.\n"
                f"To pay, say: \"Pay for booking {bk_id_v} using UPI\" (or CARD/NET_BANKING)."
            )
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
            f"• Booking Status: {bk_status}\n"
            f"• Payment Status: {pay_status}"
            f"{pay_note}"
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

    elif tool_name == "create_payment":
        msg = (
            "💳 Payment Created!\n"
            f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
            f"• Booking ID: BK{payload.get('booking_id', 'N/A')}\n"
            f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}\n"
            f"• Status: {payload.get('status', 'PENDING')}\n\n"
            "Which payment method would you like to use: UPI, CARD, or NET_BANKING?"
        )

    elif tool_name == "process_payment":
        status_val = payload.get("status")
        booking_ref = payload.get("booking_id") or validated_params.get("booking_id")
        booking_label = f" for booking {booking_ref}" if booking_ref else ""
        booking_status_val = payload.get("booking_status", "")

        if status_val == "SUCCESS":
            msg = (
                f"Payment successful{booking_label}.\n"
                f"Your booking is now CONFIRMED.\n"
                f"Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"Transaction ID: {payload.get('transaction_id', 'N/A')}\n"
                f"Amount: ₹{payload.get('amount', 0):,.0f}\n"
                f"Booking Status: {payload.get('booking_status', 'CONFIRMED')}"
            )
        elif status_val == "FAILED":
            msg = (
                f"Payment failed{booking_label}.\n"
                f"Your booking remains in PENDING_PAYMENT state. You can retry payment.\n"
                f"Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"Failure Reason: {payload.get('failure_reason', 'Payment was rejected by gateway')}"
            )
        elif status_val == "PENDING":
            msg = (
                f"Payment is pending{booking_label}.\n"
                f"Payment ID: {payload.get('payment_id', 'N/A')}"
            )
        elif status_val == "PROCESSING":
            msg = (
                f"Payment is currently processing{booking_label}.\n"
                f"Payment ID: {payload.get('payment_id', 'N/A')}"
            )
        elif status_val == "REFUNDED":
            msg = f"Payment {payload.get('payment_id', 'N/A')} has been refunded."
        else:
            msg = (
                f"Payment status: {status_val}\n"
                f"Payment ID: {payload.get('payment_id', 'N/A')}"
            )
    elif tool_name == "verify_payment":
        status_val = payload.get("status")
        if status_val == "SUCCESS":
            msg = (
                "🔍 Payment Verification: SUCCESS\n"
                f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"• Booking ID: BK{payload.get('booking_id', 'N/A')}\n"
                f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}\n"
                f"• Transaction ID: {payload.get('transaction_id', 'N/A')}\n"
                f"• Method: {payload.get('payment_method', 'N/A')}"
            )
        elif status_val == "FAILED":
            msg = (
                "🔍 Payment Verification: FAILED\n"
                f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"• Failure Reason: {payload.get('failure_reason', 'Payment failed')}"
            )
        elif status_val == "PENDING":
            msg = (
                "🔍 Payment Verification: PENDING\n"
                f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}\n"
                f"• Payment is awaiting processing."
            )
        elif status_val == "REFUNDED":
            msg = (
                "🔍 Payment Verification: REFUNDED\n"
                f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"• Refund ID: {payload.get('refund_id', 'N/A')}\n"
                f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}"
            )
        else:
            msg = (
                f"🔍 Payment Verification: {status_val}\n"
                f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
                f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}"
            )

    elif tool_name in ["get_payment", "get_payment_by_booking"]:
        msg = (
            "📄 Payment Details:\n"
            f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
            f"• Booking ID: BK{payload.get('booking_id', 'N/A')}\n"
            f"• Amount: {payload.get('currency', 'INR')} {payload.get('amount', 0):,.2f}\n"
            f"• Status: {payload.get('status', 'N/A')}\n"
            f"• Method: {payload.get('payment_method', 'N/A')}\n"
            f"• Transaction ID: {payload.get('transaction_id', 'N/A') or 'None'}"
        )
    elif tool_name == "refund_payment":
        msg = (
            "💵 Refund Processed Successfully:\n"
            f"• Payment ID: {payload.get('payment_id', 'N/A')}\n"
            f"• Booking ID: BK{payload.get('booking_id', 'N/A')}\n"
            f"• Refund ID: {payload.get('refund_id', 'N/A')}\n"
            f"• Amount: ₹{payload.get('amount', 0):,.2f}\n"
            f"• Status: REFUNDED\n"
            f"• The corresponding booking has been cancelled and seats released."
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
# CHAT / TICKET HELPERS
# ============================================================

import re
from typing import Optional


def is_ticket_intent(message: str) -> bool:
    """Return True when the user is asking for a ticket."""

    if not message:
        return False

    text = message.strip().lower()

    patterns = [
        r"\bdownload\b.*\bticket\b",
        r"\bgive me\b.*\bticket\b",
        r"\bmy ticket\b",
        r"\bticket\b.*\bpdf\b",
        r"\bpdf\b.*\bticket\b",
        r"\bshow\b.*\bticket\b",
        r"\bview\b.*\bticket\b",
        r"\bget\b.*\bticket\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def extract_booking_reference(message: str) -> Optional[str]:
    """Extract booking reference such as BK2026001."""

    if not message:
        return None

    match = re.search(
        r"\b(BK\d+)\b",
        message.upper(),
    )

    return match.group(1) if match else None


def extract_booking_id(message: str) -> Optional[int]:
    """Extract numeric booking ID from 'booking 12' or 'booking #12'."""

    if not message:
        return None

    match = re.search(
        r"\bbooking\s*#?\s*(\d+)\b",
        message,
        re.IGNORECASE,
    )

    if match:
        return int(match.group(1))

    return None
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