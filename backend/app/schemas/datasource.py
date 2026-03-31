from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DataSourceCreate(BaseModel):
    name: str
    type: str  # "file" or "mysql"


class DataSourceResponse(BaseModel):
    id: int
    name: str
    type: str
    schema_info: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    id: int
    name: str
    table_name: Optional[str] = None
    row_count: int
    columns: Optional[dict] = None
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True
