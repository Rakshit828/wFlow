from typing import Literal, TypedDict


class MetadataFiltersOptions(TypedDict):
    criteria: Literal["eq", "lt", "lte", "gt", "gte", "neq"]
    value: str | int | float
