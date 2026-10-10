from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.services.movie_service import import_tv_show

from app.models import (
    TVShow,
    Season,
    Episode,
    DiaryEntry,
    ShowRating,
    ShowReview,
    WatchlistItem,
    Favorite,
    User
)

from app.security import get_current_user
from app.schemas import TVShowDetailsResponse
from app.schemas import EpisodeDetailsResponse
from app.tmdb import (
    search_tv_shows,
    get_tv_show_details,
    get_season_details
)


router = APIRouter(
    prefix="/tv-shows",
    tags=["TV Shows"]
)


# =========================================================
# TMDB SEARCH
# =========================================================

@router.get("/search")
async def tv_show_search(query: str):

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )

    try:
        results = await search_tv_shows(query)

        return {
            "query": query,
            "results": results.get("results", [])
        }

    except Exception as error:
        print(
            "TV SHOW SEARCH ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to search TV shows"
        )


# =========================================================
# TMDB TV SHOW DETAILS
# =========================================================

@router.get("/tmdb/{tmdb_id}")
async def tv_show_details(tmdb_id: int):

    try:
        show = await get_tv_show_details(tmdb_id)

        return show

    except Exception as error:
        print(
            "TV SHOW ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch TV show details: "
                f"{str(error)}"
            )
        )


# =========================================================
# TMDB SEASON DETAILS
# =========================================================

@router.get(
    "/tmdb/{tmdb_id}/season/{season_number}"
)
async def season_details(
    tmdb_id: int,
    season_number: int
):

    if season_number < 0:
        raise HTTPException(
            status_code=400,
            detail="Season number cannot be negative"
        )

    try:
        season = await get_season_details(
            tmdb_id,
            season_number
        )

        return season

    except Exception as error:
        print(
            "SEASON ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch season details: "
                f"{str(error)}"
            )
        )


# =========================================================
# IMPORT TV SHOW
# =========================================================

@router.post("/import/{tmdb_id}")
async def import_tv_show_endpoint(
    tmdb_id: int,
    db: Session = Depends(get_db)
):

    try:
        show = await import_tv_show(
            db,
            tmdb_id
        )

        return {
            "message": "TV show imported successfully",
            "show_id": show.id,
            "tmdb_id": show.tmdb_id,
            "name": show.name
        }

    except Exception as error:
        db.rollback()

        print(
            "TV SHOW IMPORT ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import TV show: "
                f"{str(error)}"
            )
        )

@router.get(
    "/episodes/{episode_id}/details",
    response_model=EpisodeDetailsResponse
)
def get_episode_details(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # -----------------------------------
    # Get episode
    # -----------------------------------

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

    # -----------------------------------
    # Get season
    # -----------------------------------

    season = (
        db.query(Season)
        .filter(Season.id == episode.season_id)
        .first()
    )

    if not season:
        raise HTTPException(
            status_code=404,
            detail="Season not found"
        )

    # -----------------------------------
    # Get user's diary entries
    # -----------------------------------

    diary_entries = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.episode_id == episode_id,
            DiaryEntry.user_id == current_user.id
        )
        .order_by(
            DiaryEntry.watched_at.desc(),
            DiaryEntry.id.desc()
        )
        .all()
    )

    # -----------------------------------
    # Watch information
    # -----------------------------------

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

    latest_watched_at = (
        latest_entry.watched_at
        if latest_entry
        else None
    )

    # -----------------------------------
    # User rating/review/notes
    # -----------------------------------

    user_rating = latest_rating

    user_review = latest_review

    user_notes = (
        latest_entry.notes
        if latest_entry
        else None
    )

    # -----------------------------------
    # Rewatch count
    # -----------------------------------

    user_rewatch_count = sum(
        1
        for entry in diary_entries
        if entry.rewatch
    )

    # -----------------------------------
    # Final response
    # -----------------------------------

    return EpisodeDetailsResponse(
        id=episode.id,
        tmdb_id=episode.tmdb_id,
        season_id=episode.season_id,
        season_number=season.season_number,
        episode_number=episode.episode_number,
        name=episode.name,
        overview=episode.overview,
        air_date=episode.air_date,
        still_path=episode.still_path,
        vote_average=(
            float(episode.vote_average)
            if episode.vote_average is not None
            else None
        ),
        vote_count=episode.vote_count,
        runtime=episode.runtime,

        watched=watched,
        watch_count=watch_count,
        latest_rating=latest_rating,
        latest_review=latest_review,
        latest_watched_at=latest_watched_at,

        user_rating=user_rating,
        user_review=user_review,
        user_notes=user_notes,
        user_rewatch_count=user_rewatch_count
    )

@router.get(
    "/{tv_show_id}/details",
    response_model=TVShowDetailsResponse
)
def get_tv_show_details(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get TV show
    show = (
        db.query(TVShow)
        .filter(TVShow.id == tv_show_id)
        .first()
    )

    if not show:
        raise HTTPException(
            status_code=404,
            detail="TV show not found"
        )

    # -----------------------------------
    # Overall rating
    # -----------------------------------

    rating_data = (
        db.query(
            func.avg(ShowRating.rating),
            func.count(ShowRating.id)
        )
        .filter(ShowRating.tv_show_id == tv_show_id)
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
        db.query(func.count(ShowReview.id))
        .filter(ShowReview.tv_show_id == tv_show_id)
        .scalar()
    )

    # -----------------------------------
    # Current user's rating
    # -----------------------------------

    user_rating_obj = (
        db.query(ShowRating)
        .filter(
            ShowRating.tv_show_id == tv_show_id,
            ShowRating.user_id == current_user.id
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
        db.query(ShowReview)
        .filter(
            ShowReview.tv_show_id == tv_show_id,
            ShowReview.user_id == current_user.id
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
    # Episode progress
    # -----------------------------------

    total_episodes = (
        db.query(func.count(Episode.id))
        .join(Season, Episode.season_id == Season.id)
        .filter(
            Season.tv_show_id == tv_show_id,
            Season.season_number > 0
        )
        .scalar()
    ) or 0

    watched_episodes = (
        db.query(
            func.count(func.distinct(DiaryEntry.episode_id))
        )
        .join(
            Episode,
            DiaryEntry.episode_id == Episode.id
        )
        .join(
            Season,
            Episode.season_id == Season.id
        )
        .filter(
            Season.tv_show_id == tv_show_id,
            Season.season_number > 0,
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.episode_id.isnot(None)
        )
        .scalar()
    ) or 0

    watch_progress = (
        round(
            (watched_episodes / total_episodes) * 100,
            2
        )
        if total_episodes > 0
        else 0.0
    )

    # -----------------------------------
    # Watchlist status
    # -----------------------------------

    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.tv_show_id == tv_show_id
        )
        .first()
    )

    in_watchlist = watchlist_item is not None

    in_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.tv_show_id == tv_show_id
    ).first() is not None

    # -----------------------------------
    # Final response
    # -----------------------------------

    return TVShowDetailsResponse(
        id=show.id,
        tmdb_id=show.tmdb_id,
        name=show.name,
        original_name=show.original_name,
        overview=show.overview,
        first_air_date=show.first_air_date,
        last_air_date=show.last_air_date,
        original_language=show.original_language,
        poster_path=show.poster_path,
        backdrop_path=show.backdrop_path,
        vote_average=float(show.vote_average)
        if show.vote_average is not None
        else None,
        vote_count=show.vote_count,
        popularity=float(show.popularity)
        if show.popularity is not None
        else None,
        status=show.status,
        number_of_seasons=show.number_of_seasons,
        number_of_episodes=show.number_of_episodes,

        average_rating=average_rating,
        rating_count=rating_count,
        review_count=int(review_count or 0),

        user_rating=user_rating,
        user_review=user_review,
        user_contains_spoilers=user_contains_spoilers,

        watched_episodes=int(watched_episodes),
        total_episodes=int(total_episodes),
        watch_progress=watch_progress,
        in_watchlist=in_watchlist,
        in_favorites=in_favorites
    )

# =========================================================
# GET ALL IMPORTED SEASONS
# =========================================================

@router.get("/{tv_show_id}/seasons")
def get_tv_show_seasons(
    tv_show_id: int,
    db: Session = Depends(get_db)
):

    tv_show = (
        db.query(TVShow)
        .filter(
            TVShow.id == tv_show_id
        )
        .first()
    )

    if not tv_show:
        raise HTTPException(
            status_code=404,
            detail="TV show not found"
        )

    seasons = (
        db.query(Season)
        .filter(
            Season.tv_show_id == tv_show_id,
            Season.season_number > 0
        )
        .order_by(
            Season.season_number
        )
        .all()
    )

    result = []

    for season in seasons:

        episode_count = (
            db.query(Episode)
            .filter(
                Episode.season_id == season.id
            )
            .count()
        )

        result.append({
            "season_id": season.id,
            "season_number": season.season_number,
            "tmdb_id": season.tmdb_id,
            "name": season.name,
            "overview": season.overview,
            "air_date": season.air_date,
            "poster_path": season.poster_path,
            "episode_count": episode_count
        })

    return {
        "tv_show_id": tv_show.id,
        "tmdb_id": tv_show.tmdb_id,
        "name": tv_show.name,
        "number_of_seasons": len(result),
        "seasons": result
    }


# =========================================================
# GET SEASON EPISODES + USER WATCH STATUS
# =========================================================

@router.get(
    "/{tv_show_id}/seasons/{season_number}"
)
def get_season_episodes(
    tv_show_id: int,
    season_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if season_number <= 0:
        raise HTTPException(
            status_code=400,
            detail="Season number must be greater than 0"
        )

    # -----------------------------------------------------
    # Find TV show
    # -----------------------------------------------------

    tv_show = (
        db.query(TVShow)
        .filter(
            TVShow.id == tv_show_id
        )
        .first()
    )

    if not tv_show:
        raise HTTPException(
            status_code=404,
            detail="TV show not found"
        )

    # -----------------------------------------------------
    # Find season
    # -----------------------------------------------------

    season = (
        db.query(Season)
        .filter(
            Season.tv_show_id == tv_show_id,
            Season.season_number == season_number
        )
        .first()
    )

    if not season:
        raise HTTPException(
            status_code=404,
            detail="Season not found"
        )

    # -----------------------------------------------------
    # Get episodes
    # -----------------------------------------------------

    episodes = (
        db.query(Episode)
        .filter(
            Episode.season_id == season.id
        )
        .order_by(
            Episode.episode_number
        )
        .all()
    )

    episode_results = []

    watched_count = 0

    for episode in episodes:

        # -------------------------------------------------
        # Get user's complete watch history
        # -------------------------------------------------

        diary_entries = (
            db.query(DiaryEntry)
            .filter(
                DiaryEntry.user_id == current_user.id,
                DiaryEntry.episode_id == episode.id
            )
            .order_by(
                DiaryEntry.watched_at.desc()
            )
            .all()
        )

        is_watched = len(diary_entries) > 0

        if is_watched:
            watched_count += 1

        latest_entry = (
            diary_entries[0]
            if diary_entries
            else None
        )

        latest_rating = None

        if (
            latest_entry
            and latest_entry.rating is not None
        ):
            latest_rating = float(
                latest_entry.rating
            )

        latest_watched_at = (
            latest_entry.watched_at
            if latest_entry
            else None
        )

        episode_results.append({
            "episode_id": episode.id,
            "tmdb_id": episode.tmdb_id,
            "episode_number": episode.episode_number,
            "name": episode.name,
            "overview": episode.overview,
            "air_date": episode.air_date,
            "runtime": episode.runtime,
            "still_path": episode.still_path,
            "vote_average": (
                float(episode.vote_average)
                if episode.vote_average is not None
                else None
            ),
            "vote_count": episode.vote_count,

            # User watch information
            "watched": is_watched,
            "watch_count": len(diary_entries),
            "latest_rating": latest_rating,
            "latest_watched_at": latest_watched_at
        })

    total_episodes = len(episodes)

    remaining_episodes = (
        total_episodes - watched_count
    )

    progress_percentage = 0

    if total_episodes > 0:
        progress_percentage = round(
            (watched_count / total_episodes) * 100,
            2
        )

    return {
        "tv_show_id": tv_show.id,
        "tmdb_id": tv_show.tmdb_id,
        "tv_show_name": tv_show.name,

        "season_id": season.id,
        "season_number": season.season_number,
        "season_name": season.name,
        "season_overview": season.overview,
        "air_date": season.air_date,
        "poster_path": season.poster_path,

        "total_episodes": total_episodes,
        "watched_episodes": watched_count,
        "remaining_episodes": remaining_episodes,
        "progress_percentage": progress_percentage,

        "episodes": episode_results
    }