import os
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

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
  Read file content into text. For non-txt types, return placeholder note.
  """
  ext_part, _ = validate_file(file)
  temp_dir = ensure_temp_dir()
  temp_path = temp_dir / file.filename if file.filename else temp_dir / "upload.tmp"

  # Save stream to temp to allow parsers later.
  with temp_path.open("wb") as out:
    while True:
      chunk = await file.read(1024 * 1024)
      if not chunk:
        break
      out.write(chunk)

  text: str
  if ext_part == "txt":
    text = temp_path.read_text(encoding="utf-8", errors="ignore")
  else:
    text = f"[{ext_part}] parser not implemented, raw file saved at {temp_path}"

  # Optionally clean up non-txt files to avoid clutter; keep temp for debugging.
  try:
    if ext_part != "txt":
      os.remove(temp_path)
  except OSError:
    pass

  return text
