from fastapi import APIRouter, HTTPException

from server.app.schemas.text import TextParseRequest, TextParseResponse, SummarizeRequest, SummarizeResponse, SummarizeMeta, TextMeta
from server.app.core.config import settings
from server.app.services import text_service

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/parse", response_model=TextParseResponse)
def parse_text(payload: TextParseRequest) -> TextParseResponse:
  text, truncated = text_service.clamp_text(payload.content)
  meta = TextMeta(length=len(text), truncated=truncated)
  return TextParseResponse(text=text, meta=meta)


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_text(payload: SummarizeRequest) -> SummarizeResponse:
  base_text, truncated_input = text_service.clamp_text(payload.text)
  ratio = payload.ratio or 0.3
  max_tokens = payload.max_tokens or settings.TTS_SLICE_LIMIT

  try:
    summary, truncated_output, model = text_service.summarize_llm(
      base_text,
      ratio=ratio,
      max_tokens=max_tokens,
    )
  except ValueError as e:
    # If not configured or failed, expose as 502 to front-end
    raise HTTPException(status_code=502, detail=str(e))

  meta = SummarizeMeta(ratio=ratio, truncated=truncated_input or truncated_output, model=model)
  if not summary:
    raise HTTPException(status_code=400, detail="No content to summarize")
  return SummarizeResponse(summary=summary, meta=meta)
