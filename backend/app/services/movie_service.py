from sqlalchemy.orm import Session, joinedload

from app.models import (
    Movie,
    Genre,
    MovieGenre,
    Person,
    MovieCredit
)

from datetime import date

from app.models import TVShow, Season, Episode
from app.tmdb import (
    get_tv_show_details,
    get_season_details
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

async def import_tv_show(db, tmdb_id: int):
    # 1. Fetch TV show details
    print("STEP 1: Fetching TV show details")

    try:
        show_data = await get_tv_show_details(tmdb_id)
        print("STEP 1 SUCCESS: TV show details fetched")

    except Exception as error:
        import traceback

        print("STEP 1 FAILED: TV show details request")
        print("ERROR:", repr(error))
        traceback.print_exc()

        raise

    # 2. Check if show already exists
    show = db.query(TVShow).filter(
        TVShow.tmdb_id == tmdb_id
    ).first()

    if not show:
        show = TVShow(
            tmdb_id=show_data["id"],
            name=show_data["name"],
            original_name=show_data.get("original_name"),
            overview=show_data.get("overview"),
            first_air_date=(
                date.fromisoformat(show_data["first_air_date"])
                if show_data.get("first_air_date")
                else None
            ),
            last_air_date=(
                date.fromisoformat(show_data["last_air_date"])
                if show_data.get("last_air_date")
                else None
            ),
            original_language=show_data.get("original_language"),
            poster_path=show_data.get("poster_path"),
            backdrop_path=show_data.get("backdrop_path"),
            vote_average=show_data.get("vote_average"),
            vote_count=show_data.get("vote_count", 0),
            popularity=show_data.get("popularity"),
            status=show_data.get("status"),
            number_of_seasons=show_data.get("number_of_seasons", 0),
            number_of_episodes=show_data.get("number_of_episodes", 0)
        )

        db.add(show)
        db.flush()

    # 3. Import seasons and episodes
    for season_data in show_data.get("seasons", []):

        # Skip Specials (Season 0)
        if season_data["season_number"] == 0:
            continue

        season_number = season_data["season_number"]

        season = db.query(Season).filter(
            Season.tmdb_id == season_data["id"]
        ).first()

        if not season:
            season = Season(
                tv_show_id=show.id,
                tmdb_id=season_data["id"],
                season_number=season_number,
                name=season_data.get("name"),
                overview=season_data.get("overview"),
                air_date=(
                    date.fromisoformat(season_data["air_date"])
                    if season_data.get("air_date")
                    else None
                ),
                poster_path=season_data.get("poster_path"),
                episode_count=season_data.get("episode_count", 0)
            )

            db.add(season)
            db.flush()

        # 4. Fetch complete season information
        print(f"FETCHING SEASON {season_number} FOR SHOW {tmdb_id}")

        try:
            season_details = await get_season_details(
                tmdb_id,
                season_number
            )

            print(f"SEASON {season_number} FETCHED SUCCESSFULLY")

        except Exception as error:
            import traceback

            print(f"FAILED TO FETCH SEASON {season_number}")
            print("ERROR:", repr(error))
            traceback.print_exc()

            raise

        # 5. Import episodes
        for episode_data in season_details.get("episodes", []):

            existing_episode = db.query(Episode).filter(
                Episode.tmdb_id == episode_data["id"]
            ).first()

            if existing_episode:
                continue

            episode = Episode(
                season_id=season.id,
                tmdb_id=episode_data["id"],
                episode_number=episode_data["episode_number"],
                name=episode_data["name"],
                overview=episode_data.get("overview"),
                air_date=(
                    date.fromisoformat(episode_data["air_date"])
                    if episode_data.get("air_date")
                    else None
                ),
                runtime=episode_data.get("runtime"),
                still_path=episode_data.get("still_path"),
                vote_average=episode_data.get("vote_average"),
                vote_count=episode_data.get("vote_count", 0)
            )

            db.add(episode)

    print("STEP 6: Committing data to database")

    try:
        db.commit()
        print("STEP 6 SUCCESS: Database commit completed")

    except Exception as error:
        import traceback

        print("STEP 6 FAILED: Database commit")
        print("ERROR:", repr(error))
        traceback.print_exc()

        raise

    db.refresh(show)

    return show