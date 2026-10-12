from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    SmallInteger,
    Numeric,
    TIMESTAMP,
    ForeignKey,
    Boolean,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    display_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

class Movie(Base):
    __tablename__ = "movies"

    id = Column(BigInteger, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)

    title = Column(String(255), nullable=False)
    original_title = Column(String(255))

    overview = Column(Text)

    release_date = Column(Date)
    runtime = Column(SmallInteger)

    original_language = Column(String(10))

    poster_path = Column(String(500))
    backdrop_path = Column(String(500))

    vote_average = Column(Numeric(4, 2))
    vote_count = Column(Integer)
    popularity = Column(Numeric(12, 4))

    status = Column(String(50))

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    genres = relationship(
        "Genre",
        secondary="movie_genres",
        back_populates="movies"
    )

    credits = relationship(
        "MovieCredit",
        back_populates="movie"
    )

    movie_reviews = relationship(
        "MovieReview",
        back_populates="movie",
        cascade="all, delete-orphan"
    )

    favorites = relationship(
        "Favorite",
        back_populates="movie",
        cascade="all, delete-orphan"
    )

class TVShow(Base):
    __tablename__ = "tv_shows"

    id = Column(BigInteger, primary_key=True, index=True)

    tmdb_id = Column(Integer, unique=True, nullable=False)

    name = Column(String(255), nullable=False)
    original_name = Column(String(255))
    overview = Column(Text)

    first_air_date = Column(Date)
    last_air_date = Column(Date)

    original_language = Column(String(10))

    poster_path = Column(String(500))
    backdrop_path = Column(String(500))

    vote_average = Column(Numeric(4, 2))
    vote_count = Column(Integer, default=0)
    popularity = Column(Numeric(12, 4))

    status = Column(String(50))

    number_of_seasons = Column(SmallInteger, default=0)
    number_of_episodes = Column(Integer, default=0)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    seasons = relationship(
        "Season",
        back_populates="tv_show"
    )

    show_ratings = relationship(
        "ShowRating",
        back_populates="tv_show",
        cascade="all, delete-orphan"
    )

    show_reviews = relationship(
        "ShowReview",
        back_populates="tv_show",
        cascade="all, delete-orphan"
    )

    favorites = relationship(
        "Favorite",
        back_populates="tv_show",
        cascade="all, delete-orphan"
    )

class Season(Base):
    __tablename__ = "seasons"

    id = Column(BigInteger, primary_key=True, index=True)

    tv_show_id = Column(
        BigInteger,
        ForeignKey("tv_shows.id"),
        nullable=False
    )

    tmdb_id = Column(Integer, unique=True, nullable=False)

    season_number = Column(SmallInteger, nullable=False)

    name = Column(String(255))
    overview = Column(Text)

    air_date = Column(Date)
    poster_path = Column(String(500))

    episode_count = Column(
        SmallInteger,
        default=0
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    tv_show = relationship(
        "TVShow",
        back_populates="seasons"
    )

    episodes = relationship(
        "Episode",
        back_populates="season"
    )

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(BigInteger, primary_key=True, index=True)

    season_id = Column(
        BigInteger,
        ForeignKey("seasons.id"),
        nullable=False
    )

    tmdb_id = Column(Integer, unique=True, nullable=False)

    episode_number = Column(
        SmallInteger,
        nullable=False
    )

    name = Column(String(255), nullable=False)
    overview = Column(Text)

    air_date = Column(Date)
    runtime = Column(SmallInteger)

    still_path = Column(String(500))

    vote_average = Column(Numeric(4, 2))
    vote_count = Column(Integer, default=0)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    season = relationship(
        "Season",
        back_populates="episodes"
    )

class Genre(Base):
    __tablename__ = "genres"

    id = Column(BigInteger, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    movies = relationship(
        "Movie",
        secondary="movie_genres",
        back_populates="genres"
    )


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        primary_key=True
    )

    genre_id = Column(
        BigInteger,
        ForeignKey("genres.id"),
        primary_key=True
    )


class Person(Base):
    __tablename__ = "people"

    id = Column(BigInteger, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)

    name = Column(String(255), nullable=False)

    profile_path = Column(String(500))
    known_for_department = Column(String(100))

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    movie_credits = relationship(
        "MovieCredit",
        back_populates="person"
    )


class MovieCredit(Base):
    __tablename__ = "movie_credits"

    id = Column(BigInteger, primary_key=True, index=True)

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=False
    )

    person_id = Column(
        BigInteger,
        ForeignKey("people.id"),
        nullable=False
    )

    credit_type = Column(
        String(10),
        nullable=False
    )

    character_name = Column(String(255))
    job = Column(String(255))
    department = Column(String(100))

    movie = relationship(
        "Movie",
        back_populates="credits"
    )

    person = relationship(
        "Person",
        back_populates="movie_credits"
    )

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=True
    )

    tv_show_id = Column(
        BigInteger,
        nullable=True
    )

    added_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

class MovieRating(Base):
    __tablename__ = "movie_ratings"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=False
    )

    rating = Column(
        Numeric(2, 1),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    movie = relationship("Movie")
    user = relationship("User")

class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=True
    )

    episode_id = Column(
        BigInteger,
        ForeignKey("episodes.id"),
        nullable=True
    )

    watched_at = Column(
        DateTime,
        nullable=False
    )

    notes = Column(
        Text,
        nullable=True
    )

    rewatch = Column(
        Boolean,
        nullable=False,
        default=False
    )

    rating = Column(
        Numeric(2, 1),
        nullable=True
    )

    review = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    movie = relationship(
        "Movie",
        backref="diary_entries"
    )

    episode = relationship(
        "Episode",
        backref="diary_entries"
    )

    user = relationship("User")

class ShowRating(Base):
    __tablename__ = "show_ratings"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    tv_show_id = Column(
        BigInteger,
        ForeignKey("tv_shows.id"),
        nullable=False
    )

    rating = Column(
        Numeric(2, 1),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    tv_show = relationship(
        "TVShow",
        back_populates="show_ratings"
    )

    user = relationship("User")


class ShowReview(Base):
    __tablename__ = "show_reviews"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    tv_show_id = Column(
        BigInteger,
        ForeignKey("tv_shows.id"),
        nullable=False
    )

    review_text = Column(
        Text,
        nullable=False
    )

    contains_spoilers = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    tv_show = relationship(
        "TVShow",
        back_populates="show_reviews"
    )

    user = relationship("User")

class MovieReview(Base):
    __tablename__ = "movie_reviews"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=False
    )

    review_text = Column(
        Text,
        nullable=False
    )

    contains_spoilers = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    movie = relationship(
        "Movie",
        back_populates="movie_reviews"
    )

    user = relationship("User")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=True
    )

    tv_show_id = Column(
        BigInteger,
        ForeignKey("tv_shows.id"),
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    movie = relationship(
        "Movie",
        back_populates="favorites"
    )

    tv_show = relationship(
        "TVShow",
        back_populates="favorites"
    )

    user = relationship("User")


class UserFollow(Base):
    __tablename__ = "user_follows"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    follower_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    following_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    follower = relationship(
        "User",
        foreign_keys=[follower_id]
    )

    following = relationship(
        "User",
        foreign_keys=[following_id]
    )


class List(Base):
    __tablename__ = "lists"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User")
    items = relationship(
        "ListItem",
        back_populates="list",
        cascade="all, delete-orphan",
    )


class ListItem(Base):
    __tablename__ = "list_items"

    id = Column(BigInteger, primary_key=True, index=True)
    list_id = Column(
        BigInteger,
        ForeignKey("lists.id"),
        nullable=False,
    )
    movie_id = Column(
        BigInteger,
        ForeignKey("movies.id"),
        nullable=True,
    )
    tv_show_id = Column(
        BigInteger,
        ForeignKey("tv_shows.id"),
        nullable=True,
    )
    position = Column(Integer, nullable=True)
    added_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    list = relationship("List", back_populates="items")
    movie = relationship("Movie")
    tv_show = relationship("TVShow")
