from typing import Optional

from pydantic import BaseModel


class FileMeta(BaseModel):
  filename: str
  size: int
  ext: str
  note: Optional[str] = None


class FileParseResponse(BaseModel):
  text: str
  meta: FileMeta
