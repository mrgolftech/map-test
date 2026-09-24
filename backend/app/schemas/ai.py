from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIKeyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["FACT", "JUDGMENT"]
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(min_length=1, max_length=1200)
    evidence: list[str] = Field(default_factory=list, max_length=8)


class AISpatialPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["JUDGMENT"] = "JUDGMENT"
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(min_length=1, max_length=1200)
    evidence: list[str] = Field(default_factory=list, max_length=8)


class AIPossibleCause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["HYPOTHESIS"] = "HYPOTHESIS"
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(min_length=1, max_length=1200)
    rationale: str = Field(min_length=1, max_length=1200)


class AIRecommendedCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["RECOMMENDATION"] = "RECOMMENDATION"
    title: str = Field(min_length=1, max_length=160)
    action: str = Field(min_length=1, max_length=1200)
    expected_evidence: str | None = Field(default=None, max_length=1200)


class AIReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=1, max_length=2400)
    key_findings: list[AIKeyFinding] = Field(max_length=12)
    spatial_patterns: list[AISpatialPattern] = Field(max_length=8)
    possible_causes: list[AIPossibleCause] = Field(max_length=8)
    recommended_checks: list[AIRecommendedCheck] = Field(max_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(max_length=12)


class AIAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1, max_length=64)


class AIAnalyzeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    model: str
    report: AIReport


class AIAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AIAnalyzeResult
    meta: dict[str, object] = Field(default_factory=dict)


class LLMConfigStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    configured: bool
    base_url: str | None
    model: str | None
    api_key_configured: bool


class LLMConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: LLMConfigStatus
    meta: dict[str, object] = Field(default_factory=dict)


class LLMConnectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    model: str
    message: str


class LLMConnectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: LLMConnectionResult
    meta: dict[str, object] = Field(default_factory=dict)
