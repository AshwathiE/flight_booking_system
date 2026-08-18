from fastapi import APIRouter
from pydantic import BaseModel

from agent.flight_agent import search_flights_with_agent, execute_agent_request

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


class AIFlightSearchRequest(BaseModel):
    message: str


@router.post("/search_flights")
async def ai_search_flights(
    request: AIFlightSearchRequest
):
    result = await search_flights_with_agent(
        request.message
    )

    return result


@router.post("/agent")
async def ai_agent_endpoint(
    request: AIFlightSearchRequest
):
    result = await execute_agent_request(
        request.message
    )

    return result