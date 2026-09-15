from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    Date,
    SmallInteger,
    Numeric,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


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