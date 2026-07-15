from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(default=0, ge=0)


class Item(ItemCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
