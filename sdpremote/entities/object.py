from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Object(BaseModel):
    key: str
    checksum: Optional[str] = Field(
        None,
        description='`null` when data is `null`',
    )
    creator: str
    timestamp: datetime
