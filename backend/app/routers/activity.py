
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

    # Fetch only enough records from each source to cover the requested page.
    fetch_limit = limit + offset
    activities = []

    # 1. Diary entries
    diary_query = (
        db.query(DiaryEntry)
        .options(
            joinedload(DiaryEntry.movie),
            joinedload(DiaryEntry.episode),
            joinedload(DiaryEntry.user),
        )
        .filter(DiaryEntry.user_id.in_(following_ids))
    )
    total_diary = diary_query.count()

    entries = (
        diary_query
        .order_by(DiaryEntry.watched_at.desc(), DiaryEntry.id.desc())
        .limit(fetch_limit)
        .all()
    )

    for entry in entries:
        item = {
            "activity_type": (
                "movie_watched" if entry.movie else "episode_watched"
            ),
            "user_id": entry.user_id,
            "username": entry.user.username if entry.user else None,
            "display_name": (
                entry.user.display_name if entry.user else None
            ),
            "created_at": entry.watched_at,
            "rating": float(entry.rating) if entry.rating is not None else None,
            "notes": entry.notes,
            "rewatch": entry.rewatch,
            "movie": None,
            "show": None,
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

    # 2. Movie ratings
    movie_rating_query = (
        db.query(MovieRating)
        .options(
            joinedload(MovieRating.movie),
            joinedload(MovieRating.user),
        )
        .filter(MovieRating.user_id.in_(following_ids))
    )
    total_movie_ratings = movie_rating_query.count()

    movie_ratings = (
        movie_rating_query
        .order_by(
            MovieRating.updated_at.desc(),
            MovieRating.id.desc(),
        )
        .limit(fetch_limit)
        .all()
    )

    for rating in movie_ratings:
        activities.append({
            "activity_type": "movie_rated",
            "user_id": rating.user_id,
            "username": rating.user.username if rating.user else None,
            "display_name": (
                rating.user.display_name if rating.user else None
            ),
            "created_at": rating.updated_at or rating.created_at,
            "rating": float(rating.rating),
            "movie": {
                "id": rating.movie.id,
                "title": rating.movie.title,
            } if rating.movie else None,
            "show": None,
            "episode": None,
            "notes": None,
            "rewatch": None,
        })

    # 3. TV-show ratings
    show_rating_query = (
        db.query(ShowRating)
        .options(
            joinedload(ShowRating.tv_show),
            joinedload(ShowRating.user),
        )
        .filter(ShowRating.user_id.in_(following_ids))
    )
    total_show_ratings = show_rating_query.count()

    show_ratings = (
        show_rating_query
        .order_by(ShowRating.updated_at.desc(), ShowRating.id.desc())
        .limit(fetch_limit)
        .all()
    )

    for rating in show_ratings:
        activities.append({
            "activity_type": "show_rated",
            "user_id": rating.user_id,
            "username": rating.user.username if rating.user else None,
            "display_name": (
                rating.user.display_name if rating.user else None
            ),
            "created_at": rating.updated_at or rating.created_at,
            "rating": float(rating.rating),
            "show": {
                "id": rating.tv_show.id,
                "title": rating.tv_show.name,
            } if rating.tv_show else None,
            "movie": None,
            "episode": None,
            "notes": None,
            "rewatch": None,
        })

    # 4. Movie reviews
    movie_review_query = (
        db.query(MovieReview)
        .options(
            joinedload(MovieReview.movie),
            joinedload(MovieReview.user),
        )
        .filter(MovieReview.user_id.in_(following_ids))
    )
    total_movie_reviews = movie_review_query.count()

    movie_reviews = (
        movie_review_query
        .order_by(MovieReview.updated_at.desc(), MovieReview.id.desc())
        .limit(fetch_limit)
        .all()
    )

    for review in movie_reviews:
        activities.append({
            "activity_type": "movie_reviewed",
            "user_id": review.user_id,
            "username": review.user.username if review.user else None,
            "display_name": (
                review.user.display_name if review.user else None
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

    # 5. TV-show reviews
    show_review_query = (
        db.query(ShowReview)
        .options(
            joinedload(ShowReview.tv_show),
            joinedload(ShowReview.user),
        )
        .filter(ShowReview.user_id.in_(following_ids))
    )
    total_show_reviews = show_review_query.count()

    show_reviews = (
        show_review_query
        .order_by(ShowReview.updated_at.desc(), ShowReview.id.desc())
        .limit(fetch_limit)
        .all()
    )

    for review in show_reviews:
        activities.append({
            "activity_type": "show_reviewed",
            "user_id": review.user_id,
            "username": review.user.username if review.user else None,
            "display_name": (
                review.user.display_name if review.user else None
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

    # 6. Favorites
    favorite_query = (
        db.query(Favorite)
        .options(
            joinedload(Favorite.movie),
            joinedload(Favorite.tv_show),
            joinedload(Favorite.user),
        )
        .filter(Favorite.user_id.in_(following_ids))
    )
    total_favorites = favorite_query.count()

    favorites = (
        favorite_query
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .limit(fetch_limit)
        .all()
    )

    for favorite in favorites:
        movie = favorite.movie
        show = favorite.tv_show

        activities.append({
            "activity_type": (
                "movie_favorited" if movie else "show_favorited"
            ),
            "user_id": favorite.user_id,
            "username": (
                favorite.user.username if favorite.user else None
            ),
            "display_name": (
                favorite.user.display_name if favorite.user else None
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

    # Merge the limited results, sort newest first, and paginate.
    activities.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    total = (
        total_diary
        + total_movie_ratings
        + total_show_ratings
        + total_movie_reviews
        + total_show_reviews
        + total_favorites
    )

    page = activities[offset:offset + limit]

    return {
        "total_returned": len(page),
        "total_activities": total,
        "limit": limit,
        "offset": offset,
        "activities": page,
    }
