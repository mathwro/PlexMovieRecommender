# PlexMovieRecommender

A Discord bot that recommends movies and TV series from your Plex library based on your watch history.

## Features

- `/recommend` — 5 movie recommendations based on your recently watched movies
- `/recommend-genre <genre>` — movie recommendations filtered by genre
- `/recommend-series` — 5 series recommendations based on your recently watched shows
- `/recommend-series-genre <genre>` — series recommendations filtered by genre
- `/plex-login` — link your Plex account via OAuth (no password required)
- `/plex-logout` — unlink your Plex account
- Recommendations include movie/show poster, rating, genres, cast, and an explanation of why it was recommended
- All responses are private (only visible to you)

## Requirements

- Python 3.11+
- A Plex Media Server
- A Discord bot token

## Setup

### 1. Create a Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a bot
3. Under **Bot**, enable **Server Members Intent**
4. Copy the bot token
5. Invite the bot to your server with the `applications.commands` and `bot` scopes

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id   # right-click server → Copy Server ID (requires Developer Mode)

PLEX_URL=http://localhost:32400            # URL the bot uses to reach Plex internally
PLEX_PUBLIC_URL=http://your-public-ip:32400  # publicly accessible URL for poster images

PLEX_LIBRARY=Movies                        # name of your Plex movie library
PLEX_SERIES_LIBRARY=TV Shows               # name of your Plex TV library
```

`PLEX_URL` and `PLEX_PUBLIC_URL` can be the same if the bot is not running on the Plex server itself.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python bot.py
```

## Installing as a Windows service (NSSM)

The included `install_service.bat` installs the bot as a Windows service using [NSSM](https://nssm.cc/) so it starts automatically and restarts on failure.

1. Download NSSM and ensure `nssm.exe` is on your PATH
2. Run `install_service.bat` as Administrator

The script will automatically detect a `venv` or `.venv` folder in the project directory and prefer that Python over the system install.

Logs are written to `bot.log` (stdout) and `bot_error.log` (stderr) in the project directory.

```
nssm start   PlexRecommenderBot
nssm stop    PlexRecommenderBot
nssm restart PlexRecommenderBot
nssm remove  PlexRecommenderBot confirm
```

## How recommendations work

When you run `/recommend`, the bot:

1. Fetches your watch history from Plex
2. Builds a profile from your 5 most recently watched titles (genres, directors/cast, era)
3. Scores every unwatched title in the library against that profile
4. Returns the top 5 matches with an explanation

Scoring weights:
- Genre overlap: 40%
- Director match: 25% (movies only)
- Cast overlap: 20%
- Era (decade) similarity: 15%

If you have no watch history, it falls back to top-rated unwatched titles in the library.

## Project structure

```
bot.py                  # entry point
config.py               # environment variable loading
cogs/
  auth.py               # /plex-login, /plex-logout
  recommend.py          # /recommend, /recommend-genre
  series.py             # /recommend-series, /recommend-series-genre
db/
  database.py           # SQLite setup
  users.py              # user token storage
plex/
  auth.py               # Plex OAuth PIN login flow
  client.py             # PlexServer connection + cache
  index.py              # movie library indexing
  series_index.py       # series library indexing
recommender/
  engine.py             # recommendation logic
  scorer.py             # scoring functions
utils/
  embeds.py             # Discord embed builders
```
