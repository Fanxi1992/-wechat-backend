from sqlmodel import Session

from server.app.core import security
from server.app.dbs.daos import UserDAO


class UserService:
  """
  Minimal user service wiring. Extend or replace when auth is required.
  """

  def __init__(self, db: Session):
    self.db = db

  def create_user(self, username: str, password: str):
    hashed = security.get_password_hash(password)
    return UserDAO.create_user(username, hashed, self.db)
