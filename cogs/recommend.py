from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import config
from db.users import get_user
from plex.client import get_server
from plex.index import MovieIndex, build_index
from recommender.engine import Recommender
from utils.embeds import build_movie_embed

# Per-user index cache: discord_id → (MovieIndex, timestamp)
_index_cache: Dict[str, Tuple[MovieIndex, float]] = {}
_INDEX_TTL = 300  # 5 minutes


def _get_cached_index(discord_id: str) -> Optional[MovieIndex]:
    entry = _index_cache.get(discord_id)
    if entry and (time.monotonic() - entry[1]) < _INDEX_TTL:
        return entry[0]
    return None


def _set_cached_index(discord_id: str, index: MovieIndex) -> None:
    _index_cache[discord_id] = (index, time.monotonic())


async def _get_index(discord_id: str, plex_token: str) -> MovieIndex:
    cached = _get_cached_index(discord_id)
    if cached:
        return cached
    server = await get_server(discord_id, plex_token)
    index = await build_index(server, config.PLEX_LIBRARY)
    _set_cached_index(discord_id, index)
    return index


async def _require_auth(interaction: discord.Interaction):
    """Return user record or send ephemeral error and return None."""
    user = await get_user(str(interaction.user.id))
    if not user:
        await interaction.followup.send(
            "You haven't linked your Plex account yet. Use `/plex-login` to get started.",
            ephemeral=True,
        )
        return None
    return user


class RecommendCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="recommend",
        description="Get 5 movie recommendations based on your recently watched movies",
    )
    async def recommend(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        user = await _require_auth(interaction)
        if not user:
            return

        try:
            index = await _get_index(str(interaction.user.id), user["plex_token"])
        except Exception as exc:
            await interaction.followup.send(
                f"Failed to connect to Plex: {exc}", ephemeral=True
            )
            return

        recommender = Recommender(index)
        recs = recommender.recommend_from_history(n=5, seed_count=5)

        if not recs:
            await interaction.followup.send(
                "No recommendations found. Your library may be empty.", ephemeral=True
            )
            return

        embeds = [build_movie_embed(rec, i + 1) for i, rec in enumerate(recs)]
        watched_count = sum(1 for r in index.records.values() if r.watched)
        header = (
            f"**Recommendations for {interaction.user.display_name}** "
            f"(based on {min(watched_count, 5)} recently watched)"
        )
        await interaction.followup.send(content=header, embeds=embeds)

    @app_commands.command(
        name="recommend-genre",
        description="Get 5 movie recommendations in a specific genre",
    )
    @app_commands.describe(genre="The genre to filter by (e.g. thriller, comedy, sci-fi)")
    async def recommend_genre(self, interaction: discord.Interaction, genre: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        user = await _require_auth(interaction)
        if not user:
            return

        try:
            index = await _get_index(str(interaction.user.id), user["plex_token"])
        except Exception as exc:
            await interaction.followup.send(
                f"Failed to connect to Plex: {exc}", ephemeral=True
            )
            return

        recommender = Recommender(index)
        recs = recommender.recommend_by_genre(genre, n=5)

        if not recs:
            available = ", ".join(sorted(index.genre_index.keys())[:20])
            await interaction.followup.send(
                f"No movies found for genre **{genre}**.\n"
                f"Available genres include: {available}",
                ephemeral=True,
            )
            return

        embeds = [build_movie_embed(rec, i + 1) for i, rec in enumerate(recs)]
        await interaction.followup.send(
            content=f"**{genre.title()} recommendations for {interaction.user.display_name}**",
            embeds=embeds,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecommendCog(bot))
