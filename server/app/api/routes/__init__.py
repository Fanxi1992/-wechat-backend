from fastapi import APIRouter

from server.app.api.routes import auth, text, files, meal

router = APIRouter()

router.include_router(auth.router)
router.include_router(text.router)
router.include_router(files.router)
router.include_router(meal.router)
