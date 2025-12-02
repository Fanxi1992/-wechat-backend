from sqlmodel import SQLModel, create_engine, Session

from app.core.config import settings

engine = create_engine(
  settings.DATABASE_URL,
  echo=settings.DEBUG,
  pool_recycle=7200,
)

SessionLocal = Session


def init_db() -> None:
  """
  Create tables. Call this from a startup script or migration step.
  """
  SQLModel.metadata.create_all(engine)
