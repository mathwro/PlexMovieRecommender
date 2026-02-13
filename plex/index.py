from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from plexapi.server import PlexServer

import config


def _thumb_url(movie, token: str) -> Optional[str]:
    thumb = getattr(movie, "thumb", None)
    if not thumb:
        return None
    return f"{config.PLEX_PUBLIC_URL}{thumb}?X-Plex-Token={token}"


@dataclass
class MovieRecord:
    rating_key: str
    title: str
    year: Optional[int]
    decade: Optional[int]
    genres: FrozenSet[str]
    directors: FrozenSet[str]
    actors: FrozenSet[str]        # capped at 10
    rating: Optional[float]
    audience_rating: Optional[float]
    watched: bool
    summary: str = ""
    thumb_url: Optional[str] = None


@dataclass
class MovieIndex:
    records: Dict[str, MovieRecord]                  # rating_key → record
    watched_order: List[str]                         # newest-first rating_keys
    genre_index: Dict[str, List[str]]                # genre → [rating_keys]


def _decade(year: Optional[int]) -> Optional[int]:
    return (year // 10) * 10 if year else None


def _build_record(movie, watched_keys: set, token: str) -> MovieRecord:
    year = getattr(movie, "year", None)
    genres = frozenset(g.tag.lower() for g in (movie.genres or []))
    directors = frozenset(d.tag for d in (movie.directors or []))
    actors = frozenset(r.tag for r in (movie.roles or [])[:10])
    rating = getattr(movie, "rating", None)
    audience_rating = getattr(movie, "audienceRating", None)
    summary = getattr(movie, "summary", "") or ""

    return MovieRecord(
        rating_key=str(movie.ratingKey),
        title=movie.title,
        year=year,
        decade=_decade(year),
        genres=genres,
        directors=directors,
        actors=actors,
        rating=rating,
        audience_rating=audience_rating,
        watched=str(movie.ratingKey) in watched_keys,
        summary=summary,
        thumb_url=_thumb_url(movie, token),
    )


async def build_index(server: PlexServer, library_name: str = "Movies") -> MovieIndex:
    """Fetch all movies and watch history, return a MovieIndex."""
    loop = asyncio.get_running_loop()
    token: str = server._token

    section = await loop.run_in_executor(
        None, lambda: server.library.section(library_name)
    )

    movies = await loop.run_in_executor(None, section.all)

    # Fetch history scoped to this library section
    history = await loop.run_in_executor(
        None,
        lambda: server.history(librarySectionID=section.key),
    )

    # Build watched set and ordered list (history is newest-first)
    seen: set[str] = set()
    watched_order: List[str] = []
    for item in history:
        key = str(item.ratingKey)
        if key not in seen:
            seen.add(key)
            watched_order.append(key)

    records: Dict[str, MovieRecord] = {}
    genre_index: Dict[str, List[str]] = {}

    for movie in movies:
        record = _build_record(movie, seen, token)
        records[record.rating_key] = record
        for genre in record.genres:
            genre_index.setdefault(genre, []).append(record.rating_key)

    return MovieIndex(
        records=records,
        watched_order=watched_order,
        genre_index=genre_index,
    )
