
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.engine import init_db
from api.routes import workouts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the existing database
    init_db()
    yield


app = FastAPI(
    title="Gym Progress Tracker API",
    description="REST API for tracking workouts and exercises",
    version="1.0.0",
    lifespan=lifespan,
)


# Register API routes
app.include_router(workouts.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "Gym Tracker API is running",
    }
