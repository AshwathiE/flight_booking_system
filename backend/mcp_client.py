import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


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

    async with streamable_http_client(MCP_SERVER_URL) as (
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

    async with streamable_http_client(MCP_SERVER_URL) as (
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

    async with streamable_http_client(MCP_SERVER_URL) as (
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

    async with streamable_http_client(MCP_SERVER_URL) as (
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
# TEST MCP CONNECTION
# ---------------------------------------------------------

async def test_mcp_connection():

    print("Connecting to Flight MCP Server...")

    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            print("Connected successfully!")

            tools_result = await session.list_tools()

            print("\nAvailable MCP Tools:")

            for tool in tools_result.tools:
                print(f"- {tool.name}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())


# ---------------------------------------------------------
# RUN TEST
# ---------------------------------------------------------
##async def test_search():

  ##  print("\nSearching flights...")

 ##   result = await search_flights_mcp(
  ##      origin="Chennai",
  ##      destination="Delhi",
  ##      date="2026-08-20",
  ##      total_seats=2,
  ##      travel_class="Economy"
  ##  )

  ##  print("\nSearch Result:")

  ##  for content in result.content:
  ##      if hasattr(content, "text"):
  ##          print(content.text)


##if __name__ == "__main__":
    ##asyncio.run(test_search())


##async def test_check_availability():

  ##  print("\nChecking seat availability...")

  ##  result = await check_availability_mcp(
  ##      flight_id="6E202",
  ##      total_seats=100
  ##  )

  ##  print("\nAvailability Result:")

  ##  for content in result.content:
  ##      if hasattr(content, "text"):
  ##          print(content.text)


##if __name__ == "__main__":
   ## asyncio.run(test_check_availability())



async def test_get_fare():

    print("\nCalculating fare...")

    result = await get_fare_mcp(
        flight_id="6E202",
        total_seats=2,
        travel_class="Economy"
    )

    print("\nFare Result:")

    for content in result.content:
        if hasattr(content, "text"):
            print(content.text)


if __name__ == "__main__":
    asyncio.run(test_get_fare())


async def test_search():

    print("\nTesting flight search...")

    result = await search_flights_mcp(
        origin="Chennai",
        destination="Delhi",
        date="2026-08-20",
        total_seats=2,
        travel_class="Economy"
    )

    print("\nMCP Search Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_search())