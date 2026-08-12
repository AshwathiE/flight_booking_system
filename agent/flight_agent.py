import os
import json
import re
import logging
logger = logging.getLogger(__name__)
from groq import Groq
from dotenv import load_dotenv

from backend.mcp_client import search_flights_mcp

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

SYSTEM_PROMPT = """
You are a flight booking assistant.

Extract flight search information from the user's request.

You MUST return ONLY a JSON object.

DO NOT use Markdown.
DO NOT use ```json.
DO NOT add explanations.
DO NOT add any text before or after the JSON.

The JSON must have exactly these fields:

{
    "origin": "string",
    "destination": "string",
    "date": "YYYY-MM-DD",
    "total_seats": 1,
    "travel_class": "Economy",
    "max_price": null
}

Rules:

- total_seats means the number of seats requested by the user.
- available_seats is NOT a user input.
- available_seats comes from PostgreSQL.
- If travel class is not specified, use "Economy".
- If maximum price is not specified, use null.
- Convert dates to YYYY-MM-DD. If date is not specified by the user, use "2026-08-15".
"""


def parse_json_safely(text: str):
    if not text or not text.strip():
        raise ValueError("Empty response text received from LLM")

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove markdown code fences like ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # Search for embedded JSON object in text
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from text: {text!r}")


async def understand_flight_request(user_request: str):

    logger.info("Understanding user flight request")
    logger.debug("User request sent to LLM: %s", user_request)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_request
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    logger.info("LLM response received")

    request_data = parse_json_safely(content)

    logger.info("Flight request successfully parsed")
    logger.debug("Parsed request: %s", request_data)

    return request_data



async def search_flights_with_agent(user_request: str):

    logger.info("Flight search agent started")
    logger.debug("User request: %s", user_request)

    # Step 1: Understand the user's request using the LLM
    request_data = await understand_flight_request(user_request)

    logger.info("User request successfully understood by AI")
    logger.debug("Extracted flight request: %s", request_data)

    # Step 2: Extract flight search parameters
    origin = request_data.get("origin") or ""
    destination = request_data.get("destination") or ""
    date = request_data.get("date") or ""
    total_seats = request_data.get("total_seats") or 1
    travel_class = request_data.get("travel_class") or "Economy"
    max_price = request_data.get("max_price")

    logger.info(
        "Flight search parameters extracted: "
        "origin=%s, destination=%s, date=%s, seats=%s, class=%s",
        origin,
        destination,
        date,
        total_seats,
        travel_class
    )

    # Step 3: Call the Flight MCP tool
    logger.info("Calling flight search MCP tool")

    result = await search_flights_mcp(
        origin=origin,
        destination=destination,
        date=date,
        total_seats=total_seats,
        travel_class=travel_class,
        max_price=max_price
    )

    logger.info("Flight search MCP tool completed successfully")
    logger.debug("MCP result received: %s", result)

    # Step 4: Return MCP result to the AI endpoint
    logger.info("Returning flight search result from agent")

    return result