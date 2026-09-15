from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MovieResponse
from app.services.movie_service import (
    import_movie_data,
    get_movie_by_id
)
from app.models import Movie
from app.tmdb import search_movies, get_movie_details


router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)


@router.get("/search")
async def movie_search(query: str):

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )

    try:
        results = await search_movies(query)

        return {
            "query": query,
            "results": results.get("results", [])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
@router.get("/tmdb/{tmdb_id}")
async def movie_details(tmdb_id: int):

    try:
        movie = await get_movie_details(tmdb_id)

        return movie

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch movie details from TMDB"
        )
@router.post("/import/{tmdb_id}")
async def import_movie(
    tmdb_id: int,
    db: Session = Depends(get_db)
):

    try:
        # Get complete movie data from TMDB
        movie_data = await get_movie_details(tmdb_id)

        # Import movie, genres, cast and crew
        movie = import_movie_data(
            db=db,
            movie_data=movie_data
        )

        # Save all changes
        db.commit()

        return {
            "message": "Movie imported successfully",
            "movie_id": movie.id,
            "tmdb_id": movie.tmdb_id,
            "title": movie.title
        }

    except Exception as error:
        db.rollback()

        print("IMPORT ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Failed to import movie"
        )

@router.get("/", response_model=list[MovieResponse])
def get_movies(
    db: Session = Depends(get_db)
):

    movies = db.query(Movie).all()

    return movies

@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db)
):
    movie = get_movie_by_id(
        db=db,
        movie_id=movie_id
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie not found"
        )

    return movie