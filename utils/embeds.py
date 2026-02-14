from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote

import discord

from plex.client import get_machine_id
from recommender.engine import Recommendation


def _plex_url(rating_key: str) -> Optional[str]:
    """Build an app.plex.tv deep link for the given item."""
    mid = get_machine_id()
    if not mid:
        return None
    key = quote(f"/library/metadata/{rating_key}", safe="")
    return f"https://app.plex.tv/desktop#!/server/{mid}/details?key={key}"


def build_series_embed(rec: Recommendation, rank: int) -> discord.Embed:
    show = rec.movie  # MovieRecord reused for series

    title = f"{rank}. {show.title}"
    if show.year:
        title += f" ({show.year})"

    rating_str = ""
    if show.audience_rating:
        rating_str = f"⭐ {show.audience_rating:.1f}/10"
    elif show.rating:
        rating_str = f"⭐ {show.rating:.1f}/10"

    genres_str = ", ".join(sorted(show.genres)).title() if show.genres else "Unknown"
    top_cast = list(show.actors)[:3]
    cast_str = ", ".join(top_cast) if top_cast else "Unknown"

    embed = discord.Embed(
        title=title,
        description=show.summary[:300] + ("…" if len(show.summary) > 300 else ""),
        url=_plex_url(show.rating_key),
        color=discord.Color.og_blurple(),
    )

    embed.add_field(name="Rating", value=rating_str or "N/A", inline=True)
    embed.add_field(name="Genres", value=genres_str, inline=True)
    embed.add_field(name="Top Cast", value=cast_str, inline=False)

    if rec.explanation:
        why = "\n".join(f"• {e}" for e in rec.explanation)
        embed.add_field(name="Why recommended", value=why, inline=False)

    if show.thumb_url:
        embed.set_thumbnail(url=show.thumb_url)

    embed.set_footer(text=f"Score: {rec.score:.2f}")
    return embed


def build_movie_embed(rec: Recommendation, rank: int) -> discord.Embed:
    movie = rec.movie

    title = f"{rank}. {movie.title}"
    if movie.year:
        title += f" ({movie.year})"

    rating_str = ""
    if movie.audience_rating:
        rating_str = f"⭐ {movie.audience_rating:.1f}/10"
    elif movie.rating:
        rating_str = f"⭐ {movie.rating:.1f}/10"

    genres_str = ", ".join(sorted(movie.genres)).title() if movie.genres else "Unknown"
    directors_str = ", ".join(sorted(movie.directors)) if movie.directors else "Unknown"
    top_cast = list(movie.actors)[:3]
    cast_str = ", ".join(top_cast) if top_cast else "Unknown"

    embed = discord.Embed(
        title=title,
        description=movie.summary[:300] + ("…" if len(movie.summary) > 300 else ""),
        url=_plex_url(movie.rating_key),
        color=discord.Color.blurple(),
    )

    embed.add_field(name="Rating", value=rating_str or "N/A", inline=True)
    embed.add_field(name="Genres", value=genres_str, inline=True)
    embed.add_field(name="Director", value=directors_str, inline=False)
    embed.add_field(name="Top Cast", value=cast_str, inline=False)

    if rec.explanation:
        why = "\n".join(f"• {e}" for e in rec.explanation)
        embed.add_field(name="Why recommended", value=why, inline=False)

    if movie.thumb_url:
        embed.set_thumbnail(url=movie.thumb_url)

    embed.set_footer(text=f"Score: {rec.score:.2f}")
    return embed
