from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    status_code: int
    details: Optional[Any] = None
