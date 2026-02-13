import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_ID: int | None = int(gid) if (gid := os.getenv("DISCORD_GUILD_ID")) else None
DISCORD_MEMBERS_INTENT: bool = os.getenv("DISCORD_MEMBERS_INTENT", "").lower() in ("1", "true", "yes")
PLEX_URL: str = os.environ["PLEX_URL"]
PLEX_PUBLIC_URL: str = os.getenv("PLEX_PUBLIC_URL", PLEX_URL).rstrip("/")
PLEX_LIBRARY: str = os.getenv("PLEX_LIBRARY", "Movies")
PLEX_SERIES_LIBRARY: str = os.getenv("PLEX_SERIES_LIBRARY", "TV Shows")
