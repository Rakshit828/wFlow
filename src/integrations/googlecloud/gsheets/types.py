from pydantic import BaseModel, Field, computed_field
from typing import List, Dict, Optional, Literal
from src.integrations.googlecloud.shared import CommonGoogleConfigModel, CommonBaseModel
from enum import Enum


class GoogleSheetsApis(str, Enum):
    GET_SHEETS_METADATA = "/v4/spreadsheets/{spreadsheetId}"


class ReadSheetMetadataInput(CommonBaseModel):
    sheet_url: str = Field(alias="sheetUrl")
    config: CommonGoogleConfigModel

    @computed_field
    @property
    def spreadsheet_id(self) -> str:
        id = self.sheet_url.split("/")[-2].split("?")[0]
        print("Spreadsheet id is : ", id)
        return id
