from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  
    code: str = Field(index=True)  
    value: float  
    quantity: int = 1 
    category: str = "currency"  
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        table_name = "items"  