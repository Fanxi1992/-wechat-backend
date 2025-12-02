from fastapi import FastAPI
from app.api.routes import router as api_router
from app.core.config import settings


def create_app() -> FastAPI:
  """
  Application factory to wire routers, dependencies, and startup/shutdown hooks.
  Extend here when adding middleware, CORS, tracing, etc.
  """
  app = FastAPI(title="TTS Backend", version="0.1.0")

  # Routers
  app.include_router(api_router, prefix=settings.API_PREFIX)

  @app.get("/health", tags=["health"])
  def health_check():
    return {"status": "ok"}

  return app


app = create_app()


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
