from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
  expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  payload = {"exp": expire, "sub": subject, "type": "access"}
  return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
  expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
  payload = {"exp": expire, "sub": subject, "type": "refresh"}
  return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
