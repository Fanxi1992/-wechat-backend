from typing import Optional, List

from sqlmodel import Session, select

from app.dbs import models


class UserDAO:
  """
  Minimal DAO example. Extend or replace when a real auth system is needed.
  """

  @staticmethod
  def get_by_username(username: str, db: Session) -> Optional[models.User]:
    return db.exec(select(models.User).where(models.User.username == username)).first()

  @staticmethod
  def get_by_id(user_id: int, db: Session) -> Optional[models.User]:
    return db.get(models.User, user_id)

  @staticmethod
  def create_user(username: str, password_hash: str, db: Session) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

  @staticmethod
  def list_users(offset: int, limit: int, db: Session) -> List[models.User]:
    return db.exec(select(models.User).offset(offset).limit(limit)).all()
