from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import WatchlistItem, Movie, User
from app.security import get_current_user


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)


@router.post("/movies/{movie_id}", status_code=201)
def add_movie_to_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    movie = (
        db.query(Movie)
        .filter(Movie.id == movie_id)
        .first()
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    existing_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.movie_id == movie_id
        )
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=409,
            detail="Movie already exists in your watchlist"
        )

    watchlist_item = WatchlistItem(
        user_id=current_user.id,
        movie_id=movie_id
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    return {
        "message": "Movie added to watchlist",
        "watchlist_id": watchlist_item.id,
        "movie_id": movie.id,
        "title": movie.title
    }

@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist_items = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id
        )
        .all()
    )

    result = []

    for item in watchlist_items:

        movie = None

        if item.movie_id:
            movie = (
                db.query(Movie)
                .filter(Movie.id == item.movie_id)
                .first()
            )

        result.append({
            "watchlist_id": item.id,
            "movie_id": item.movie_id,
            "title": movie.title if movie else None,
            "poster_path": movie.poster_path if movie else None,
            "added_at": item.added_at
        })

    return result

@router.delete("/movies/{movie_id}")
def remove_movie_from_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.movie_id == movie_id
        )
        .first()
    )

    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail="Movie is not in your watchlist"
        )

    db.delete(watchlist_item)
    db.commit()

    return {
        "message": "Movie removed from watchlist",
        "movie_id": movie_id
    }