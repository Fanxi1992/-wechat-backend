import base64
import json
import mimetypes

from fastapi import UploadFile

from server.app.core.config import settings


FOOD_NUTRITION_SCHEMA = {
  "type": "object",
  "properties": {
    "foods": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "food_name": {"type": "string", "description": "标准化的食物名称"},
          "weight": {"type": "number", "description": "重量，单位为克(g)", "minimum": 0},
          "unit": {"type": "string", "description": "单位，建议为g"},
          "calories": {"type": "number", "description": "能量，单位为千卡(kcal)", "minimum": 0},
          "carbohydrates": {"type": "number", "description": "碳水化合物，单位为克(g)", "minimum": 0},
          "protein": {"type": "number", "description": "蛋白质，单位为克(g)", "minimum": 0},
          "fat": {"type": "number", "description": "脂肪，单位为克(g)", "minimum": 0},
        },
        "required": ["food_name", "weight", "unit", "calories", "carbohydrates", "protein", "fat"],
        "additionalProperties": False,
      },
    }
  },
  "required": ["foods"],
  "additionalProperties": False,
}


def _looks_like_schema_unsupported(err: Exception) -> bool:
  msg = str(err).lower()
  return ("response_format" in msg) or ("json_schema" in msg)


def _guess_mime_type(filename: str, content_type: str | None) -> str:
  if content_type and content_type.startswith("image/"):
    return content_type
  mime_type, _ = mimetypes.guess_type(filename)
  return mime_type or "image/jpeg"


def _image_bytes_to_data_url(image_bytes: bytes, mime_type: str) -> str:
  image_b64 = base64.b64encode(image_bytes).decode("utf-8")
  return f"data:{mime_type};base64,{image_b64}"


def _extract_json_object(text: str) -> dict:
  try:
    return json.loads(text)
  except json.JSONDecodeError:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
      return json.loads(text[start : end + 1])
    raise


def _get_api_key() -> str:
  if not settings.DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY not configured")
  return settings.DASHSCOPE_API_KEY


def _get_openai_client():
  try:
    from openai import OpenAI  # type: ignore[import-not-found]
  except ImportError as e:  # pragma: no cover
    raise ValueError("Missing dependency: pip install openai") from e

  return OpenAI(
    api_key=_get_api_key(),
    base_url=settings.DASHSCOPE_BASE_URL,
    timeout=settings.QWEN_VL_TIMEOUT,
    max_retries=0,
  )


def analyze_meal_photo(image_data_url: str) -> tuple[dict, bool, str]:
  """
  Call DashScope Qwen-VL for meal photo analysis.
  Returns (result_json, used_json_schema, model).
  Raises ValueError on missing config or request failure.
  """
  client = _get_openai_client()

  system_prompt = (
    "你是一个专业的营养学家，擅长根据餐食照片估算营养成分。"
    "请只输出严格符合 JSON Schema 的 JSON，不要输出任何解释、前后缀、Markdown 代码块。"
    "所有数值字段必须是数字类型，不能带单位；重量单位为克(g)，能量单位为千卡(kcal)。"
    "如果图中有多个食物，请分别列出。"
  )
  user_prompt = (
    "请识别图片中的所有食物，并估算每种食物的可食部分重量，以及热量、碳水、蛋白质、脂肪。"
    "输出字段：food_name, weight, unit, calories, carbohydrates, protein, fat。"
    "unit 请统一用 'g'。"
  )

  request_kwargs: dict = {
    "model": settings.QWEN_VL_MODEL,
    "messages": [
      {"role": "system", "content": system_prompt},
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": image_data_url}},
          {"type": "text", "text": user_prompt},
        ],
      },
    ],
    "temperature": settings.QWEN_VL_TEMPERATURE,
    "max_tokens": settings.QWEN_VL_MAX_TOKENS,
    "stream": False,
    "extra_body": {"enable_thinking": settings.QWEN_VL_ENABLE_THINKING},
  }

  used_json_schema = False
  if settings.QWEN_VL_USE_JSON_SCHEMA:
    used_json_schema = True
    request_kwargs["response_format"] = {
      "type": "json_schema",
      "json_schema": {
        "name": "food_nutrition_analysis",
        "schema": FOOD_NUTRITION_SCHEMA,
        "strict": True,
      },
    }

  last_error: Exception | None = None
  retries = max(0, settings.QWEN_VL_RETRIES)
  for attempt in range(retries + 1):
    try:
      try:
        response = client.chat.completions.create(**request_kwargs)
      except Exception as e:
        if used_json_schema and _looks_like_schema_unsupported(e):
          request_kwargs.pop("response_format", None)
          used_json_schema = False
          response = client.chat.completions.create(**request_kwargs)
        else:
          raise

      content = (response.choices[0].message.content or "").strip()
      if not content:
        raise ValueError("Empty content from Qwen-VL")
      return _extract_json_object(content), used_json_schema, request_kwargs["model"]
    except Exception as e:  # noqa: BLE001
      last_error = e
      if attempt >= retries:
        break

  raise ValueError(str(last_error) if last_error else "Qwen-VL analyze failed")


def validate_image_upload(file: UploadFile) -> tuple[str, int]:
  filename = file.filename or "unnamed"
  ext_part = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
  allowed = [e.strip().lower() for e in settings.ALLOW_IMAGE_EXT.split(",") if e.strip()]
  if ext_part not in allowed:
    raise ValueError(f"unsupported image type: {ext_part}")
  max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
  size_attr = getattr(file, "size", None)
  if size_attr and size_attr > max_bytes:
    raise ValueError("image too large")
  return ext_part, size_attr or 0


async def read_image_upload(file: UploadFile) -> tuple[bytes, str, int]:
  """
  Read uploaded image into memory with a hard size limit.
  Returns (bytes, mime_type, size).
  """
  validate_image_upload(file)
  filename = file.filename or "upload"
  mime_type = _guess_mime_type(filename, file.content_type)

  max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
  written = 0
  chunks: list[bytes] = []

  while True:
    chunk = await file.read(1024 * 1024)
    if not chunk:
      break
    written += len(chunk)
    if written > max_bytes:
      raise ValueError("image too large")
    chunks.append(chunk)

  data = b"".join(chunks)
  if not data:
    raise ValueError("empty image file")
  return data, mime_type, written


def analyze_meal_image_bytes(image_bytes: bytes, mime_type: str) -> tuple[dict, bool, str]:
  image_data_url = _image_bytes_to_data_url(image_bytes, mime_type)
  return analyze_meal_photo(image_data_url)

