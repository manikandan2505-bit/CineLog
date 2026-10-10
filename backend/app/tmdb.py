import asyncio
import json
import os
import subprocess
import tempfile
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY is not set in the .env file"
    )


def _tmdb_get(url: str, params: dict | None = None):
    """
    Make a TMDB request using Windows curl.exe.

    Windows curl/Schannel works reliably with the current
    network environment, while Python's TLS stack does not.
    """

    query_string = f"api_key={quote(TMDB_API_KEY, safe='')}"

    if params:
        for key, value in params.items():
            query_string += (
                f"&{quote(str(key), safe='')}"
                f"={quote(str(value), safe='')}"
            )

    full_url = f"{url}?{query_string}"

    print(
        "TMDB CURL URL:",
        full_url.replace(TMDB_API_KEY, "***API_KEY***")
    )

    last_error = None

    # Retry up to 6 times because TMDB connections
    # occasionally fail with curl error 35.
    for attempt in range(6):
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".json",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            result = subprocess.run(
                [
                    "curl.exe",
                    "-4",
                    "-sS",
                    "--fail",
                    full_url,
                    "-o",
                    temp_path,
                ],
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"TMDB curl request failed "
                    f"(exit code {result.returncode})"
                )

            with open(
                temp_path,
                "r",
                encoding="utf-8",
                errors="replace"
            ) as file:
                response_text = file.read()

            if not response_text.strip():
                raise RuntimeError(
                    "TMDB returned an empty response"
                )

            try:
                return json.loads(response_text)

            except json.JSONDecodeError as error:
                raise RuntimeError(
                    "TMDB returned invalid JSON: "
                    f"{response_text[:500]}"
                ) from error

        except Exception as error:
            last_error = error

            print(
                f"TMDB REQUEST FAILED "
                f"(Attempt {attempt + 1}/6): {error}"
            )

            # Wait 3 seconds before the next attempt.
            if attempt < 5:
                print("Retrying TMDB request in 3 seconds...")
                time.sleep(3)

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    raise RuntimeError(
        f"TMDB request failed after 6 attempts: {last_error}"
    )


# ---------------------------------------------------------
# MOVIES
# ---------------------------------------------------------

async def search_movies(query: str):
    url = f"{TMDB_BASE_URL}/search/movie"

    params = {
        "query": query,
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
    }

    return await asyncio.to_thread(
        _tmdb_get,
        url,
        params,
    )


async def get_movie_details(tmdb_id: int):
    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"

    params = {
        "language": "en-US",
        "append_to_response": "credits",
    }

    print("TMDB MOVIE REQUEST:", url)
    print("TMDB API KEY LOADED:", bool(TMDB_API_KEY))

    data = await asyncio.to_thread(
        _tmdb_get,
        url,
        params,
    )

    print("TMDB MOVIE STATUS: 200")

    return data


# ---------------------------------------------------------
# TV SHOWS
# ---------------------------------------------------------

async def search_tv_shows(query: str):
    url = f"{TMDB_BASE_URL}/search/tv"

    params = {
        "query": query,
        "language": "en-US",
        "page": 1,
    }

    return await asyncio.to_thread(
        _tmdb_get,
        url,
        params,
    )


async def get_tv_show_details(tmdb_id: int):
    url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"

    params = {
        "language": "en-US",
    }

    print("TMDB TV SHOW REQUEST:", url)

    data = await asyncio.to_thread(
        _tmdb_get,
        url,
        params,
    )

    print("TMDB TV SHOW STATUS: 200")

    return data


async def get_season_details(
    tmdb_id: int,
    season_number: int
):
    url = (
        f"{TMDB_BASE_URL}/tv/"
        f"{tmdb_id}/season/{season_number}"
    )

    params = {
        "language": "en-US",
    }

    print(
        "TMDB SEASON REQUEST:",
        url
    )

    data = await asyncio.to_thread(
        _tmdb_get,
        url,
        params,
    )

    print("TMDB SEASON STATUS: 200")

    return data