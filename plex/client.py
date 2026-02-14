from __future__ import annotations

import asyncio
import time
from typing import Dict, Tuple
from xml.etree.ElementTree import fromstring

import requests
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

import config

# Cache: discord_id → (PlexServer, timestamp)
_server_cache: Dict[str, Tuple[PlexServer, float]] = {}
_CACHE_TTL = 300  # 5 minutes

# Resolved once on first use
_machine_id: str | None = None


def _is_fresh(ts: float) -> bool:
    return (time.monotonic() - ts) < _CACHE_TTL


def _get_machine_id() -> str:
    """Get the machine identifier from the /identity endpoint (no auth required)."""
    resp = requests.get(f"{config.PLEX_URL.rstrip('/')}/identity", timeout=10)
    resp.raise_for_status()
    return fromstring(resp.content).attrib["machineIdentifier"]


def _connect_via_account(plex_token: str) -> PlexServer:
    """Connect to the configured Plex server via MyPlexAccount.

    Matches the server by machine identifier so it works regardless of
    whether PLEX_URL is localhost, a LAN IP, or a public address.
    Gives shared/friend users a properly scoped access token.
    """
    global _machine_id
    if _machine_id is None:
        _machine_id = _get_machine_id()

    account = MyPlexAccount(token=plex_token)
    for resource in account.resources():
        if resource.product == "Plex Media Server" and resource.clientIdentifier == _machine_id:
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
