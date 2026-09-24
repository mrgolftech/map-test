from pydantic import BaseModel, ConfigDict, Field


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AdminSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authenticated: bool
    configured: bool
    username: str | None = None


class AdminSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AdminSession
    meta: dict[str, object] = Field(default_factory=dict)
