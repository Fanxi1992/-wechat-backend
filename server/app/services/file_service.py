import os
import re
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
from PyPDF2 import PdfReader  # type: ignore
import docx  # type: ignore

from server.app.core.config import settings


def ensure_temp_dir() -> Path:
  path = Path(settings.TEMP_DIR)
  path.mkdir(parents=True, exist_ok=True)
  return path


def validate_file(file: UploadFile) -> Tuple[str, int]:
  filename = file.filename or "unnamed"
  ext_part = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
  allowed = [e.strip().lower() for e in settings.ALLOW_FILE_EXT.split(",") if e.strip()]
  if ext_part not in allowed:
    raise ValueError(f"unsupported file type: {ext_part}")
  max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
  size_attr = getattr(file, "size", None)
  if size_attr and size_attr > max_bytes:
    raise ValueError("file too large")
  return ext_part, size_attr or 0


def sanitize_text(text: str) -> str:
  """
  Light cleaning for readability:
  - normalize newlines
  - remove control chars and zero-width chars
  - collapse multiple blank lines and spaces
  """
  if not text:
    return text

  # Normalize newlines
  text = text.replace("\r\n", "\n").replace("\r", "\n")
  # Remove control characters/zero-width
  text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]", "", text)
  text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t ")
  # Collapse multiple spaces
  text = re.sub(r"[ \t]+", " ", text)
  # Collapse multiple blank lines to max 1
  text = re.sub(r"\n{3,}", "\n\n", text)
  return text.strip()


async def read_file_content(file: UploadFile) -> str:
  """
  Read file content into text. Supports txt/pdf/docx. Other allowed types can be extended here.
  Enforces size limit while streaming. Applies light sanitization.
  """
  ext_part, declared_size = validate_file(file)
  temp_dir = ensure_temp_dir()
  temp_path = temp_dir / (file.filename or "upload.tmp")

  max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
  written = 0

  with temp_path.open("wb") as out:
    while True:
      chunk = await file.read(1024 * 1024)
      if not chunk:
        break
      written += len(chunk)
      if written > max_bytes:
        out.close()
        try:
          os.remove(temp_path)
        except OSError:
          pass
        raise ValueError("file too large")
      out.write(chunk)

  try:
    if ext_part == "txt":
      raw_text = temp_path.read_text(encoding="utf-8", errors="ignore")
    elif ext_part == "pdf":
      reader = PdfReader(str(temp_path))
      pages = [page.extract_text() or "" for page in reader.pages]
      raw_text = "\n".join(pages)
    elif ext_part in ("doc", "docx"):
      doc = docx.Document(str(temp_path))
      paragraphs = [p.text for p in doc.paragraphs]
      raw_text = "\n".join(paragraphs)
    else:
      raw_text = ""
  finally:
    try:
      os.remove(temp_path)
    except OSError:
      pass

  cleaned = sanitize_text(raw_text)
  if not cleaned:
    cleaned = f"[{ext_part}] parser returned empty text"
  return cleaned
