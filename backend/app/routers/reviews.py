from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    TVShow,
    ShowReview,
    Movie,
    MovieReview,
    User
)
from app.schemas import (
    ShowReviewCreate,
    ShowReviewResponse,
    MovieReviewCreate,
    MovieReviewResponse
)
from app.security import get_current_user


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


# =========================================================
# CREATE TV SHOW REVIEW
# =========================================================

@router.post(
    "/tv-shows/{tv_show_id}",
    response_model=ShowReviewResponse,
    status_code=201
)
def create_tv_show_review(
    tv_show_id: int,
    review_data: ShowReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

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
    # Validate review
    # -----------------------------------------------------

    if not review_data.review_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Review cannot be empty"
        )

    # -----------------------------------------------------
    # Create review
    # -----------------------------------------------------

    new_review = ShowReview(
        user_id=current_user.id,
        tv_show_id=tv_show_id,
        review_text=review_data.review_text,
        contains_spoilers=review_data.contains_spoilers
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


# =========================================================
# GET TV SHOW REVIEWS
# =========================================================

@router.get(
    "/tv-shows/{tv_show_id}",
    response_model=list[ShowReviewResponse]
)
def get_tv_show_reviews(
    tv_show_id: int,
    db: Session = Depends(get_db)
):

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
    # Get reviews
    # -----------------------------------------------------

    reviews = (
        db.query(ShowReview)
        .filter(
            ShowReview.tv_show_id == tv_show_id
        )
        .order_by(
            ShowReview.created_at.desc()
        )
        .all()
    )

    return reviews


# =========================================================
# UPDATE TV SHOW REVIEW
# =========================================================

@router.put(
    "/{review_id}",
    response_model=ShowReviewResponse
)
def update_tv_show_review(
    review_id: int,
    review_data: ShowReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Validate review
    # -----------------------------------------------------

    if not review_data.review_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Review cannot be empty"
        )

    # -----------------------------------------------------
    # Find user's review
    # -----------------------------------------------------

    review = (
        db.query(ShowReview)
        .filter(
            ShowReview.id == review_id,
            ShowReview.user_id == current_user.id
        )
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    review.review_text = review_data.review_text
    review.contains_spoilers = (
        review_data.contains_spoilers
    )

    db.commit()
    db.refresh(review)

    return review


# =========================================================
# DELETE TV SHOW REVIEW
# =========================================================

@router.delete(
    "/{review_id}"
)
def delete_tv_show_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    review = (
        db.query(ShowReview)
        .filter(
            ShowReview.id == review_id,
            ShowReview.user_id == current_user.id
        )
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    db.delete(review)
    db.commit()

    return {
        "message": "TV show review deleted",
        "review_id": review_id
    }

@router.post(
    "/movies/{movie_id}",
    response_model=MovieReviewResponse,
    status_code=201
)
def create_movie_review(
    movie_id: int,
    review_data: MovieReviewCreate,
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

    if not review_data.review_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Review cannot be empty"
        )

    review = MovieReview(
        user_id=current_user.id,
        movie_id=movie_id,
        review_text=review_data.review_text.strip(),
        contains_spoilers=review_data.contains_spoilers
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get(
    "/movies/{movie_id}",
    response_model=list[MovieReviewResponse]
)
def get_movie_reviews(
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

    reviews = (
        db.query(MovieReview)
        .filter(MovieReview.movie_id == movie_id)
        .order_by(MovieReview.created_at.desc())
        .all()
    )

    return reviews


@router.put(
    "/movies/{review_id}",
    response_model=MovieReviewResponse
)
def update_movie_review(
    review_id: int,
    review_data: MovieReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = (
        db.query(MovieReview)
        .filter(
            MovieReview.id == review_id,
            MovieReview.user_id == current_user.id
        )
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Movie review not found"
        )

    if not review_data.review_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Review cannot be empty"
        )

    review.review_text = review_data.review_text.strip()
    review.contains_spoilers = review_data.contains_spoilers

    db.commit()
    db.refresh(review)

    return review


@router.delete(
    "/movies/{review_id}"
)
def delete_movie_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = (
        db.query(MovieReview)
        .filter(
            MovieReview.id == review_id,
            MovieReview.user_id == current_user.id
        )
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Movie review not found"
        )

    db.delete(review)
    db.commit()

    return {
        "message": "Movie review deleted",
        "review_id": review_id
    }