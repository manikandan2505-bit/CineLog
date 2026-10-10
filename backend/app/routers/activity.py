
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    User,
    UserFollow,
    DiaryEntry,
    MovieRating,
    ShowRating,
    MovieReview,
    ShowReview,
    Favorite,
)
from app.security import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity Feed"])



@router.get("/following")
def get_following_activity(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    following_ids = (
        db.query(UserFollow.following_id)
        .filter(UserFollow.follower_id == current_user.id)
        .subquery()
    )

    activities = []

    # 1. Diary activities
    entries = (
        db.query(DiaryEntry)
        .options(
            joinedload(DiaryEntry.movie),
            joinedload(DiaryEntry.episode),
            joinedload(DiaryEntry.user),
        )
        .filter(DiaryEntry.user_id.in_(following_ids))
        .all()
    )

    for entry in entries:
        item = {
            "activity_type": (
                "movie_watched"
                if entry.movie
                else "episode_watched"
            ),
            "user_id": entry.user_id,
            "username": entry.user.username if entry.user else None,
            "display_name": (
                entry.user.display_name if entry.user else None
            ),
            "created_at": entry.watched_at,
            "rating": entry.rating,
            "notes": entry.notes,
            "rewatch": entry.rewatch,
            "movie": None,
            "episode": None,
        }

        if entry.movie:
            item["movie"] = {
                "id": entry.movie.id,
                "title": entry.movie.title,
            }

        if entry.episode:
            item["episode"] = {
                "id": entry.episode.id,
                "title": entry.episode.name,
                "episode_number": entry.episode.episode_number,
                "season_id": entry.episode.season_id,
            }

        activities.append(item)

    # 2. Movie rating activities
    movie_ratings = (
        db.query(MovieRating)
        .options(
            joinedload(MovieRating.movie),
        )
        .filter(MovieRating.user_id.in_(following_ids))
        .all()
    )

    for rating in movie_ratings:
        activities.append({
            "activity_type": "movie_rated",
            "user_id": rating.user_id,
            "username": (
                db.query(User.username)
                .filter(User.id == rating.user_id)
                .scalar()
            ),
            "created_at": rating.updated_at or rating.created_at,
            "rating": float(rating.rating),
            "movie": {
                "id": rating.movie.id,
                "title": rating.movie.title,
            } if rating.movie else None,
            "episode": None,
            "notes": None,
            "rewatch": None,
        })

    # 3. TV-show rating activities
    show_ratings = (
        db.query(ShowRating)
        .options(
            joinedload(ShowRating.tv_show),
        )
        .filter(ShowRating.user_id.in_(following_ids))
        .all()
    )

    for rating in show_ratings:
        activities.append({
            "activity_type": "show_rated",
            "user_id": rating.user_id,
            "username": (
                db.query(User.username)
                .filter(User.id == rating.user_id)
                .scalar()
            ),
            "created_at": rating.updated_at or rating.created_at,
            "rating": float(rating.rating),
            "show": {
                "id": rating.tv_show.id,
                "name": rating.tv_show.name,
            } if rating.tv_show else None,
            "movie": None,
            "episode": None,
            "notes": None,
            "rewatch": None,
        })

    # 4. Movie review activities
    movie_reviews = (
        db.query(MovieReview)
        .options(joinedload(MovieReview.movie))
        .filter(MovieReview.user_id.in_(following_ids))
        .all()
    )

    for review in movie_reviews:
        reviewer = (
            db.query(User)
            .filter(User.id == review.user_id)
            .first()
        )

        activities.append({
            "activity_type": "movie_reviewed",
            "user_id": review.user_id,
            "username": reviewer.username if reviewer else None,
            "display_name": (
                reviewer.display_name if reviewer else None
            ),
            "created_at": review.updated_at or review.created_at,
            "review_text": review.review_text,
            "contains_spoilers": review.contains_spoilers,
            "movie": {
                "id": review.movie.id,
                "title": review.movie.title,
            } if review.movie else None,
            "show": None,
            "episode": None,
            "rating": None,
            "notes": None,
            "rewatch": None,
        })

    # 5. TV-show review activities
    show_reviews = (
        db.query(ShowReview)
        .options(joinedload(ShowReview.tv_show))
        .filter(ShowReview.user_id.in_(following_ids))
        .all()
    )

    for review in show_reviews:
        reviewer = (
            db.query(User)
            .filter(User.id == review.user_id)
            .first()
        )

        activities.append({
            "activity_type": "show_reviewed",
            "user_id": review.user_id,
            "username": reviewer.username if reviewer else None,
            "display_name": (
                reviewer.display_name if reviewer else None
            ),
            "created_at": review.updated_at or review.created_at,
            "review_text": review.review_text,
            "contains_spoilers": review.contains_spoilers,
            "show": {
                "id": review.tv_show.id,
                "title": review.tv_show.name,
            } if review.tv_show else None,
            "movie": None,
            "episode": None,
            "rating": None,
            "notes": None,
            "rewatch": None,
        })

    # 6. Favorite activities
    favorites = (
        db.query(Favorite)
        .options(
            joinedload(Favorite.movie),
            joinedload(Favorite.tv_show),
        )
        .filter(Favorite.user_id.in_(following_ids))
        .all()
    )

    for favorite in favorites:
        user = (
            db.query(User)
            .filter(User.id == favorite.user_id)
            .first()
        )

        movie = favorite.movie
        show = favorite.tv_show

        activities.append({
            "activity_type": (
                "movie_favorited" if movie
                else "show_favorited"
            ),
            "user_id": favorite.user_id,
            "username": user.username if user else None,
            "display_name": (
                user.display_name if user else None
            ),
            "created_at": favorite.created_at,
            "movie": {
                "id": movie.id,
                "title": movie.title,
            } if movie else None,
            "show": {
                "id": show.id,
                "title": show.name,
            } if show else None,
            "episode": None,
            "rating": None,
            "notes": None,
            "rewatch": None,
        })


    # Sort all activity types newest first, then paginate
    activities.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    total = len(activities)
    page = activities[offset:offset + limit]

    return {
        "total_returned": len(page),
        "total_activities": total,
        "limit": limit,
        "offset": offset,
        "activities": page,
    }
