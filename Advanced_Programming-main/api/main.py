from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from db.engine import init_db
from api.routes import auth, exercises, workouts


# All API routes in one router, so they can be mounted both in this
# standalone app and inside the NiceGUI web app (see application.py).
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workouts.router)
api_router.include_router(exercises.router)


@api_router.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "Gym Tracker API is running",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the existing database
    init_db()
    yield


# Standalone API (uvicorn api.main:app) - useful for testing in /docs
app = FastAPI(
    title="Gym Progress Tracker API",
    description="REST API for tracking workouts and exercises",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)
