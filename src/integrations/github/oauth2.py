"""Contains the google specific login for OAuth 2.0."""

from src.integrations.oauth2 import OAuthInterface


class GithubOAuthInterface(OAuthInterface):
    def __init__(self):
        super().__init__()
    
    def create_authorization_url(self):
        pass

    async def exchange_for_code(self):
        pass

