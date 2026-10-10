from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    WatchlistItem,
    Movie,
    TVShow,
    Season,
    Episode,
    DiaryEntry,
    User
)
from app.security import get_current_user


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)


# =========================================================
# MOVIE WATCHLIST
# =========================================================

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
            "poster_path": (
                movie.poster_path
                if movie
                else None
            ),
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


# =========================================================
# TV SHOW WATCHLIST
# =========================================================

@router.post("/tv-shows/{tv_show_id}", status_code=201)
def add_tv_show_to_watchlist(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    existing_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.tv_show_id == tv_show_id
        )
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=409,
            detail="TV show already exists in your watchlist"
        )

    watchlist_item = WatchlistItem(
        user_id=current_user.id,
        tv_show_id=tv_show_id
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    return {
        "message": "TV show added to watchlist",
        "watchlist_id": watchlist_item.id,
        "tv_show_id": tv_show.id,
        "name": tv_show.name
    }


# =========================================================
# GET TV SHOW WATCHLIST
# =========================================================

@router.get("/tv-shows")
def get_tv_show_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist_items = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.tv_show_id.isnot(None)
        )
        .all()
    )

    result = []

    for item in watchlist_items:

        tv_show = (
            db.query(TVShow)
            .filter(
                TVShow.id == item.tv_show_id
            )
            .first()
        )

        if not tv_show:
            continue

        # Total number of episodes in this TV show
        total_episodes = (
            db.query(Episode)
            .join(
                Season,
                Episode.season_id == Season.id
            )
            .filter(
                Season.tv_show_id == tv_show.id,
                Season.season_number > 0
            )
            .count()
        )

        # Count UNIQUE episodes watched.
        # Multiple diary entries for the same episode
        # (rewatches) must count as ONE watched episode.
        watched_episodes = (
            db.query(Episode.id)
            .join(
                DiaryEntry,
                DiaryEntry.episode_id == Episode.id
            )
            .join(
                Season,
                Episode.season_id == Season.id
            )
            .filter(
                DiaryEntry.user_id == current_user.id,
                Season.tv_show_id == tv_show.id,
                Season.season_number > 0
            )
            .distinct()
            .count()
        )

        remaining_episodes = (
            total_episodes - watched_episodes
        )

        progress = 0

        if total_episodes > 0:
            progress = round(
                (watched_episodes / total_episodes) * 100,
                2
            )

        result.append({
            "watchlist_id": item.id,
            "tv_show_id": tv_show.id,
            "tmdb_id": tv_show.tmdb_id,
            "name": tv_show.name,
            "poster_path": tv_show.poster_path,
            "number_of_seasons": tv_show.number_of_seasons,
            "number_of_episodes": tv_show.number_of_episodes,
            "watched_episodes": watched_episodes,
            "total_episodes": total_episodes,
            "remaining_episodes": remaining_episodes,
            "progress_percentage": progress,
            "added_at": item.added_at
        })

    return result


# =========================================================
# GET SINGLE TV SHOW WATCHLIST STATUS
# =========================================================

@router.get("/tv-shows/{tv_show_id}")
def get_tv_show_watchlist_status(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.tv_show_id == tv_show_id
        )
        .first()
    )

    # Total episodes excluding Season 0 / Specials
    total_episodes = (
        db.query(Episode)
        .join(
            Season,
            Episode.season_id == Season.id
        )
        .filter(
            Season.tv_show_id == tv_show_id,
            Season.season_number > 0
        )
        .count()
    )

    # Count UNIQUE episodes watched.
    watched_episodes = (
        db.query(Episode.id)
        .join(
            DiaryEntry,
            DiaryEntry.episode_id == Episode.id
        )
        .join(
            Season,
            Episode.season_id == Season.id
        )
        .filter(
            DiaryEntry.user_id == current_user.id,
            Season.tv_show_id == tv_show_id,
            Season.season_number > 0
        )
        .distinct()
        .count()
    )

    remaining_episodes = (
        total_episodes - watched_episodes
    )

    progress = 0

    if total_episodes > 0:
        progress = round(
            (watched_episodes / total_episodes) * 100,
            2
        )

    return {
        "tv_show_id": tv_show.id,
        "tmdb_id": tv_show.tmdb_id,
        "name": tv_show.name,
        "in_watchlist": watchlist_item is not None,
        "watchlist_id": (
            watchlist_item.id
            if watchlist_item
            else None
        ),
        "watched_episodes": watched_episodes,
        "total_episodes": total_episodes,
        "remaining_episodes": remaining_episodes,
        "progress_percentage": progress
    }


# =========================================================
# TV SHOW SEASON-BY-SEASON PROGRESS
# =========================================================

@router.get("/tv-shows/{tv_show_id}/progress")
def get_tv_show_progress(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    total_episodes = 0
    watched_episodes = 0
    season_results = []

    for season in seasons:

        # Total episodes in this season
        total = (
            db.query(Episode)
            .filter(
                Episode.season_id == season.id
            )
            .count()
        )

        # Count UNIQUE episodes watched.
        #
        # If the user watches the same episode twice,
        # there will be two DiaryEntry rows but only one
        # unique Episode.id.
        watched = (
            db.query(Episode.id)
            .join(
                DiaryEntry,
                DiaryEntry.episode_id == Episode.id
            )
            .filter(
                DiaryEntry.user_id == current_user.id,
                Episode.season_id == season.id
            )
            .distinct()
            .count()
        )

        remaining = total - watched

        progress = 0

        if total > 0:
            progress = round(
                (watched / total) * 100,
                2
            )

        total_episodes += total
        watched_episodes += watched

        season_results.append({
            "season_number": season.season_number,
            "name": season.name,
            "total_episodes": total,
            "watched_episodes": watched,
            "remaining_episodes": remaining,
            "progress_percentage": progress
        })

    remaining_episodes = (
        total_episodes - watched_episodes
    )

    overall_progress = 0

    if total_episodes > 0:
        overall_progress = round(
            (watched_episodes / total_episodes) * 100,
            2
        )

    return {
        "tv_show_id": tv_show.id,
        "tmdb_id": tv_show.tmdb_id,
        "name": tv_show.name,

        "total_episodes": total_episodes,
        "watched_episodes": watched_episodes,
        "remaining_episodes": remaining_episodes,
        "progress_percentage": overall_progress,

        "seasons": season_results
    }


# =========================================================
# REMOVE TV SHOW FROM WATCHLIST
# =========================================================

@router.delete("/tv-shows/{tv_show_id}")
def remove_tv_show_from_watchlist(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.tv_show_id == tv_show_id
        )
        .first()
    )

    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail="TV show is not in your watchlist"
        )

    db.delete(watchlist_item)
    db.commit()

    return {
        "message": "TV show removed from watchlist",
        "tv_show_id": tv_show_id
    }