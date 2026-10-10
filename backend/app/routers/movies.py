from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.security import get_current_user
from app.schemas import MovieResponse
from app.services.movie_service import (
    import_movie_data,
    get_movie_by_id
)
from app.models import (
    Movie,
    Favorite,
    MovieRating,
    MovieReview,
    DiaryEntry,
    WatchlistItem,
    User
)

from app.schemas import MovieDetailsResponse
from app.tmdb import search_movies, get_movie_details


router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)


@router.get("/search")
async def movie_search(query: str):

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )

    try:
        results = await search_movies(query)

        return {
            "query": query,
            "results": results.get("results", [])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
@router.get("/tmdb/{tmdb_id}")
async def movie_details(tmdb_id: int):

    try:
        movie = await get_movie_details(tmdb_id)

        return movie

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch movie details from TMDB"
        )
@router.post("/import/{tmdb_id}")
async def import_movie(
    tmdb_id: int,
    db: Session = Depends(get_db)
):

    try:
        # Get complete movie data from TMDB
        movie_data = await get_movie_details(tmdb_id)

        # Import movie, genres, cast and crew
        movie = import_movie_data(
            db=db,
            movie_data=movie_data
        )

        # Save all changes
        db.commit()

        return {
            "message": "Movie imported successfully",
            "movie_id": movie.id,
            "tmdb_id": movie.tmdb_id,
            "title": movie.title
        }

    except Exception as error:
        db.rollback()

        print("IMPORT ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Failed to import movie"
        )

@router.get("/", response_model=list[MovieResponse])
def get_movies(
    db: Session = Depends(get_db)
):

    movies = db.query(Movie).all()

    return movies

@router.get(
    "/{movie_id}/details",
    response_model=MovieDetailsResponse
)
def get_movie_details(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # -----------------------------------
    # Get movie
    # -----------------------------------

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

    # -----------------------------------
    # Overall rating
    # -----------------------------------

    rating_data = (
        db.query(
            func.avg(MovieRating.rating),
            func.count(MovieRating.id)
        )
        .filter(MovieRating.movie_id == movie_id)
        .first()
    )

    average_rating = (
        float(rating_data[0])
        if rating_data[0] is not None
        else None
    )

    rating_count = int(rating_data[1] or 0)

    # -----------------------------------
    # Review count
    # -----------------------------------

    review_count = (
        db.query(func.count(MovieReview.id))
        .filter(MovieReview.movie_id == movie_id)
        .scalar()
    ) or 0

    # -----------------------------------
    # Current user's rating
    # -----------------------------------

    user_rating_obj = (
        db.query(MovieRating)
        .filter(
            MovieRating.movie_id == movie_id,
            MovieRating.user_id == current_user.id
        )
        .first()
    )

    user_rating = (
        float(user_rating_obj.rating)
        if user_rating_obj
        else None
    )

    # -----------------------------------
    # Current user's review
    # -----------------------------------

    user_review_obj = (
        db.query(MovieReview)
        .filter(
            MovieReview.movie_id == movie_id,
            MovieReview.user_id == current_user.id
        )
        .first()
    )

    user_review = (
        user_review_obj.review_text
        if user_review_obj
        else None
    )

    user_contains_spoilers = (
        user_review_obj.contains_spoilers
        if user_review_obj
        else False
    )

    # -----------------------------------
    # Movie diary
    # -----------------------------------

    diary_entries = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.movie_id == movie_id,
            DiaryEntry.user_id == current_user.id
        )
        .order_by(
            DiaryEntry.watched_at.desc(),
            DiaryEntry.id.desc()
        )
        .all()
    )

    watched = len(diary_entries) > 0

    watch_count = len(diary_entries)

    latest_entry = (
        diary_entries[0]
        if diary_entries
        else None
    )

    latest_rating = (
        float(latest_entry.rating)
        if latest_entry and latest_entry.rating is not None
        else None
    )

    latest_review = (
        latest_entry.review
        if latest_entry
        else None
    )

    latest_notes = (
        latest_entry.notes
        if latest_entry
        else None
    )

    latest_watched_at = (
        latest_entry.watched_at
        if latest_entry
        else None
    )

    # -----------------------------------
    # Watchlist
    # -----------------------------------

    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.movie_id == movie_id
        )
        .first()
    )

    in_watchlist = watchlist_item is not None

    in_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.movie_id == movie_id
    ).first() is not None

    # -----------------------------------
    # Final response
    # -----------------------------------

    return MovieDetailsResponse(
        id=movie.id,
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        original_title=movie.original_title,
        overview=movie.overview,
        release_date=movie.release_date,
        runtime=movie.runtime,
        original_language=movie.original_language,
        poster_path=movie.poster_path,
        backdrop_path=movie.backdrop_path,
        vote_average=(
            float(movie.vote_average)
            if movie.vote_average is not None
            else None
        ),
        vote_count=movie.vote_count,
        popularity=(
            float(movie.popularity)
            if movie.popularity is not None
            else None
        ),
        status=movie.status,

        average_rating=average_rating,
        rating_count=rating_count,
        review_count=int(review_count),

        user_rating=user_rating,
        user_review=user_review,
        user_contains_spoilers=user_contains_spoilers,

        watched=watched,
        watch_count=watch_count,
        latest_rating=latest_rating,
        latest_review=latest_review,
        latest_notes=latest_notes,
        latest_watched_at=latest_watched_at,

        in_watchlist=in_watchlist,
        in_favorites = in_favorites
    )

@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db)
):
    movie = get_movie_by_id(
        db=db,
        movie_id=movie_id
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    return movie