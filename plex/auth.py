from __future__ import annotations

import asyncio
from typing import Optional, Tuple

from plexapi.myplex import MyPlexPinLogin


POLL_INTERVAL = 3       # seconds between checkLogin polls
LOGIN_TIMEOUT = 300     # 5 minutes


async def start_pin_login() -> Tuple[MyPlexPinLogin, str]:
    """Create a PIN login session and return (pinlogin, oauth_url)."""
    loop = asyncio.get_running_loop()
    pinlogin: MyPlexPinLogin = await loop.run_in_executor(
        None, lambda: MyPlexPinLogin(oauth=True)
    )
    oauth_url: str = pinlogin.oauthUrl(forwardUrl=None)
    return pinlogin, oauth_url


async def poll_for_token(
    pinlogin: MyPlexPinLogin,
    timeout: int = LOGIN_TIMEOUT,
) -> Optional[str]:
    """
    Poll checkLogin() every POLL_INTERVAL seconds until the user authenticates
    or timeout is reached.

    Returns the auth token string on success, or None on timeout.
    """
    loop = asyncio.get_running_loop()
    elapsed = 0

    while elapsed < timeout:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        success: bool = await loop.run_in_executor(
            None, pinlogin.checkLogin
        )
        if success:
            return pinlogin.token

    return None
