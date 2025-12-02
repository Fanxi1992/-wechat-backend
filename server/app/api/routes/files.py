from fastapi import APIRouter, UploadFile, File, HTTPException

from server.app.schemas.file import FileParseResponse, FileMeta
from server.app.services.file_service import read_file_content, validate_file

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/parse", response_model=FileParseResponse)
async def parse_file(file: UploadFile = File(...)) -> FileParseResponse:
  try:
    ext, _ = validate_file(file)
  except ValueError as e:
    print(f"[file_parse][reject] filename={file.filename} err={e}")
    raise HTTPException(status_code=400, detail=str(e))

  text = await read_file_content(file)
  meta = FileMeta(
    filename=file.filename or "unnamed",
    size=file.size or 0,  # type: ignore[attr-defined]
    ext=ext,
    note="parser placeholder for non-txt files" if ext != "txt" else None,
  )
  print(f"[file_parse] filename={meta.filename} size={meta.size} ext={ext} text_len={len(text)}")
  return FileParseResponse(text=text, meta=meta)
