from typing import List, Optional

from pydantic import BaseModel


class CodeFile(BaseModel):
    filename: str
    content: str


class AgentRequest(BaseModel):
    session_id: str
    message: str
    code: Optional[str] = None
    files: Optional[List[CodeFile]] = None


class AgentResponse(BaseModel):
    requirements_complete: bool
    clarifying_question: Optional[str] = None
    retrieved_context: List[str] = []
    plan: Optional[dict] = None
    review: Optional[dict] = None


class ReviewRequest(BaseModel):
    code: Optional[str] = None
    files: Optional[List[CodeFile]] = None


class ReviewResponse(BaseModel):
    review: dict
