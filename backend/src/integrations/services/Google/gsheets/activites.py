from src.integrations.services.Google.gsheets.types import (
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
from typing import Any
from src.integrations.services.Google import GoogleRequestHandler
from src.integrations.components.types import RequestOptions
from loguru import logger
from temporalio import activity


async def get_sheets_metadata(node_input: ReadSheetMetadataInput) -> dict[str, Any]:
    api_client: GoogleRequestHandler = node_input.config.service_handler
    _, response_json = await api_client.handle(
        "GET",
        GoogleSheetsApis.GET_SHEETS_METADATA.format(
            spreadsheetId=node_input.spreadsheet_id
        ),
    )
    return response_json


@activity.defn
async def create_google_sheet(
    node_input: CreateGoogleSheetInput,
) -> CreateGoogleSheetResponse:
    json = {"properties": node_input.model_dump(by_alias=True)}
    options: RequestOptions = {
        "json": json,
        "data": None,
        "params": None,
        "headers": None,
        "timeout": None,
    }
    api_client: GoogleRequestHandler = node_input.config.service_handler
    _, response_json = await api_client.handle(
        "POST",
        endpoint=GoogleSheetsApis.CREATE_NEW_SPREADSHEET,
        options=options,
    )
    return CreateGoogleSheetResponse.model_validate(response_json)


@activity.defn
async def read_cell_values(node_input: ReadCellValuesInput) -> ReadCellValuesResponse:
    api_client: GoogleRequestHandler = node_input.config.service_handler
    _, response_json = await api_client.handle(
        "GET",
        GoogleSheetsApis.READ_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheet_id, range=node_input.range
        ),
    )
    return ReadCellValuesResponse(**response_json)


@activity.defn
async def append_cell_values(
    node_input: AppendCellValuesInput,
) -> AppendCellValuesResponse:
    api_client: GoogleRequestHandler = node_input.config.service_handler
    json: dict[str, Any] = {
        "range": node_input.range,
        "values": node_input.values,
    }
    params = {
        "valueInputOption": node_input.value_input_option,
        "insertDataOption": node_input.insert_data_option,
    }
    options: RequestOptions = {
        "json": json,
        "params": params,
        "data": None,
        "headers": None,
        "timeout": None,
    }

    if node_input.major_dimension is not None:
        json["majorDimension"] = node_input.major_dimension

    logger.debug(f"The json body is : {json}")

    _, response_json = await api_client.handle(
        "POST",
        GoogleSheetsApis.APPEND_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheed_id, range=node_input.range
        ),
        options=options,
    )
    print("Response : ", response_json)
    return AppendCellValuesResponse(**response_json)


@activity.defn
async def update_cell_values(
    node_input: UpdateCellValuesInput,
) -> UpdateCellValuesResponse:
    api_client: GoogleRequestHandler = node_input.config.service_handler
    json: dict[str, Any] = {
        "range": node_input.range,
        "values": node_input.values,
    }
    params = {
        "valueInputOption": node_input.value_input_option,
    }
    options: RequestOptions = {
        "json": json,
        "params": params,
        "data": None,
        "headers": None,
        "timeout": None,
    }

    if node_input.major_dimension is not None:
        json["majorDimension"] = node_input.major_dimension

    logger.debug(f"The json body is : {json}")

    _, response_json = await api_client.handle(
        "PUT",
        GoogleSheetsApis.UPDATE_CELL_VALUES.format(
            spreadsheetId=node_input.spreadsheet_id, range=node_input.range
        ),
        options=options,
    )
    print("Response : ", response_json)
    return UpdateCellValuesResponse(**response_json)
