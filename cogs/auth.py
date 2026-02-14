from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from plexapi.myplex import MyPlexAccount

from db.users import delete_user, get_user, save_user
from plex.auth import poll_for_token, start_pin_login
from plex.client import invalidate_cache


class AuthCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Track in-progress logins to prevent duplicates
        self._pending: set[int] = set()

    @app_commands.command(name="plex-login", description="Link your Plex account to get recommendations")
    async def plex_login(self, interaction: discord.Interaction) -> None:
        discord_id = str(interaction.user.id)

        if discord_id in {str(uid) for uid in self._pending}:
            await interaction.response.send_message(
                "You already have a login in progress. Check your DMs or wait for it to expire.",
                ephemeral=True,
            )
            return

        existing = await get_user(discord_id)
        if existing:
            await interaction.response.send_message(
                f"Your Plex account is already linked as **{existing['plex_username']}**. "
                "Use `/plex-logout` first if you want to relink.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            pinlogin, oauth_url = await start_pin_login()
        except Exception as exc:
            await interaction.followup.send(
                f"Failed to start Plex login: {exc}", ephemeral=True
            )
            return

        self._pending.add(interaction.user.id)

        await interaction.followup.send(
            f"**[Click here to link your Plex account]({oauth_url})**\n\n"
            "After authorizing on plex.tv, come back here — "
            "I'll confirm once your account is linked (timeout: 5 minutes).",
            ephemeral=True,
        )

        asyncio.create_task(
            self._await_login(interaction, pinlogin, discord_id),
            name=f"plex_login_{discord_id}",
        )

    async def _await_login(self, interaction: discord.Interaction, pinlogin, discord_id: str) -> None:
        try:
            token: Optional[str] = await poll_for_token(pinlogin)

            if token is None:
                await interaction.followup.send(
                    "Plex login timed out. Please run `/plex-login` again.",
                    ephemeral=True,
                )
                return

            # Resolve username from the token
            loop = asyncio.get_running_loop()
            try:
                account = await loop.run_in_executor(
                    None, lambda: MyPlexAccount(token=token)
                )
                username = account.username
            except Exception:
                username = None

            await save_user(discord_id, token, username)

            display = f"**{username}**" if username else "your account"
            await interaction.followup.send(
                f"Successfully linked {display} to your Discord profile! "
                "You can now use `/recommend`.",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"An error occurred during login: {exc}", ephemeral=True
            )
        finally:
            self._pending.discard(interaction.user.id)

    @app_commands.command(name="plex-logout", description="Unlink your Plex account")
    async def plex_logout(self, interaction: discord.Interaction) -> None:
        discord_id = str(interaction.user.id)
        deleted = await delete_user(discord_id)
        invalidate_cache(discord_id)

        if deleted:
            await interaction.response.send_message(
                "Your Plex account has been unlinked.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "No linked Plex account found.", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AuthCog(bot))
