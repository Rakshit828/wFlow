from loguru import logger
from typing import TypeVar, Optional, Union, Type, Any, Dict
from pydantic import BaseModel
from src.types.db_types import CredentialsTypeEnum

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)



