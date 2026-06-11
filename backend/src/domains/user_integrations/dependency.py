from src.domains.user_integrations.service import GoogleIntegrationService


def get_google_integration_service() -> GoogleIntegrationService:
    return GoogleIntegrationService()
