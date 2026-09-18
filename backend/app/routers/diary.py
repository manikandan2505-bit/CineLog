from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import DiaryEntry, Movie, User
from app.schemas import (
    DiaryEntryCreate,
    DiaryEntryUpdate,
    DiaryEntryResponse
)
from app.security import get_current_user


router = APIRouter(
    prefix="/diary",
    tags=["Diary"]
)


@router.post(
    "/movies/{movie_id}",
    response_model=DiaryEntryResponse,
    status_code=201
)
def create_movie_diary_entry(
    movie_id: int,
    diary_data: DiaryEntryCreate,
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

    if diary_data.rating is not None:

        if (
            diary_data.rating < 0.5
            or diary_data.rating > 5.0
        ):
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 0.5 and 5.0"
            )

        if (diary_data.rating * 2) % 1 != 0:
            raise HTTPException(
                status_code=400,
                detail="Rating must use 0.5 star increments"
            )

    diary_entry = DiaryEntry(
        user_id=current_user.id,
        movie_id=movie_id,
        watched_at=diary_data.watched_at,
        rating=diary_data.rating,
        review=diary_data.review
    )

    db.add(diary_entry)
    db.commit()
    db.refresh(diary_entry)

    return diary_entry

@router.get("/")
def get_my_diary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    diary_entries = (
        db.query(DiaryEntry)
        .options(joinedload(DiaryEntry.movie))
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.movie_id.isnot(None)
        )
        .order_by(DiaryEntry.watched_at.desc())
        .all()
    )

    result = []

    for entry in diary_entries:
        movie = entry.movie

        result.append({
            "id": entry.id,
            "movie_id": entry.movie_id,
            "title": movie.title if movie else None,
            "poster_path": movie.poster_path if movie else None,
            "watched_at": entry.watched_at,
            "rating": (
                float(entry.rating)
                if entry.rating is not None
                else None
            ),
            "review": entry.review,
            "notes": entry.notes,
            "rewatch": entry.rewatch,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at
        })

    return result

@router.get("/{diary_id}")
def get_diary_entry(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    diary_entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == diary_id,
            DiaryEntry.user_id == current_user.id
        )
        .first()
    )

    if not diary_entry:
        raise HTTPException(
            status_code=404,
            detail="Diary entry not found"
        )

    movie = None

    if diary_entry.movie_id:
        movie = (
            db.query(Movie)
            .filter(Movie.id == diary_entry.movie_id)
            .first()
        )

    return {
        "id": diary_entry.id,
        "movie_id": diary_entry.movie_id,
        "title": movie.title if movie else None,
        "poster_path": movie.poster_path if movie else None,
        "watched_at": diary_entry.watched_at,
        "rating": (
            float(diary_entry.rating)
            if diary_entry.rating is not None
            else None
        ),
        "review": diary_entry.review,
        "notes": diary_entry.notes,
        "rewatch": diary_entry.rewatch,
        "created_at": diary_entry.created_at,
        "updated_at": diary_entry.updated_at
    }

@router.put(
    "/{diary_id}",
    response_model=DiaryEntryResponse
)
def update_diary_entry(
    diary_id: int,
    diary_data: DiaryEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    diary_entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == diary_id,
            DiaryEntry.user_id == current_user.id
        )
        .first()
    )

    if not diary_entry:
        raise HTTPException(
            status_code=404,
            detail="Diary entry not found"
        )

    if diary_data.rating is not None:
        if (
            diary_data.rating < 0.5
            or diary_data.rating > 5.0
        ):
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 0.5 and 5.0"
            )

        if (diary_data.rating * 2) % 1 != 0:
            raise HTTPException(
                status_code=400,
                detail="Rating must use 0.5 star increments"
            )

    if diary_data.watched_at is not None:
        diary_entry.watched_at = diary_data.watched_at

    if diary_data.rating is not None:
        diary_entry.rating = diary_data.rating

    if diary_data.review is not None:
        diary_entry.review = diary_data.review

    if diary_data.notes is not None:
        diary_entry.notes = diary_data.notes

    if diary_data.rewatch is not None:
        diary_entry.rewatch = diary_data.rewatch

    db.commit()
    db.refresh(diary_entry)

    return diary_entry

@router.delete("/{diary_id}")
def delete_diary_entry(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    diary_entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == diary_id,
            DiaryEntry.user_id == current_user.id
        )
        .first()
    )

    if not diary_entry:
        raise HTTPException(
            status_code=404,
            detail="Diary entry not found"
        )

    db.delete(diary_entry)
    db.commit()

    return {
        "message": "Diary entry deleted successfully",
        "diary_id": diary_id
    }