from __future__ import annotations

import asyncio
import time
from typing import Dict, Tuple

from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

import config

# Cache: discord_id → (PlexServer, timestamp)
_server_cache: Dict[str, Tuple[PlexServer, float]] = {}
_CACHE_TTL = 300  # 5 minutes


def _is_fresh(ts: float) -> bool:
    return (time.monotonic() - ts) < _CACHE_TTL


def _connect_via_account(plex_token: str) -> PlexServer:
    """Connect to the configured Plex server via MyPlexAccount.

    Uses the account's resource list to get a properly scoped access token,
    which is required for shared/friend users.
    """
    account = MyPlexAccount(token=plex_token)
    for resource in account.resources():
        if resource.product != "Plex Media Server":
            continue
        for connection in resource.connections:
            if connection.uri.rstrip("/") == config.PLEX_URL.rstrip("/"):
                return resource.connect()
    raise RuntimeError(
        "Your Plex account does not have access to the configured server. "
        "Make sure you've been invited to the server."
    )


async def get_server(discord_id: str, plex_token: str) -> PlexServer:
    """Return a (possibly cached) PlexServer for this user's token."""
    cached = _server_cache.get(discord_id)
    if cached and _is_fresh(cached[1]):
        return cached[0]

    loop = asyncio.get_running_loop()
    server: PlexServer = await loop.run_in_executor(
        None,
        lambda: _connect_via_account(plex_token),
    )
    _server_cache[discord_id] = (server, time.monotonic())
    return server


def invalidate_cache(discord_id: str) -> None:
    _server_cache.pop(discord_id, None)
