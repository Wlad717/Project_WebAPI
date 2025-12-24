from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ItemCreate(BaseModel):
    name: str
    code: str
    value: float
    quantity: int = 1
    category: str = "currency"

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    quantity: Optional[int] = None
    category: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    code: str
    value: float
    quantity: int
    category: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    message: str
    status: str