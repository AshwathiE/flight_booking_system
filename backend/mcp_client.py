import os
import asyncio
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger("mcp_client")

FLIGHT_MCP_SERVER_URL = os.getenv("FLIGHT_MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
BOOKING_MCP_SERVER_URL = os.getenv("BOOKING_MCP_SERVER_URL", "http://127.0.0.1:8002/mcp")
PAYMENT_MCP_SERVER_URL = os.getenv("PAYMENT_MCP_SERVER_URL", "http://127.0.0.1:8003/mcp")

MCP_SERVERS = {
    "flight":  FLIGHT_MCP_SERVER_URL,
    "booking": BOOKING_MCP_SERVER_URL,
    "payment": PAYMENT_MCP_SERVER_URL,
}


# ---------------------------------------------------------
# SEARCH FLIGHTS THROUGH MCP
# ---------------------------------------------------------

async def search_flights_mcp(
    origin: str,
    destination: str,
    date: str,
    total_seats: int,
    travel_class: str,
    max_price: float | None = None
):

    async with streamable_http_client(FLIGHT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "search_flights",
                arguments={
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "total_seats": total_seats,
                    "travel_class": travel_class,
                    "max_price": max_price,
                },
            )

            return result


# ---------------------------------------------------------
# GET FLIGHT DETAILS THROUGH MCP
# ---------------------------------------------------------

async def get_flight_details_mcp(flight_id: str):

    async with streamable_http_client(FLIGHT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_flight_details",
                arguments={
                    "flight_id": flight_id
                },
            )

            return result

# ---------------------------------------------------------
# CHECK AVAILABILITY THROUGH MCP
# ---------------------------------------------------------

async def check_availability_mcp(
    flight_id: str,
    total_seats: int = 1
):

    async with streamable_http_client(FLIGHT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "check_availability",
                arguments={
                    "flight_id": flight_id,
                    "total_seats": total_seats
                },
            )

            return result


# ---------------------------------------------------------
# GET FARE THROUGH MCP
# ---------------------------------------------------------

async def get_fare_mcp(
    flight_id: str,
    total_seats: int = 1,
    travel_class: str = "Economy"
):

    async with streamable_http_client(FLIGHT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_fare",
                arguments={
                    "flight_id": flight_id,
                    "total_seats": total_seats,
                    "travel_class": travel_class
                },
            )

            return result


# ---------------------------------------------------------
# CREATE BOOKING THROUGH MCP
# ---------------------------------------------------------

async def create_booking_mcp(
    user_id: int,
    flight_id: str,
    number_of_seats: int = 1
):
    async with streamable_http_client(BOOKING_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                "create_booking",
                arguments={
                    "user_id": user_id,
                    "flight_id": flight_id,
                    "number_of_seats": number_of_seats,
                },
            )
            return result


# ---------------------------------------------------------
# GET BOOKING THROUGH MCP
# ---------------------------------------------------------

async def get_booking_mcp(
    booking_id: int,
    user_id: int | None = None
):
    async with streamable_http_client(BOOKING_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            arguments = {"booking_id": booking_id}
            if user_id is not None:
                arguments["user_id"] = user_id

            result = await session.call_tool(
                "get_booking",
                arguments=arguments,
            )
            return result


# ---------------------------------------------------------
# GET USER BOOKINGS THROUGH MCP
# ---------------------------------------------------------

async def get_user_bookings_mcp(
    user_id: int
):
    async with streamable_http_client(BOOKING_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                "get_user_bookings",
                arguments={
                    "user_id": user_id
                },
            )
            return result


# ---------------------------------------------------------
# CANCEL BOOKING THROUGH MCP
# ---------------------------------------------------------

async def cancel_booking_mcp(
    booking_id: int,
    user_id: int
):
    async with streamable_http_client(BOOKING_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                "cancel_booking",
                arguments={
                    "booking_id": booking_id,
                    "user_id": user_id
                },
            )
            return result


# ---------------------------------------------------------
# CHANGE BOOKING THROUGH MCP
# ---------------------------------------------------------

async def change_booking_mcp(
    booking_id: int,
    user_id: int,
    new_flight_id: str,
    new_number_of_seats: int
):
    async with streamable_http_client(BOOKING_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                "change_booking",
                arguments={
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "new_flight_id": new_flight_id,
                    "new_number_of_seats": new_number_of_seats
                },
            )
            return result

# ---------------------------------------------------------
# PAYMENT MCP FUNCTIONS
# ---------------------------------------------------------

async def create_payment_mcp(
    booking_id: int,
    user_id: int,
    payment_method: str = "MOCK",
):
    """
    Create a pending payment through the Payment MCP Server.

    IMPORTANT:
    Amount and currency are NOT supplied by the client.
    The PaymentService obtains the amount from
    Booking.total_price in the database.
    """

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "create_payment",
                arguments={
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "payment_method": payment_method,
                },
            )

            return result


async def process_payment_mcp(
    payment_id: str,
    user_id: int,
    success: bool = True,
):
    """
    Process a pending payment through the Payment MCP Server.
    """

    if not payment_id:
        raise ValueError(
            "payment_id is required to process payment."
        )

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "process_payment",
                arguments={
                    "payment_id": payment_id,
                    "user_id": user_id,
                    "success": success,
                },
            )

            return result


async def verify_payment_mcp(
    payment_id: str,
    user_id: int,
):
    """
    Verify payment status through the Payment MCP Server.
    """

    if not payment_id:
        raise ValueError(
            "payment_id is required to verify payment."
        )

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "verify_payment",
                arguments={
                    "payment_id": payment_id,
                    "user_id": user_id,
                },
            )

            return result


async def get_payment_mcp(
    payment_id: str,
    user_id: int,
):
    """
    Retrieve a specific payment.
    """

    if not payment_id:
        raise ValueError(
            "payment_id is required to retrieve payment."
        )

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_payment",
                arguments={
                    "payment_id": payment_id,
                    "user_id": user_id,
                },
            )

            return result


async def get_payment_by_booking_mcp(
    booking_id: int,
    user_id: int,
):
    """
    Retrieve payment information using booking ID.
    """

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_payment_by_booking",
                arguments={
                    "booking_id": booking_id,
                    "user_id": user_id,
                },
            )

            return result


async def refund_payment_mcp(
    payment_id: str,
    user_id: int,
):
    """
    Refund a successful payment.

    The Payment MCP Server does not currently accept
    a refund reason.
    """

    if not payment_id:
        raise ValueError(
            "payment_id is required to refund payment."
        )

    async with streamable_http_client(PAYMENT_MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "refund_payment",
                arguments={
                    "payment_id": payment_id,
                    "user_id": user_id,
                },
            )

            return result

# ---------------------------------------------------------
# MCP TOOL DISCOVERY & VALIDATION
# ---------------------------------------------------------

async def discover_server_tools(server_url: str) -> list[str]:
    """
    Connect to an MCP server at given URL and discover its registered tools.
    """
    async with streamable_http_client(server_url) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return [tool.name for tool in tools_result.tools]


async def discover_payment_tools() -> list[str]:
    """
    Discover tools available on the Payment MCP Server.
    """
    return await discover_server_tools(PAYMENT_MCP_SERVER_URL)


async def discover_flight_tools() -> list[str]:
    """
    Discover tools available on the Flight MCP Server.
    """
    return await discover_server_tools(FLIGHT_MCP_SERVER_URL)


async def discover_booking_tools() -> list[str]:
    """
    Discover tools available on the Booking MCP Server.
    """
    return await discover_server_tools(BOOKING_MCP_SERVER_URL)


async def discover_all_tools() -> dict[str, list[str]]:
    """
    Discover all tools across Flight, Booking, and Payment MCP servers.
    """
    results = {}
    for name, url in MCP_SERVERS.items():
        try:
            tools = await discover_server_tools(url)
            results[name] = tools
        except Exception as exc:
            logger.error("Failed to discover tools for %s server: %s", name, exc)
            results[name] = []
    return results


# ---------------------------------------------------------
# TEST MCP CONNECTION
# ---------------------------------------------------------

async def test_mcp_connection():
    print(f"Connecting to Flight MCP Server at {FLIGHT_MCP_SERVER_URL}...")
    try:
        tools = await discover_flight_tools()
        print("Connected to Flight MCP Server successfully!")
        print("Flight MCP tools discovered:")
        for tool in tools:
            print(f"- {tool}")
    except Exception as exc:
        print(f"Failed to connect to Flight MCP Server: {exc}")


async def test_payment_mcp_connection():
    print(f"Connecting to Payment MCP Server at {PAYMENT_MCP_SERVER_URL}...")
    try:
        tools = await discover_payment_tools()
        print("Connected to Payment MCP Server successfully!")
        print("Payment MCP tools discovered:")
        for tool in tools:
            print(f"- {tool}")
    except Exception as exc:
        print(f"Failed to connect to Payment MCP Server: {exc}")


async def test_all_mcp_connections():
    print("=" * 60)
    print("Testing connections to all MCP servers...")
    print("=" * 60)
    for name, url in MCP_SERVERS.items():
        print(f"\nConnecting to {name.capitalize()} MCP Server at {url}...")
        try:
            tools = await discover_server_tools(url)
            print(f"Connected to {name.capitalize()} MCP Server successfully!")
            print(f"{name.capitalize()} MCP tools discovered:")
            for tool in tools:
                print(f"- {tool}")
        except Exception as exc:
            print(f"Failed to connect to {name.capitalize()} MCP Server: {exc}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_mcp_connections())
