from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional, Tuple

from plexapi.server import PlexServer

import config

# Cache: discord_id → (PlexServer, timestamp)
_server_cache: Dict[str, Tuple[PlexServer, float]] = {}
_CACHE_TTL = 300  # 5 minutes


def _is_fresh(ts: float) -> bool:
    return (time.monotonic() - ts) < _CACHE_TTL


async def get_server(discord_id: str, plex_token: str) -> PlexServer:
    """Return a (possibly cached) PlexServer for this user's token."""
    cached = _server_cache.get(discord_id)
    if cached and _is_fresh(cached[1]):
        return cached[0]

    loop = asyncio.get_running_loop()
    server: PlexServer = await loop.run_in_executor(
        None,
        lambda: PlexServer(config.PLEX_URL, plex_token),
    )
    _server_cache[discord_id] = (server, time.monotonic())
    return server


def invalidate_cache(discord_id: str) -> None:
    _server_cache.pop(discord_id, None)
