from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movie, MovieRating, User
from app.schemas import (
    MovieRatingCreate,
    MovieRatingResponse
)
from app.security import get_current_user


router = APIRouter(
    prefix="/ratings",
    tags=["Ratings"]
)


@router.post(
    "/movies/{movie_id}",
    response_model=MovieRatingResponse,
    status_code=201
)
def rate_movie(
    movie_id: int,
    rating_data: MovieRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if rating_data.rating < 0.5 or rating_data.rating > 5.0:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 0.5 and 5.0"
        )

    if (rating_data.rating * 2) % 1 != 0:
        raise HTTPException(
            status_code=400,
            detail="Rating must use 0.5 star increments"
        )

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

    existing_rating = (
        db.query(MovieRating)
        .filter(
            MovieRating.user_id == current_user.id,
            MovieRating.movie_id == movie_id
        )
        .first()
    )

    if existing_rating:
        raise HTTPException(
            status_code=409,
            detail="You have already rated this movie"
        )

    new_rating = MovieRating(
        user_id=current_user.id,
        movie_id=movie_id,
        rating=rating_data.rating
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)

    return new_rating

@router.get(
    "/movies/{movie_id}",
    response_model=MovieRatingResponse
)
def get_movie_rating(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = (
        db.query(MovieRating)
        .filter(
            MovieRating.user_id == current_user.id,
            MovieRating.movie_id == movie_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this movie"
        )

    return rating

@router.put(
    "/movies/{movie_id}",
    response_model=MovieRatingResponse
)
def update_movie_rating(
    movie_id: int,
    rating_data: MovieRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if rating_data.rating < 0.5 or rating_data.rating > 5.0:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 0.5 and 5.0"
        )

    if (rating_data.rating * 2) % 1 != 0:
        raise HTTPException(
            status_code=400,
            detail="Rating must use 0.5 star increments"
        )

    rating = (
        db.query(MovieRating)
        .filter(
            MovieRating.user_id == current_user.id,
            MovieRating.movie_id == movie_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this movie"
        )

    rating.rating = rating_data.rating

    db.commit()
    db.refresh(rating)

    return rating

@router.delete("/movies/{movie_id}")
def delete_movie_rating(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = (
        db.query(MovieRating)
        .filter(
            MovieRating.user_id == current_user.id,
            MovieRating.movie_id == movie_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this movie"
        )

    db.delete(rating)
    db.commit()

    return {
        "message": "Movie rating deleted",
        "movie_id": movie_id
    }