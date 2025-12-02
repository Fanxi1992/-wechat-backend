from app.core.config import settings


def clamp_text(content: str) -> tuple[str, bool]:
  limit = settings.TEXT_LIMIT
  if len(content) > limit:
    return content[:limit], True
  return content, False


def summarize_mock(text: str, ratio: float, max_tokens: int) -> tuple[str, bool]:
  """
  Mock summarization: return a truncated slice respecting ratio/max_tokens.
  """
  if not text:
    return "", False
  target_len = min(max_tokens, max(1, int(len(text) * ratio)))
  truncated = len(text) > target_len
  summary = text[:target_len]
  return summary, truncated
