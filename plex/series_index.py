from __future__ import annotations

import asyncio
from typing import Dict, List, Set

from plexapi.server import PlexServer

from plex.index import MovieIndex, MovieRecord, _decade, _thumb_url


def _build_series_record(show, watched_keys: Set[str], token: str) -> MovieRecord:
    year = getattr(show, "year", None)
    genres = frozenset(g.tag.lower() for g in (show.genres or []))
    actors = frozenset(r.tag for r in (show.roles or [])[:10])
    rating = getattr(show, "rating", None)
    audience_rating = getattr(show, "audienceRating", None)
    summary = getattr(show, "summary", "") or ""

    return MovieRecord(
        rating_key=str(show.ratingKey),
        title=show.title,
        year=year,
        decade=_decade(year),
        genres=genres,
        directors=frozenset(),  # not meaningful at show level
        actors=actors,
        rating=rating,
        audience_rating=audience_rating,
        watched=str(show.ratingKey) in watched_keys,
        summary=summary,
        thumb_url=_thumb_url(show, token),
    )


async def build_series_index(server: PlexServer, library_name: str = "TV Shows") -> MovieIndex:
    """Fetch all shows and watch history, return a MovieIndex."""
    loop = asyncio.get_running_loop()
    token: str = server._token

    section = await loop.run_in_executor(
        None, lambda: server.library.section(library_name)
    )

    shows = await loop.run_in_executor(None, section.all)

    # History returns episodes; grandparentRatingKey is the show's ratingKey
    history = await loop.run_in_executor(
        None,
        lambda: server.history(librarySectionID=section.key),
    )

    seen: Set[str] = set()
    watched_order: List[str] = []
    for item in history:
        key = str(getattr(item, "grandparentRatingKey", None) or "")
        if key and key not in seen:
            seen.add(key)
            watched_order.append(key)

    records: Dict[str, MovieRecord] = {}
    genre_index: Dict[str, List[str]] = {}

    for show in shows:
        record = _build_series_record(show, seen, token)
        records[record.rating_key] = record
        for genre in record.genres:
            genre_index.setdefault(genre, []).append(record.rating_key)

    return MovieIndex(
        records=records,
        watched_order=watched_order,
        genre_index=genre_index,
    )
