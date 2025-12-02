from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/placeholder")
def auth_placeholder():
  """
  Placeholder auth route. Replace with real register/login when needed.
  """
  return {"message": "auth placeholder"}
