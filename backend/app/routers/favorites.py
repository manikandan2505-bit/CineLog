from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movie,TVShow, Favorite, User
from app.schemas import FavoriteResponse
from app.security import get_current_user


router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)


@router.post(
    "/movies/{movie_id}",
    response_model=FavoriteResponse,
    status_code=201
)
def add_movie_favorite(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check movie exists
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

    # Check if already favorited
    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.movie_id == movie_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Movie already in favorites"
        )

    favorite = Favorite(
        user_id=current_user.id,
        movie_id=movie_id
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.get(
    "/movies",
    response_model=list[FavoriteResponse]
)
def get_movie_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorites = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.movie_id.isnot(None)
        )
        .order_by(Favorite.created_at.desc())
        .all()
    )

    return favorites


@router.delete(
    "/movies/{movie_id}"
)
def remove_movie_favorite(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.movie_id == movie_id
        )
        .first()
    )

    if not favorite:
        raise HTTPException(
            status_code=404,
            detail="Movie is not in favorites"
        )

    db.delete(favorite)
    db.commit()

    return {
        "message": "Movie removed from favorites",
        "movie_id": movie_id
    }

@router.post("/tv-shows/{tv_show_id}", response_model=FavoriteResponse, status_code=201)
def add_tv_show_favorite(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tv_show = db.query(TVShow).filter(TVShow.id == tv_show_id).first()
    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.tv_show_id == tv_show_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="TV show already in favorites")

    favorite = Favorite(
        user_id=current_user.id,
        tv_show_id=tv_show_id
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.get("/tv-shows", response_model=list[FavoriteResponse])
def get_tv_show_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.tv_show_id.isnot(None)
    ).order_by(Favorite.created_at.desc()).all()

    return favorites


@router.delete("/tv-shows/{tv_show_id}")
def remove_tv_show_favorite(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.tv_show_id == tv_show_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=404,
            detail="TV show is not in favorites"
        )

    db.delete(favorite)
    db.commit()

    return {
        "message": "TV show removed from favorites",
        "tv_show_id": tv_show_id
    }