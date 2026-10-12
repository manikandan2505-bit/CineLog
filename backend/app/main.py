from fastapi import FastAPI
from sqlalchemy import text

from app.routers import users
from app.routers import watchlist
from app.routers import diary
from app.routers import tv_shows
from app.routers import favorites
from app.routers import follows
from app.routers import activity
from app.routers import lists

from app.database import engine
from app.routers import movies
from app.routers import ratings
from app.routers import reviews


app = FastAPI(
    title="CineLog API",
    description="Backend API for the CineLog movie and TV tracking platform",
    version="1.0.0"
)


app.include_router(movies.router)
app.include_router(users.router)
app.include_router(watchlist.router)
app.include_router(diary.router)
app.include_router(tv_shows.router)
app.include_router(ratings.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(follows.router)
app.include_router(activity.router)
app.include_router(lists.router)

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