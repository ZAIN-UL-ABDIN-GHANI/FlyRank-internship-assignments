from typing import List, Literal, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AgentRequest(BaseModel):
    history: List[Message]
    code: Optional[str] = None


class AgentResponse(BaseModel):
    requirements_complete: bool
    clarifying_question: Optional[str] = None
    retrieved_context: List[str] = []
    plan: Optional[dict] = None
    review: Optional[dict] = None
