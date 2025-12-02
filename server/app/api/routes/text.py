from fastapi import APIRouter, HTTPException

from app.schemas.text import TextParseRequest, TextParseResponse, SummarizeRequest, SummarizeResponse, SummarizeMeta, TextMeta
from app.core.config import settings
from app.services import text_service

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/parse", response_model=TextParseResponse)
def parse_text(payload: TextParseRequest) -> TextParseResponse:
  text, truncated = text_service.clamp_text(payload.content)
  meta = TextMeta(length=len(text), truncated=truncated)
  return TextParseResponse(text=text, meta=meta)


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_text(payload: SummarizeRequest) -> SummarizeResponse:
  base_text, truncated_input = text_service.clamp_text(payload.text)
  summary, truncated_output = text_service.summarize_mock(
    base_text,
    ratio=payload.ratio or 0.3,
    max_tokens=payload.max_tokens or settings.TTS_SLICE_LIMIT,
  )
  meta = SummarizeMeta(ratio=payload.ratio or 0.3, truncated=truncated_input or truncated_output)
  if not summary:
    raise HTTPException(status_code=400, detail="No content to summarize")
  return SummarizeResponse(summary=summary, meta=meta)
