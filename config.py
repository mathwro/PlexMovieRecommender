import os
from dotenv import dotenv_values

# Merge .env file with real environment variables (env vars take precedence)
# utf-8-sig handles UTF-8 with or without BOM (avoids issues with Windows editors)
_env: dict = {**dotenv_values(encoding="utf-8-sig"), **os.environ}


def _get(key: str, default: str | None = None) -> str | None:
    return _env.get(key, default)


def _require(key: str) -> str:
    val = _env.get(key)
    if not val:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return val


DISCORD_TOKEN: str = _require("DISCORD_TOKEN")
DISCORD_GUILD_ID: int | None = int(gid) if (gid := _get("DISCORD_GUILD_ID")) else None
DISCORD_MEMBERS_INTENT: bool = _get("DISCORD_MEMBERS_INTENT", "").lower() in ("1", "true", "yes")

PLEX_URL: str = _require("PLEX_URL")
PLEX_PUBLIC_URL: str = _get("PLEX_PUBLIC_URL", PLEX_URL).rstrip("/")
PLEX_LIBRARY: str = _get("PLEX_LIBRARY", "Movies")
PLEX_SERIES_LIBRARY: str = _get("PLEX_SERIES_LIBRARY", "TV Shows")
