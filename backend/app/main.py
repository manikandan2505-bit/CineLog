from fastapi import FastAPI
from sqlalchemy import text

from app.routers import users
from app.routers import watchlist

from app.database import engine
from app.routers import movies


app = FastAPI(
    title="CineLog API",
    description="Backend API for the CineLog movie and TV tracking platform",
    version="1.0.0"
)


app.include_router(movies.router)
app.include_router(users.router)
app.include_router(watchlist.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to CineLog API",
        "status": "running"
    }


@app.get("/health")
def health_check():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as error:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error)
        }