from pydantic import BaseModel, Field, ConfigDict, computed_field, PrivateAttr
from typing import Optional, List
from src.config import CONFIG
from datetime import datetime
from typing import List, Literal
from enum import Enum


from src.integrations.googlecloud.shared import CommonBaseModel, CommonGoogleConfigModel



class GDriveApis(str, Enum):
    UPLOAD_FILE = "/upload/drive/v3/files"
    """Create/Upload a new file in the google drive."""