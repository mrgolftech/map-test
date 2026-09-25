from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=240)
    label: str = Field(min_length=1, max_length=240)
    value: str = Field(min_length=1, max_length=500)
    analysis_id: str | None = None


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[ChatCitation] = Field(default_factory=list, max_length=12)
    limitations: list[str] = Field(default_factory=list, max_length=8)
    insufficient_evidence: bool = False
    model: str | None = None
    created_at: datetime


class ChatThreadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: str | None
    scope: Literal["analysis", "comparison"]
    context_ids: list[str]
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatThreadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: ChatThreadData
    meta: dict[str, object] = Field(default_factory=dict)


class AnalysisChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)


class ComparisonChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_ids: list[str] = Field(min_length=2, max_length=25)
    question: str = Field(min_length=1, max_length=2000)


class ChatAnswerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=6000)
    citation_ids: list[str] = Field(default_factory=list, max_length=12)
    insufficient_evidence: bool = False
    limitations: list[str] = Field(default_factory=list, max_length=8)
