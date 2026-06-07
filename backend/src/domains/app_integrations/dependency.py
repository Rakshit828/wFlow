
from src.domains.app_integrations.service import (
    GoogleIntegrationService,
    GitHubIntegrationService,
)


def get_google_integration_service() -> GoogleIntegrationService:
    return GoogleIntegrationService()

def get_github_integration_service() -> GitHubIntegrationService:
    return GitHubIntegrationService()

