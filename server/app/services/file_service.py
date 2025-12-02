import os
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
from PyPDF2 import PdfReader  # type: ignore
import docx  # type: ignore

from app.core.config import settings


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


async def read_file_content(file: UploadFile) -> str:
  """
  Read file content into text. Supports txt/pdf/docx. Other allowed types can be extended here.
  Enforces size limit while streaming.
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
      text = temp_path.read_text(encoding="utf-8", errors="ignore")
    elif ext_part == "pdf":
      reader = PdfReader(str(temp_path))
      pages = [page.extract_text() or "" for page in reader.pages]
      text = "\n".join(pages).strip()
    elif ext_part in ("doc", "docx"):
      doc = docx.Document(str(temp_path))
      paragraphs = [p.text for p in doc.paragraphs]
      text = "\n".join(paragraphs).strip()
    else:
      text = ""
  finally:
    try:
      os.remove(temp_path)
    except OSError:
      pass

  if not text:
    text = f"[{ext_part}] parser returned empty text"
  return text
