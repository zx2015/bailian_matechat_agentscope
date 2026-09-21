"""Pydantic models for the Bailian Agent API protocol."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    type: str = "text"
    text: str


class Message(BaseModel):
    role: str
    content: List[TextContent]


class ProcessRequest(BaseModel):
    input: List[Message]
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class Reference(BaseModel):
    """A knowledge base source document that contributed to the answer."""

    source: str
    score: float


class ProcessResponse(BaseModel):
    output: List[Message]
    session_id: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    references: Optional[List[Reference]] = None