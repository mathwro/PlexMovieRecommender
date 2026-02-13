from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

import config
from db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


class PlexBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await init_db()
        log.info("Database initialized.")

        await self.load_extension("cogs.auth")
        await self.load_extension("cogs.recommend")
        await self.load_extension("cogs.series")
        log.info("Cogs loaded.")

        if config.DISCORD_GUILD_ID:
            guild = discord.Object(id=config.DISCORD_GUILD_ID)
            # Copy global commands into guild namespace, then sync to guild
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Slash commands synced to guild %s.", config.DISCORD_GUILD_ID)
            # Clear global namespace so commands don't appear twice
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            log.info("Global commands cleared.")
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally (may take up to 1 hour to appear).")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your Plex library",
            )
        )


def main() -> None:
    bot = PlexBot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
