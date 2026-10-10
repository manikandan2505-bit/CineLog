from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Movie,
    MovieRating,
    Episode,
    DiaryEntry,
    TVShow,
    ShowRating,
    User
)
from app.schemas import (
    MovieRatingCreate,
    MovieRatingResponse,
    EpisodeDiaryEntryCreate,
    EpisodeDiaryEntryResponse,
    ShowRatingCreate,
    ShowRatingResponse
)
from app.security import get_current_user


router = APIRouter(
    prefix="/ratings",
    tags=["Ratings"]
)


# =========================================================
# MOVIE RATINGS
# =========================================================

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


# =========================================================
# EPISODE RATINGS
# =========================================================

@router.post(
    "/episodes/{episode_id}",
    response_model=EpisodeDiaryEntryResponse,
    status_code=201
)
def rate_episode(
    episode_id: int,
    rating_data: EpisodeDiaryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Validate rating
    # -----------------------------------------------------

    if rating_data.rating is None:
        raise HTTPException(
            status_code=400,
            detail="Rating is required"
        )

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

    # -----------------------------------------------------
    # Check episode
    # -----------------------------------------------------

    episode = (
        db.query(Episode)
        .filter(Episode.id == episode_id)
        .first()
    )

    if not episode:
        raise HTTPException(
            status_code=404,
            detail="Episode not found"
        )

    # -----------------------------------------------------
    # Check existing rating
    #
    # A rating is stored as a diary entry.
    # We allow multiple entries because CineLog supports
    # rewatches.
    # -----------------------------------------------------

    new_entry = DiaryEntry(
        user_id=current_user.id,
        episode_id=episode_id,
        watched_at=rating_data.watched_at,
        rating=rating_data.rating,
        review=rating_data.review,
        notes=rating_data.notes,
        rewatch=rating_data.rewatch
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry


# =========================================================
# GET LATEST EPISODE RATING
# =========================================================

@router.get(
    "/episodes/{episode_id}",
    response_model=EpisodeDiaryEntryResponse
)
def get_episode_rating(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    episode = (
        db.query(Episode)
        .filter(Episode.id == episode_id)
        .first()
    )

    if not episode:
        raise HTTPException(
            status_code=404,
            detail="Episode not found"
        )

    latest_entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id == episode_id
        )
        .order_by(
            DiaryEntry.watched_at.desc()
        )
        .first()
    )

    if not latest_entry:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this episode"
        )

    return latest_entry


# =========================================================
# UPDATE LATEST EPISODE RATING
# =========================================================

@router.put(
    "/episodes/{episode_id}",
    response_model=EpisodeDiaryEntryResponse
)
def update_episode_rating(
    episode_id: int,
    rating_data: EpisodeDiaryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Validate rating
    # -----------------------------------------------------

    if rating_data.rating is None:
        raise HTTPException(
            status_code=400,
            detail="Rating is required"
        )

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

    # -----------------------------------------------------
    # Find latest diary entry
    # -----------------------------------------------------

    entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id == episode_id
        )
        .order_by(
            DiaryEntry.watched_at.desc()
        )
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this episode"
        )

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    entry.rating = rating_data.rating
    entry.review = rating_data.review
    entry.notes = rating_data.notes

    db.commit()
    db.refresh(entry)

    return entry


# =========================================================
# DELETE LATEST EPISODE RATING
# =========================================================

@router.delete(
    "/episodes/{episode_id}"
)
def delete_episode_rating(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id == episode_id
        )
        .order_by(
            DiaryEntry.watched_at.desc()
        )
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this episode"
        )

    db.delete(entry)
    db.commit()

    return {
        "message": "Episode rating deleted",
        "episode_id": episode_id
    }

# =========================================================
# TV SHOW RATINGS
# =========================================================

@router.post(
    "/tv-shows/{tv_show_id}",
    response_model=ShowRatingResponse,
    status_code=201
)
def rate_tv_show(
    tv_show_id: int,
    rating_data: ShowRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Validate rating
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Check TV show
    # -----------------------------------------------------

    tv_show = (
        db.query(TVShow)
        .filter(TVShow.id == tv_show_id)
        .first()
    )

    if not tv_show:
        raise HTTPException(
            status_code=404,
            detail="TV show not found"
        )

    # -----------------------------------------------------
    # Check existing rating
    # -----------------------------------------------------

    existing_rating = (
        db.query(ShowRating)
        .filter(
            ShowRating.user_id == current_user.id,
            ShowRating.tv_show_id == tv_show_id
        )
        .first()
    )

    if existing_rating:
        raise HTTPException(
            status_code=409,
            detail="You have already rated this TV show"
        )

    # -----------------------------------------------------
    # Create rating
    # -----------------------------------------------------

    new_rating = ShowRating(
        user_id=current_user.id,
        tv_show_id=tv_show_id,
        rating=rating_data.rating
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)

    return new_rating


# =========================================================
# GET TV SHOW RATING
# =========================================================

@router.get(
    "/tv-shows/{tv_show_id}",
    response_model=ShowRatingResponse
)
def get_tv_show_rating(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    rating = (
        db.query(ShowRating)
        .filter(
            ShowRating.user_id == current_user.id,
            ShowRating.tv_show_id == tv_show_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this TV show"
        )

    return rating


# =========================================================
# UPDATE TV SHOW RATING
# =========================================================

@router.put(
    "/tv-shows/{tv_show_id}",
    response_model=ShowRatingResponse
)
def update_tv_show_rating(
    tv_show_id: int,
    rating_data: ShowRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Validate rating
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Find rating
    # -----------------------------------------------------

    rating = (
        db.query(ShowRating)
        .filter(
            ShowRating.user_id == current_user.id,
            ShowRating.tv_show_id == tv_show_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this TV show"
        )

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    rating.rating = rating_data.rating

    db.commit()
    db.refresh(rating)

    return rating


# =========================================================
# DELETE TV SHOW RATING
# =========================================================

@router.delete(
    "/tv-shows/{tv_show_id}"
)
def delete_tv_show_rating(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    rating = (
        db.query(ShowRating)
        .filter(
            ShowRating.user_id == current_user.id,
            ShowRating.tv_show_id == tv_show_id
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="You have not rated this TV show"
        )

    db.delete(rating)
    db.commit()

    return {
        "message": "TV show rating deleted",
        "tv_show_id": tv_show_id
    }