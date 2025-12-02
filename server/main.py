from fastapi import FastAPI
from server.app.api.routes import router as api_router
from server.app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
  """
  Application factory to wire routers, dependencies, and startup/shutdown hooks.
  Extend here when adding middleware, CORS, tracing, etc.
  """
  app = FastAPI(title="TTS Backend", version="0.1.0")

  # CORS: allow all origins (adjust in production as needed)
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

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
