from src.integrations.googlecloud.gsheets.types import (
    ReadSheetMetadataInput,
    GoogleSheetsApis,
)
from src.integrations.googlecloud import GoogleAPIClient


async def get_sheets_metadata(node_input: ReadSheetMetadataInput) -> dict:
    api_client: GoogleAPIClient = node_input.config._google_api_client
    _, resposne_json = await api_client.request(
        "GET",
        GoogleSheetsApis.GET_SHEETS_METADATA.format(
            spreadsheetId=node_input.spreadsheet_id
        ),
        requires_bearer_token=True,
    )
    return resposne_json
