"""Contains the discord specific login for OAuth 2.0"""

import httpx
import discord
import urllib.parse
from loguru import logger
from typing import Literal


from src.integrations.oauth2 import OAuthInterface
from src.config import CONFIG


class DiscordOAuthInterface(OAuthInterface):
    PROVIDER = "DISCORD"

    def __init__(self):
        super().__init__()
        self.async_client = httpx.AsyncClient()

    async def create_authorization_url(self, tier: Literal["basic", "pro"]):
        """
        Constructs the OAuth2 URL dynamically based on user needs.
        """

        # Currently, they are fixed and hardcoded. Granular control can be added later.
        scopes = ["identify", "guilds", "bot", "applications.commands"]

        # Calculate Permissions using discord.py utility
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.send_messages = True
        perms.embed_links = True

        if tier == "pro":
            perms.manage_channels = True
            perms.manage_messages = True
            perms.attach_files = True

        permission_integer = perms.value
        logger.info(f"Redirect url is : {CONFIG.DISCORD_LOGIN_REDIRECT_URL}")
        params = {
            "client_id": CONFIG.DISCORD_CLIENT_ID,
            "redirect_uri": CONFIG.DISCORD_LOGIN_REDIRECT_URL,
            "response_type": "code",
            "scope": " ".join(scopes),
            "permissions": permission_integer,
        }

        return (
            f"https://discord.com/api/oauth2/authorize?{urllib.parse.urlencode(params)}"
        )



    async def exchange_for_code(
        self, code: str
    ) -> dict[str, str]:
        pass 

