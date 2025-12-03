import requests
from server.app.core.config import settings


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


def summarize_llm(text: str, ratio: float, max_tokens: int) -> tuple[str, bool, str]:
  """
  Call OpenRouter for summarization. Returns (summary, truncated_output, model).
  Raises ValueError on missing config or request failure.
  """
  if not settings.OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not configured")

  target_len = min(
    max_tokens,
    max(settings.SUMMARY_MIN_LENGTH, int(len(text) * ratio)),
  )
  prompt = (
    f"请用中文总结以下内容，输出一个适合用来听的摘要版本，保留关键要点，输出纯文本：\n\n{text}"
  )

  payload = {
    "model": settings.OPENROUTER_MODEL,
    "messages": [
      {"role": "user", "content": prompt}
    ],
    "max_tokens": max_tokens,
    "temperature": 0.2
  }
  headers = {
    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
  }

  last_error: Exception | None = None
  retries = max(0, settings.OPENROUTER_RETRIES)
  for attempt in range(retries + 1):
    try:
      resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=settings.OPENROUTER_TIMEOUT,
      )
      if resp.status_code != 200:
        raise ValueError(f"OpenRouter error: {resp.status_code} {resp.text}")
      data = resp.json()
      choices = data.get("choices") or []
      if not choices:
        raise ValueError("No choices returned from OpenRouter")
      message = choices[0].get("message") or {}
      content = message.get("content", "").strip()
      if not content:
        raise ValueError("Empty content from OpenRouter")
      truncated_output = len(content) > target_len
      return content, truncated_output, payload["model"]
    except Exception as e:  # noqa: BLE001
      last_error = e
      if attempt >= retries:
        break
  raise ValueError(str(last_error) if last_error else "OpenRouter summarize failed")
