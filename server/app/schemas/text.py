from typing import Optional

from pydantic import BaseModel, Field


class TextParseRequest(BaseModel):
  content: str = Field(..., min_length=1, description="Raw text content")


class TextMeta(BaseModel):
  length: int
  truncated: bool = False


class TextParseResponse(BaseModel):
  text: str
  meta: TextMeta


class SummarizeRequest(BaseModel):
  text: str = Field(..., min_length=1)
  max_tokens: Optional[int] = Field(default=200, ge=10, le=2000)
  ratio: Optional[float] = Field(default=0.3, ge=0.05, le=1.0)


class SummarizeMeta(BaseModel):
  truncated: bool = False
  ratio: float
  model: str | None = None


class SummarizeResponse(BaseModel):
  summary: str
  meta: SummarizeMeta
