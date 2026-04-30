from pydantic import BaseModel, Field, computed_field
from typing import List, Dict, Optional, Literal, Any
from src.integrations.googlecloud.shared import CommonGoogleConfigModel, CommonBaseModel
from enum import Enum

DEV_REF = "https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGetByDataFilter"
class GoogleSheetsApis(str, Enum):
    GET_SHEETS_METADATA = "/v4/spreadsheets/{spreadsheetId}"
    CREATE_NEW_SPREADSHEET = "/v4/spreadsheets"
    READ_CELL_VALUES = "/v4/spreadsheets/{spreadsheetId}/values/{range}"
    APPEND_CELL_VALUES = "/v4/spreadsheets/{spreadsheetId}/values/{range}:append"
    UPDATE_CELL_VALUES = "/v4/spreadsheets/{spreadsheetId}/values/{range}"


class CreateGoogleSheetInput(CommonBaseModel):
    title: str
    timezone: str = Field(alias="timeZone")

    config: CommonGoogleConfigModel = Field(exclude=True)


class SpreadSheetProperties(CommonBaseModel):
    title: str
    timezone: str = Field(alias="timeZone")


class CreateGoogleSheetResponse(CommonBaseModel):
    spreadsheet_id: str = Field(alias="spreadsheetId")
    spreadsheet_url: str = Field(alias="spreadsheetUrl")
    properties: SpreadSheetProperties


class ReadCellValuesInput(CommonBaseModel):
    spreadsheet_id: str = Field(alias="spreadsheetId")
    range: str
    config: CommonGoogleConfigModel


class SheetDimension(str, Enum):
    ROWS = "ROWS"
    COLUMNS = "COLUMNS"


class ReadCellValuesResponse(CommonBaseModel):
    range: str
    values: List[List[str]]
    major_dimension: str = Field(alias="majorDimension")


class AppendCellValuesInput(CommonBaseModel):
    spreadsheed_id: str = Field(alias="spreadsheetId")
    range: str
    values: List[List[Any]]
    major_dimension: Optional[SheetDimension] = Field(
        default=None, alias="majorDimension"
    )
    value_input_option: Literal["RAW", "USER_ENTERED"] = Field(
        default="USER_ENTERED", alias="valueInputOption"
    )
    insert_data_option: Literal["INSERT_ROWS", "OVERWRITE"] = Field(
        default="INSERT_ROWS", alias="insertDataOption"
    )

    config: CommonGoogleConfigModel = Field(exclude=True)


class AppendCellValuesResponse(CommonBaseModel):
    spreadsheet_id: str = Field(alias="spreadsheetId")
    updates: dict[str, Any]


class UpdateCellValuesInput(CommonBaseModel):
    spreadsheet_id: str = Field(alias="spreadsheetId")
    range: str
    values: List[List[Any]]
    major_dimension: Optional[SheetDimension] = Field(
        default=None, alias="majorDimension"
    )
    value_input_option: Literal["RAW", "USER_ENTERED"] = Field(
        default="USER_ENTERED", alias="valueInputOption"
    )

    config: CommonGoogleConfigModel = Field(exclude=True)


class UpdateCellValuesResponse(CommonBaseModel):
    spreadsheet_id: str = Field(alias="spreadsheetId")
    updated_range: str = Field(alias="updatedRange")
    updated_rows: int = Field(alias="updatedRows")
    updated_columns: int = Field(alias="updatedColumns")
    updated_cells: int = Field(alias="updatedCells")


class ReadSheetMetadataInput(CommonBaseModel):
    sheet_url: str = Field(alias="sheetUrl")
    config: CommonGoogleConfigModel

    @computed_field
    @property
    def spreadsheet_id(self) -> str:
        id = self.sheet_url.split("/")[-2].split("?")[0]
        print("Spreadsheet id is : ", id)
        return id
