from sqlalchemy.orm import Session, joinedload

from app.models import (
    Movie,
    Genre,
    MovieGenre,
    Person,
    MovieCredit
)


def import_movie_data(
    db: Session,
    movie_data: dict
):
    """
    Import a TMDB movie and its related
    genres, cast, and crew into CineLog.
    """

    tmdb_id = movie_data["id"]

    # --------------------------------
    # MOVIE
    # --------------------------------

    movie = (
        db.query(Movie)
        .filter(Movie.tmdb_id == tmdb_id)
        .first()
    )

    if not movie:

        movie = Movie(
            tmdb_id=tmdb_id,
            title=movie_data["title"],
            original_title=movie_data.get("original_title"),
            overview=movie_data.get("overview"),
            release_date=movie_data.get("release_date") or None,
            runtime=movie_data.get("runtime"),
            original_language=movie_data.get(
                "original_language"
            ),
            poster_path=movie_data.get("poster_path"),
            backdrop_path=movie_data.get(
                "backdrop_path"
            ),
            vote_average=movie_data.get(
                "vote_average"
            ),
            vote_count=movie_data.get(
                "vote_count"
            ),
            popularity=movie_data.get(
                "popularity"
            ),
            status=movie_data.get("status"),
        )

        db.add(movie)
        db.flush()


    # --------------------------------
    # GENRES
    # --------------------------------

    for genre_data in movie_data.get("genres", []):

        genre = (
            db.query(Genre)
            .filter(
                Genre.tmdb_id == genre_data["id"]
            )
            .first()
        )

        if not genre:

            genre = Genre(
                tmdb_id=genre_data["id"],
                name=genre_data["name"]
            )

            db.add(genre)
            db.flush()


        existing_relation = (
            db.query(MovieGenre)
            .filter(
                MovieGenre.movie_id == movie.id,
                MovieGenre.genre_id == genre.id
            )
            .first()
        )

        if not existing_relation:

            movie_genre = MovieGenre(
                movie_id=movie.id,
                genre_id=genre.id
            )

            db.add(movie_genre)


    # --------------------------------
    # CAST
    # --------------------------------

    credits = movie_data.get("credits", {})

    cast = credits.get("cast", [])

    for cast_member in cast:

        person = (
            db.query(Person)
            .filter(
                Person.tmdb_id == cast_member["id"]
            )
            .first()
        )

        if not person:

            person = Person(
                tmdb_id=cast_member["id"],
                name=cast_member["name"],
                profile_path=cast_member.get(
                    "profile_path"
                ),
                known_for_department=cast_member.get(
                    "known_for_department"
                )
            )

            db.add(person)
            db.flush()


        existing_credit = (
            db.query(MovieCredit)
            .filter(
                MovieCredit.movie_id == movie.id,
                MovieCredit.person_id == person.id,
                MovieCredit.credit_type == "cast"
            )
            .first()
        )

        if not existing_credit:

            credit = MovieCredit(
                movie_id=movie.id,
                person_id=person.id,
                credit_type="cast",
                character_name=cast_member.get(
                    "character"
                ),
                department=cast_member.get(
                    "known_for_department"
                )
            )

            db.add(credit)


    # --------------------------------
    # CREW
    # --------------------------------

    crew = credits.get("crew", [])

    for crew_member in crew:

        person = (
            db.query(Person)
            .filter(
                Person.tmdb_id == crew_member["id"]
            )
            .first()
        )

        if not person:

            person = Person(
                tmdb_id=crew_member["id"],
                name=crew_member["name"],
                profile_path=crew_member.get(
                    "profile_path"
                ),
                known_for_department=crew_member.get(
                    "known_for_department"
                )
            )

            db.add(person)
            db.flush()


        existing_credit = (
            db.query(MovieCredit)
            .filter(
                MovieCredit.movie_id == movie.id,
                MovieCredit.person_id == person.id,
                MovieCredit.credit_type == "crew"
            )
            .first()
        )

        if not existing_credit:

            credit = MovieCredit(
                movie_id=movie.id,
                person_id=person.id,
                credit_type="crew",
                job=crew_member.get("job"),
                department=crew_member.get(
                    "department"
                )
            )

            db.add(credit)


    return movie

def get_movie_by_id(
    db: Session,
    movie_id: int
):
    """
    Fetch a movie from the local database
    together with its genres and credits/person details.
    """

    movie = (
        db.query(Movie)
        .options(
            joinedload(Movie.genres),
            joinedload(Movie.credits)
            .joinedload(MovieCredit.person)
        )
        .filter(Movie.id == movie_id)
        .first()
    )

    return movie