from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class GenreResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tmdb_id: int
    name: str


class PersonResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tmdb_id: int
    name: str
    profile_path: str | None = None
    known_for_department: str | None = None


class MovieCreditResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    credit_type: str
    character_name: str | None = None
    job: str | None = None
    department: str | None = None

    person: PersonResponse

class UserCreate(BaseModel):

    username: str
    email: str
    password: str

    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

class UserLogin(BaseModel):

    email: str
    password: str


class UserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    username: str
    email: str

    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

    created_at: datetime
    updated_at: datetime

class MovieResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tmdb_id: int

    title: str
    original_title: str | None = None

    overview: str | None = None

    release_date: date | None = None
    runtime: int | None = None

    original_language: str | None = None

    poster_path: str | None = None
    backdrop_path: str | None = None

    vote_average: float | None = None
    vote_count: int | None = None
    popularity: float | None = None

    status: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    genres: list[GenreResponse] = []
    credits: list[MovieCreditResponse] = []