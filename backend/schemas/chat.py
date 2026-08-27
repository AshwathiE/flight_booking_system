from typing import Any, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    type: str = "text"
    data: Optional[Any] = None
    conversation_id: Optional[str] = None