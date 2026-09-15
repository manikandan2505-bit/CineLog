import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"

TMDB_TOKEN = os.getenv("TMDB_API_READ_ACCESS_TOKEN")

if not TMDB_TOKEN:
    raise RuntimeError(
        "TMDB_API_READ_ACCESS_TOKEN is not set in the .env file"
    )


async def search_movies(query: str):
    url = f"{TMDB_BASE_URL}/search/movie"

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json",
    }

    params = {
        "query": query,
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )

    response.raise_for_status()

    return response.json()


async def get_movie_details(tmdb_id: int):
    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json",
    }

    params = {
        "language": "en-US",
        "append_to_response": "credits",
    }

    print("TMDB REQUEST:", url)
    print("TMDB TOKEN LOADED:", bool(TMDB_TOKEN))

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )

        print("TMDB STATUS:", response.status_code)

        response.raise_for_status()

        return response.json()

    except httpx.ConnectError as error:
        print("TMDB CONNECT ERROR:", repr(error))
        raise

    except httpx.HTTPStatusError as error:
        print("TMDB HTTP ERROR:", error.response.status_code)
        print("TMDB RESPONSE:", error.response.text[:500])
        raise