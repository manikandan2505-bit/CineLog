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


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AccountDeleteRequest(BaseModel):
    current_password: str


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


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


class PublicUserProfileResponse(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    total_movies_watched: int = 0
    total_episodes_watched: int = 0
    total_movie_ratings: int = 0
    total_show_ratings: int = 0
    total_reviews: int = 0
    total_favorites: int = 0
    total_followers: int = 0
    total_following: int = 0
    is_following: bool | None = None


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

class MovieRatingCreate(BaseModel):

    rating: float


class MovieRatingResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    movie_id: int
    rating: float
    created_at: datetime
    updated_at: datetime

class DiaryEntryCreate(BaseModel):
    watched_at: datetime
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    rewatch: bool = False


class DiaryEntryUpdate(BaseModel):
    watched_at: datetime | None = None
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    rewatch: bool | None = None


class DiaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    watched_at: datetime
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    rewatch: bool
    created_at: datetime
    updated_at: datetime

class EpisodeDiaryEntryCreate(BaseModel):
    watched_at: datetime
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    rewatch: bool = False


class EpisodeDiaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    episode_id: int
    watched_at: datetime
    rating: float | None = None
    review: str | None = None
    notes: str | None = None
    rewatch: bool
    created_at: datetime
    updated_at: datetime

# =========================================================
# TV SHOW RATINGS
# =========================================================

class ShowRatingCreate(BaseModel):
    rating: float


class ShowRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tv_show_id: int
    rating: float
    created_at: datetime
    updated_at: datetime

# =========================================================
# TV SHOW REVIEWS
# =========================================================

class ShowReviewCreate(BaseModel):
    review_text: str
    contains_spoilers: bool = False


class ShowReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tv_show_id: int
    review_text: str
    contains_spoilers: bool
    created_at: datetime
    updated_at: datetime

class TVShowDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    name: str
    original_name: str | None = None
    overview: str | None = None
    first_air_date: date | None = None
    last_air_date: date | None = None
    original_language: str | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    popularity: float | None = None
    status: str | None = None
    number_of_seasons: int | None = None
    number_of_episodes: int | None = None

    average_rating: float | None = None
    rating_count: int = 0
    review_count: int = 0

    user_rating: float | None = None
    user_review: str | None = None
    user_contains_spoilers: bool = False

    watched_episodes: int = 0
    total_episodes: int = 0
    watch_progress: float = 0.0
    in_watchlist: bool = False
    in_favorites: bool = False

class EpisodeDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    season_id: int
    season_number: int
    episode_number: int
    name: str
    overview: str | None = None
    air_date: date | None = None
    still_path: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    runtime: int | None = None

    watched: bool = False
    watch_count: int = 0
    latest_rating: float | None = None
    latest_review: str | None = None
    latest_watched_at: datetime | None = None

    user_rating: float | None = None
    user_review: str | None = None
    user_notes: str | None = None
    user_rewatch_count: int = 0

class MovieDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

    average_rating: float | None = None
    rating_count: int = 0
    review_count: int = 0

    user_rating: float | None = None
    user_review: str | None = None
    user_contains_spoilers: bool = False

    watched: bool = False
    watch_count: int = 0
    latest_rating: float | None = None
    latest_review: str | None = None
    latest_notes: str | None = None
    latest_watched_at: datetime | None = None

    in_watchlist: bool = False
    in_favorites: bool = False

class MovieReviewCreate(BaseModel):
    review_text: str
    contains_spoilers: bool = False


class MovieReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    review_text: str
    contains_spoilers: bool
    created_at: datetime
    updated_at: datetime

class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int | None = None
    tv_show_id: int | None = None
    created_at: datetime



class UserProfileStatsResponse(BaseModel):
    total_movies_watched: int = 0
    total_movie_rewatches: int = 0
    total_episodes_watched: int = 0
    total_shows_tracked: int = 0

    total_movie_ratings: int = 0
    total_show_ratings: int = 0
    average_movie_rating: float | None = None
    average_show_rating: float | None = None

    total_reviews: int = 0
    total_favorites: int = 0
    total_watchlist_items: int = 0
    total_diary_entries: int = 0
