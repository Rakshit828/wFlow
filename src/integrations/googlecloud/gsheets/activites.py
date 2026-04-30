from src.integrations.googlecloud.gsheets.types import (
    ReadSheetMetadataInput,
    GoogleSheetsApis,
    CreateGoogleSheetInput,
    CreateGoogleSheetResponse,
    ReadCellValuesInput,
    ReadCellValuesResponse,
    AppendCellValuesInput,
    AppendCellValuesResponse,
    UpdateCellValuesInput,
    UpdateCellValuesResponse,
)
from src.integrations.googlecloud import GoogleAPIClient
from loguru import logger


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


async def create_google_sheet(
    node_input: CreateGoogleSheetInput,
) -> CreateGoogleSheetResponse:
    api_client: GoogleAPIClient = node_input.config._google_api_client
    _, resposne_json = await api_client.request(
        "POST",
        endpoint=GoogleSheetsApis.CREATE_NEW_SPREADSHEET,
        requires_bearer_token=True,
        json={"properties": node_input.model_dump(by_alias=True)},
    )
    return CreateGoogleSheetResponse(**resposne_json)


async def read_cell_values(node_input: ReadCellValuesInput) -> ReadCellValuesResponse:
    api_client: GoogleAPIClient = node_input.config._google_api_client
    _, resposne_json = await api_client.request(
        "GET",
        GoogleSheetsApis.READ_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheet_id, range=node_input.range
        ),
        requires_bearer_token=True,
    )
    return ReadCellValuesResponse(**resposne_json)


async def append_cell_values(
    node_input: AppendCellValuesInput,
) -> AppendCellValuesResponse:
    api_client: GoogleAPIClient = node_input.config._google_api_client
    json = {
        "range": node_input.range,
        "values": node_input.values,
    }

    if node_input.major_dimension is not None:
        json["majorDimension"] = node_input.major_dimension

    logger.debug(f"The json body is : {json}")

    _, resposne_json = await api_client.request(
        "POST",
        GoogleSheetsApis.APPEND_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheed_id, range=node_input.range
        ),
        requires_bearer_token=True,
        params={
            "valueInputOption": node_input.value_input_option,
            "insertDataOption": node_input.insert_data_option,
        },
        json=json,
    )
    print("Response : ", resposne_json)
    return AppendCellValuesResponse(**resposne_json)


async def update_cell_values(
    node_input: UpdateCellValuesInput,
) -> UpdateCellValuesResponse:
    api_client: GoogleAPIClient = node_input.config._google_api_client
    json = {
        "range": node_input.range,
        "values": node_input.values,
    }

    if node_input.major_dimension is not None:
        json["majorDimension"] = node_input.major_dimension

    logger.debug(f"The json body is : {json}")

    _, response_json = await api_client.request(
        "PUT",
        GoogleSheetsApis.UPDATE_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheet_id, range=node_input.range
        ),
        requires_bearer_token=True,
        params={
            "valueInputOption": node_input.value_input_option,
        },
        json=json,
    )
    print("Response : ", response_json)
    return UpdateCellValuesResponse(**response_json)


