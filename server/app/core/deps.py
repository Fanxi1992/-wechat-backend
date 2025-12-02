from collections.abc import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token  # noqa: F401
from app.dbs.session import SessionLocal
from app.dbs.daos import UserDAO  # type: ignore[attr-defined]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def get_db() -> Generator[Session, None, None]:
  with SessionLocal() as session:
    yield session


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  """
  Placeholder current user dependency. User model/DAO not implemented yet.
  Keep here for future expansion; will raise if called now.
  """
  try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    user_id: str | None = payload.get("sub")
    if user_id is None:
      raise ValueError("Invalid token subject")
  except (JWTError, ValueError):
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

  # Placeholder: replace with actual user lookup when model exists.
  if not hasattr(UserDAO, "get_by_id"):
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User model not implemented")
  user = UserDAO.get_by_id(int(user_id), db)  # type: ignore[attr-defined]
  if not user:
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
  return user
