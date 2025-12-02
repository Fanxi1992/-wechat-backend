from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
  username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
  password: str = Field(..., min_length=6, max_length=64)
  email: Optional[EmailStr] = None


class UserLogin(UserBase):
  password: str = Field(..., min_length=6, max_length=64)


class Token(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str = "bearer"
