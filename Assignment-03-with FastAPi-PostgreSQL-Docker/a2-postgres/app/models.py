from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    done: bool


class Task(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime

    class Config:
        from_attributes = True
