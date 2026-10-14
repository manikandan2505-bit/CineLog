from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func,extract,case
from datetime import date,timedelta


from app.database import get_db
from app.models import User,Movie,DiaryEntry,MovieGenre,Genre,TVShow,Season,Episode,MovieRating,ShowRating,MovieReview,ShowReview,Favorite,WatchlistItem,UserFollow
from app.schemas import (
    UserCreate,
    UserResponse,
    UserProfileStatsResponse,
    UserProfileUpdate,
    PasswordChange,
    AccountDeleteRequest,
    PublicUserProfileResponse,
    UserLogin
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_optional_current_user,
    get_current_user
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return users


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_username = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    existing_email = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        bio=user_data.bio,
        avatar_url=user_data.avatar_url
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        form_data.password,
        user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/{username}", response_model=PublicUserProfileResponse)
def get_public_user_profile(
    username: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    is_following = None

    if current_user is not None:
        is_following = (
                db.query(UserFollow)
                .filter(
                    UserFollow.follower_id == current_user.id,
                    UserFollow.following_id == user.id
                )
                .first()
                is not None
        )

    # Count distinct movies watched
    movie_ids = db.query(DiaryEntry.movie_id).filter(
        DiaryEntry.user_id == user.id,
        DiaryEntry.movie_id.isnot(None)
    ).distinct().all()

    total_movies_watched = len(movie_ids)

    # Count distinct episodes watched
    episode_ids = db.query(DiaryEntry.episode_id).filter(
        DiaryEntry.user_id == user.id,
        DiaryEntry.episode_id.isnot(None)
    ).distinct().all()

    total_episodes_watched = len(episode_ids)

    # Count ratings
    total_movie_ratings = db.query(MovieRating).filter(
        MovieRating.user_id == user.id
    ).count()

    total_show_ratings = db.query(ShowRating).filter(
        ShowRating.user_id == user.id
    ).count()

    # Count reviews
    total_movie_reviews = db.query(MovieReview).filter(
        MovieReview.user_id == user.id
    ).count()

    total_show_reviews = db.query(ShowReview).filter(
        ShowReview.user_id == user.id
    ).count()

    total_reviews = total_movie_reviews + total_show_reviews

    # Count favorites
    total_favorites = db.query(Favorite).filter(
        Favorite.user_id == user.id
    ).count()

    total_followers = (
        db.query(UserFollow)
        .filter(UserFollow.following_id == user.id)
        .count()
    )

    total_following = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == user.id)
        .count()
    )


    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "total_movies_watched": total_movies_watched,
        "total_episodes_watched": total_episodes_watched,
        "total_movie_ratings": total_movie_ratings,
        "total_show_ratings": total_show_ratings,
        "total_reviews": total_reviews,
        "total_favorites": total_favorites,
        "total_followers": total_followers,
        "total_following": total_following,
        "is_following": is_following,
    }


@router.get("/me/stats", response_model=UserProfileStatsResponse)
def get_current_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id

    # Get this user's diary entries
    diary_entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == user_id
    ).all()

    # Count distinct movies watched
    total_movies_watched = len({
        entry.movie_id
        for entry in diary_entries
        if entry.movie_id is not None
    })

    # Count movie rewatches
    total_movie_rewatches = sum(
        1 for entry in diary_entries
        if entry.movie_id is not None and entry.rewatch
    )

    # Count distinct episodes watched
    total_episodes_watched = len({
        entry.episode_id
        for entry in diary_entries
        if entry.episode_id is not None
    })

    # Count distinct TV shows tracked through diary activity
    episode_ids = {
        entry.episode_id
        for entry in diary_entries
        if entry.episode_id is not None
    }

    show_ids = set()

    if episode_ids:
        from app.models import Episode

        episodes = db.query(Episode).filter(
            Episode.id.in_(episode_ids)
        ).all()

        show_ids = {
            episode.season.tv_show_id
            for episode in episodes
            if episode.season is not None
        }


    total_movie_ratings = db.query(MovieRating).filter(
        MovieRating.user_id == user_id
    ).count()

    total_show_ratings = db.query(ShowRating).filter(
        ShowRating.user_id == user_id
    ).count()


    # Calculate average movie rating
    average_movie_rating = (
        db.query(func.avg(MovieRating.rating))
        .filter(MovieRating.user_id == user_id)
        .scalar()
    )

    # Calculate average TV-show rating
    average_show_rating = (
        db.query(func.avg(ShowRating.rating))
        .filter(ShowRating.user_id == user_id)
        .scalar()
    )

    if average_movie_rating is not None:
        average_movie_rating = round(float(average_movie_rating), 2)

    if average_show_rating is not None:
        average_show_rating = round(float(average_show_rating), 2)

    total_movie_reviews = db.query(MovieReview).filter(
        MovieReview.user_id == user_id
    ).count()

    total_show_reviews = db.query(ShowReview).filter(
        ShowReview.user_id == user_id
    ).count()

    total_reviews = total_movie_reviews + total_show_reviews


    total_favorites = db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).count()


    total_watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user_id
    ).count()

    return {
        "total_movies_watched": total_movies_watched,
        "total_movie_rewatches": total_movie_rewatches,
        "total_episodes_watched": total_episodes_watched,
        "total_shows_tracked": len(show_ids),
        "total_movie_ratings": total_movie_ratings,
        "total_show_ratings": total_show_ratings,
        "average_movie_rating": average_movie_rating,
        "average_show_rating": average_show_rating,
        "total_diary_entries": len(diary_entries),
        "total_reviews": total_reviews,
        "total_favorites": total_favorites,
        "total_watchlist_items": total_watchlist_items
    }


@router.get("/me/stats/monthly")
def get_monthly_viewing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            extract("month", DiaryEntry.watched_at).label("month"),
            func.sum(
                case(
                    (DiaryEntry.movie_id.isnot(None), 1),
                    else_=0,
                )
            ).label("movies_watched"),
            func.sum(
                case(
                    (DiaryEntry.episode_id.isnot(None), 1),
                    else_=0,
                )
            ).label("episodes_watched"),
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(
            extract("year", DiaryEntry.watched_at),
            extract("month", DiaryEntry.watched_at),
        )
        .order_by(
            extract("year", DiaryEntry.watched_at),
            extract("month", DiaryEntry.watched_at),
        )
        .all()
    )

    return {
        "monthly_stats": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "movies_watched": int(row.movies_watched or 0),
                "episodes_watched": int(row.episodes_watched or 0),
            }
            for row in results
        ]
    }


@router.get("/me/stats/yearly")
def get_yearly_viewing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            func.sum(
                case(
                    (DiaryEntry.movie_id.isnot(None), 1),
                    else_=0,
                )
            ).label("movies_watched"),
            func.sum(
                case(
                    (DiaryEntry.episode_id.isnot(None), 1),
                    else_=0,
                )
            ).label("episodes_watched"),
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(extract("year", DiaryEntry.watched_at))
        .order_by(extract("year", DiaryEntry.watched_at))
        .all()
    )

    return {
        "yearly_stats": [
            {
                "year": int(row.year),
                "movies_watched": int(row.movies_watched or 0),
                "episodes_watched": int(row.episodes_watched or 0),
            }
            for row in results
        ]
    }


@router.get("/me/stats/genres")
def get_genre_viewing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            Genre.id.label("genre_id"),
            Genre.name.label("genre"),
            func.count(DiaryEntry.id).label("diary_entries"),
        )
        .join(
            MovieGenre,
            MovieGenre.genre_id == Genre.id,
        )
        .join(
            DiaryEntry,
            DiaryEntry.movie_id == MovieGenre.movie_id,
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(Genre.id, Genre.name)
        .order_by(func.count(DiaryEntry.id).desc(), Genre.name.asc())
        .all()
    )

    return {
        "genre_stats": [
            {
                "genre_id": row.genre_id,
                "genre": row.genre,
                "diary_entries": row.diary_entries,
            }
            for row in results
        ]
    }


@router.get("/me/stats/ratings")
def get_movie_rating_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            MovieRating.rating.label("rating"),
            func.count(MovieRating.id).label("count"),
        )
        .filter(MovieRating.user_id == current_user.id)
        .group_by(MovieRating.rating)
        .order_by(MovieRating.rating.asc())
        .all()
    )

    return {
        "rating_distribution": [
            {
                "rating": float(row.rating),
                "count": row.count,
            }
            for row in results
        ]
    }


@router.get("/me/stats/show-ratings")
def get_show_rating_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            ShowRating.rating.label("rating"),
            func.count(ShowRating.id).label("count"),
        )
        .filter(ShowRating.user_id == current_user.id)
        .group_by(ShowRating.rating)
        .order_by(ShowRating.rating.asc())
        .all()
    )

    return {
        "rating_distribution": [
            {
                "rating": float(row.rating),
                "count": row.count,
            }
            for row in results
        ]
    }


@router.get("/me/stats/most-watched-movies")
def get_most_watched_movies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            Movie.id.label("movie_id"),
            Movie.title.label("title"),
            func.count(DiaryEntry.id).label("watch_count"),
        )
        .join(
            DiaryEntry,
            DiaryEntry.movie_id == Movie.id,
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(Movie.id, Movie.title)
        .order_by(
            func.count(DiaryEntry.id).desc(),
            Movie.title.asc(),
        )
        .limit(10)
        .all()
    )

    return {
        "most_watched_movies": [
            {
                "movie_id": row.movie_id,
                "title": row.title,
                "watch_count": row.watch_count,
            }
            for row in results
        ]
    }


@router.get("/me/stats/most-watched-shows")
def get_most_watched_shows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            TVShow.id.label("show_id"),
            TVShow.name.label("title"),
            func.count(
                func.distinct(DiaryEntry.episode_id)
            ).label("episodes_watched"),
        )
        .join(
            Season,
            Season.tv_show_id == TVShow.id,
        )
        .join(
            Episode,
            Episode.season_id == Season.id,
        )
        .join(
            DiaryEntry,
            DiaryEntry.episode_id == Episode.id,
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(TVShow.id, TVShow.name)
        .order_by(
            func.count(
                func.distinct(DiaryEntry.episode_id)
            ).desc(),
            TVShow.name.asc(),
        )
        .limit(10)
        .all()
    )

    return {
        "most_watched_shows": [
            {
                "show_id": row.show_id,
                "title": row.title,
                "episodes_watched": row.episodes_watched,
            }
            for row in results
        ]
    }


@router.get("/me/stats/recently-watched")
def get_recently_watched(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 50))

    # Recently watched movies
    movie_entries = (
        db.query(
            DiaryEntry.id.label("diary_entry_id"),
            DiaryEntry.watched_at.label("watched_at"),
            DiaryEntry.rating.label("rating"),
            DiaryEntry.rewatch.label("rewatch"),
            Movie.id.label("item_id"),
            Movie.title.label("title"),
        )
        .join(Movie, DiaryEntry.movie_id == Movie.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.movie_id.isnot(None),
        )
        .order_by(DiaryEntry.watched_at.desc(), DiaryEntry.id.desc())
        .limit(limit)
        .all()
    )

    # Recently watched TV episodes
    episode_entries = (
        db.query(
            DiaryEntry.id.label("diary_entry_id"),
            DiaryEntry.watched_at.label("watched_at"),
            DiaryEntry.rating.label("rating"),
            DiaryEntry.rewatch.label("rewatch"),
            Episode.id.label("item_id"),
            Episode.name.label("episode_title"),
            Episode.episode_number.label("episode_number"),
            Season.season_number.label("season_number"),
            TVShow.id.label("show_id"),
            TVShow.name.label("show_title"),
        )
        .join(Episode, DiaryEntry.episode_id == Episode.id)
        .join(Season, Episode.season_id == Season.id)
        .join(TVShow, Season.tv_show_id == TVShow.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id.isnot(None),
        )
        .order_by(DiaryEntry.watched_at.desc(), DiaryEntry.id.desc())
        .limit(limit)
        .all()
    )

    activities = []

    for row in movie_entries:
        activities.append({
            "diary_entry_id": row.diary_entry_id,
            "type": "movie",
            "item_id": row.item_id,
            "title": row.title,
            "watched_at": row.watched_at,
            "rating": float(row.rating) if row.rating is not None else None,
            "rewatch": row.rewatch,
        })

    for row in episode_entries:
        activities.append({
            "diary_entry_id": row.diary_entry_id,
            "type": "episode",
            "item_id": row.item_id,
            "title": row.episode_title,
            "show_id": row.show_id,
            "show_title": row.show_title,
            "season_number": row.season_number,
            "episode_number": row.episode_number,
            "watched_at": row.watched_at,
            "rating": float(row.rating) if row.rating is not None else None,
            "rewatch": row.rewatch,
        })

    activities.sort(
        key=lambda item: (
            item["watched_at"],
            item["diary_entry_id"],
        ),
        reverse=True,
    )

    return {
        "recently_watched": activities[:limit],
        "count": min(len(activities), limit),
    }


@router.get("/me/stats/watch-time")
def get_watch_time_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Movie diary entries: rewatches count as additional viewings.

    movie_rows = (
        db.query(
            Movie.runtime.label("runtime"),
        )
        .select_from(DiaryEntry)
        .join(Movie, DiaryEntry.movie_id == Movie.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.movie_id.isnot(None),
        )
        .all()
    )


    # Distinct episodes: repeated diary entries for the same
    # episode count only once in this estimate.
    episode_rows = (
        db.query(
            Episode.id.label("episode_id"),
            Episode.runtime.label("runtime"),
        )
        .join(
            DiaryEntry,
            DiaryEntry.episode_id == Episode.id,
        )
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id.isnot(None),
        )
        .group_by(Episode.id, Episode.runtime)
        .all()
    )

    movie_minutes = sum(
        int(row.runtime)
        for row in movie_rows
        if row.runtime is not None
    )

    episode_minutes = sum(
        int(row.runtime)
        for row in episode_rows
        if row.runtime is not None
    )

    missing_movie_runtime = sum(
        1 for row in movie_rows
        if row.runtime is None
    )

    missing_episode_runtime = sum(
        1 for row in episode_rows
        if row.runtime is None
    )

    total_minutes = movie_minutes + episode_minutes

    return {
        "movie_watch_time_minutes": movie_minutes,
        "episode_watch_time_minutes": episode_minutes,
        "total_watch_time_minutes": total_minutes,
        "total_watch_time_hours": round(total_minutes / 60, 2),
        "missing_movie_runtime_entries": missing_movie_runtime,
        "missing_episode_runtime_entries": missing_episode_runtime,
    }


@router.get("/me/stats/watch-time/yearly")
def get_yearly_watch_time_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Movie watch time grouped by the year watched
    movie_rows = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            func.sum(Movie.runtime).label("total_minutes"),
        )
        .select_from(DiaryEntry)
        .join(Movie, DiaryEntry.movie_id == Movie.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.movie_id.isnot(None),
        )
        .group_by(extract("year", DiaryEntry.watched_at))
        .all()
    )

    # Distinct TV episodes grouped by the year watched

    episode_rows = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            Episode.id.label("episode_id"),
            func.max(Episode.runtime).label("runtime"),
        )
        .select_from(DiaryEntry)
        .join(Episode, DiaryEntry.episode_id == Episode.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id.isnot(None),
        )
        .group_by(
            extract("year", DiaryEntry.watched_at),
            Episode.id,
        )
        .all()
    )

    yearly_stats = {}

    for row in movie_rows:
        year = int(row.year)
        yearly_stats.setdefault(
            year,
            {"movie_watch_time_minutes": 0, "episode_watch_time_minutes": 0},
        )
        yearly_stats[year]["movie_watch_time_minutes"] += int(
            row.total_minutes or 0
        )

    # Avoid counting the same episode more than once per year.
    seen_episodes = set()

    for row in episode_rows:
        year = int(row.year)
        yearly_stats.setdefault(
            year,
            {
                "movie_watch_time_minutes": 0,
                "episode_watch_time_minutes": 0,
            },
        )
        yearly_stats[year]["episode_watch_time_minutes"] += int(
            row.runtime or 0
        )


    return {
        "yearly_stats": [
            {
                "year": year,
                **stats,
                "total_watch_time_minutes": (
                    stats["movie_watch_time_minutes"]
                    + stats["episode_watch_time_minutes"]
                ),
                "total_watch_time_hours": round(
                    (
                        stats["movie_watch_time_minutes"]
                        + stats["episode_watch_time_minutes"]
                    ) / 60,
                    2,
                ),
            }
            for year, stats in sorted(yearly_stats.items())
        ]
    }


@router.get("/me/stats/watch-time/monthly")
def get_monthly_watch_time_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Movie watch time: each diary entry counts,
    # including rewatches.
    movie_rows = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            extract("month", DiaryEntry.watched_at).label("month"),
            func.sum(Movie.runtime).label("total_minutes"),
        )
        .select_from(DiaryEntry)
        .join(Movie, DiaryEntry.movie_id == Movie.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.movie_id.isnot(None),
        )
        .group_by(
            extract("year", DiaryEntry.watched_at),
            extract("month", DiaryEntry.watched_at),
        )
        .all()
    )

    # Episode watch time: count each episode once per month.
    episode_rows = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            extract("month", DiaryEntry.watched_at).label("month"),
            Episode.id.label("episode_id"),
            func.max(Episode.runtime).label("runtime"),
        )
        .select_from(DiaryEntry)
        .join(Episode, DiaryEntry.episode_id == Episode.id)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id.isnot(None),
        )
        .group_by(
            extract("year", DiaryEntry.watched_at),
            extract("month", DiaryEntry.watched_at),
            Episode.id,
        )
        .all()
    )

    monthly_stats = {}

    def ensure_month(year, month):
        key = (year, month)
        if key not in monthly_stats:
            monthly_stats[key] = {
                "movie_watch_time_minutes": 0,
                "episode_watch_time_minutes": 0,
            }
        return monthly_stats[key]

    for row in movie_rows:
        year = int(row.year)
        month = int(row.month)
        stats = ensure_month(year, month)
        stats["movie_watch_time_minutes"] += int(
            row.total_minutes or 0
        )

    for row in episode_rows:
        year = int(row.year)
        month = int(row.month)
        stats = ensure_month(year, month)
        stats["episode_watch_time_minutes"] += int(
            row.runtime or 0
        )

    return {
        "monthly_stats": [
            {
                "year": year,
                "month": month,
                **stats,
                "total_watch_time_minutes": (
                    stats["movie_watch_time_minutes"]
                    + stats["episode_watch_time_minutes"]
                ),
                "total_watch_time_hours": round(
                    (
                        stats["movie_watch_time_minutes"]
                        + stats["episode_watch_time_minutes"]
                    ) / 60,
                    2,
                ),
            }
            for (year, month), stats in sorted(monthly_stats.items())
        ]
    }


@router.get("/me/stats/streaks")
def get_viewing_streaks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watched_dates = (
        db.query(DiaryEntry.watched_at)
        .filter(DiaryEntry.user_id == current_user.id)
        .all()
    )

    active_dates = sorted({
        row.watched_at.date()
        for row in watched_dates
        if row.watched_at is not None
    })

    if not active_dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_active_days": 0,
            "last_active_date": None,
        }

    # Calculate the longest streak.
    longest_streak = 1
    running_streak = 1

    for index in range(1, len(active_dates)):
        if active_dates[index] == (
            active_dates[index - 1] + timedelta(days=1)
        ):
            running_streak += 1
        else:
            running_streak = 1

        longest_streak = max(longest_streak, running_streak)

    # Calculate the current streak.
    today = date.today()
    last_active_date = active_dates[-1]

    if last_active_date == today or last_active_date == today - timedelta(days=1):
        current_streak = 1

        for index in range(len(active_dates) - 1, 0, -1):
            if active_dates[index] == (
                active_dates[index - 1] + timedelta(days=1)
            ):
                current_streak += 1
            else:
                break
    else:
        current_streak = 0

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_active_days": len(active_dates),
        "last_active_date": last_active_date.isoformat(),
    }

@router.get("/me/stats/daily")
def get_daily_viewing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30,
):
    days = max(1, min(days, 365))
    start_date = date.today() - timedelta(days=days - 1)

    results = (
        db.query(
            func.date(DiaryEntry.watched_at).label("date"),
            func.sum(
                case(
                    (DiaryEntry.movie_id.isnot(None), 1),
                    else_=0,
                )
            ).label("movies_logged"),
            func.sum(
                case(
                    (DiaryEntry.episode_id.isnot(None), 1),
                    else_=0,
                )
            ).label("episodes_logged"),
        )
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.watched_at >= start_date,
        )
        .group_by(func.date(DiaryEntry.watched_at))
        .order_by(func.date(DiaryEntry.watched_at))
        .all()
    )

    return {
        "daily_stats": [
            {
                "date": row.date.isoformat(),
                "movies_logged": int(row.movies_logged or 0),
                "episodes_logged": int(row.episodes_logged or 0),
                "total_logged": int(
                    (row.movies_logged or 0) + (row.episodes_logged or 0)
                ),
            }
            for row in results
        ]
    }


@router.get("/me/stats/weekly")
def get_weekly_viewing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    weeks: int = 12,
):
    weeks = max(1, min(weeks, 52))
    start_date = date.today() - timedelta(weeks=weeks)

    results = (
        db.query(
            extract("year", DiaryEntry.watched_at).label("year"),
            func.week(DiaryEntry.watched_at, 3).label("week"),
            func.sum(
                case(
                    (DiaryEntry.movie_id.isnot(None), 1),
                    else_=0,
                )
            ).label("movies_logged"),
            func.sum(
                case(
                    (DiaryEntry.episode_id.isnot(None), 1),
                    else_=0,
                )
            ).label("episodes_logged"),
        )
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.watched_at >= start_date,
        )
        .group_by(
            extract("year", DiaryEntry.watched_at),
            func.week(DiaryEntry.watched_at, 3),
        )
        .order_by(
            extract("year", DiaryEntry.watched_at),
            func.week(DiaryEntry.watched_at, 3),
        )
        .all()
    )

    return {
        "weekly_stats": [
            {
                "year": int(row.year),
                "week": int(row.week),
                "movies_logged": int(row.movies_logged or 0),
                "episodes_logged": int(row.episodes_logged or 0),
                "total_logged": int(
                    (row.movies_logged or 0) + (row.episodes_logged or 0)
                ),
            }
            for row in results
        ]
    }


@router.get("/me/stats/day-of-week")
def get_day_of_week_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            func.dayofweek(DiaryEntry.watched_at).label("day_number"),
            func.sum(
                case(
                    (DiaryEntry.movie_id.isnot(None), 1),
                    else_=0,
                )
            ).label("movies_logged"),
            func.sum(
                case(
                    (DiaryEntry.episode_id.isnot(None), 1),
                    else_=0,
                )
            ).label("episodes_logged"),
        )
        .filter(DiaryEntry.user_id == current_user.id)
        .group_by(func.dayofweek(DiaryEntry.watched_at))
        .order_by(func.dayofweek(DiaryEntry.watched_at))
        .all()
    )

    day_names = {
        1: "Sunday",
        2: "Monday",
        3: "Tuesday",
        4: "Wednesday",
        5: "Thursday",
        6: "Friday",
        7: "Saturday",
    }

    return {
        "day_of_week_stats": [
            {
                "day": day_names[int(row.day_number)],
                "movies_logged": int(row.movies_logged or 0),
                "episodes_logged": int(row.episodes_logged or 0),
                "total_logged": int(
                    (row.movies_logged or 0) + (row.episodes_logged or 0)
                ),
            }
            for row in results
        ]
    }


@router.get("/me/stats/favorite-genres")
def get_favorite_genres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            Genre.id.label("genre_id"),
            Genre.name.label("genre"),
            func.count(
                func.distinct(MovieRating.movie_id)
            ).label("rated_movies"),
            func.avg(MovieRating.rating).label("average_rating"),
        )
        .join(
            MovieGenre,
            MovieGenre.genre_id == Genre.id,
        )
        .join(
            MovieRating,
            MovieRating.movie_id == MovieGenre.movie_id,
        )
        .filter(MovieRating.user_id == current_user.id)
        .group_by(Genre.id, Genre.name)
        .order_by(
            func.avg(MovieRating.rating).desc(),
            func.count(func.distinct(MovieRating.movie_id)).desc(),
            Genre.name.asc(),
        )
        .all()
    )

    return {
        "favorite_genres": [
            {
                "genre_id": row.genre_id,
                "genre": row.genre,
                "rated_movies": row.rated_movies,
                "average_rating": (
                    round(float(row.average_rating), 2)
                    if row.average_rating is not None
                    else None
                ),
            }
            for row in results
        ]
    }


@router.get("/me/stats/most-reviewed-movies")
def get_most_reviewed_movies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            Movie.id.label("movie_id"),
            Movie.title.label("title"),
            func.count(MovieReview.id).label("review_count"),
        )
        .select_from(MovieReview)
        .join(Movie, MovieReview.movie_id == Movie.id)
        .filter(MovieReview.user_id == current_user.id)
        .group_by(Movie.id, Movie.title)
        .order_by(
            func.count(MovieReview.id).desc(),
            Movie.title.asc(),
        )
        .limit(10)
        .all()
    )

    return {
        "most_reviewed_movies": [
            {
                "movie_id": row.movie_id,
                "title": row.title,
                "review_count": row.review_count,
            }
            for row in results
        ]
    }


@router.get("/me/stats/most-reviewed-shows")
def get_most_reviewed_shows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            TVShow.id.label("show_id"),
            TVShow.name.label("title"),
            func.count(ShowReview.id).label("review_count"),
        )
        .select_from(ShowReview)
        .join(TVShow, ShowReview.tv_show_id == TVShow.id)
        .filter(ShowReview.user_id == current_user.id)
        .group_by(TVShow.id, TVShow.name)
        .order_by(
            func.count(ShowReview.id).desc(),
            TVShow.name.asc(),
        )
        .limit(10)
        .all()
    )

    return {
        "most_reviewed_shows": [
            {
                "show_id": row.show_id,
                "title": row.title,
                "review_count": row.review_count,
            }
            for row in results
        ]
    }


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/password")
def change_current_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify the current password
    if not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # Prevent reusing the current password
    if verify_password(
        password_data.new_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    # Hash and save the new password
    current_user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_current_user_account(
    password_data: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}

