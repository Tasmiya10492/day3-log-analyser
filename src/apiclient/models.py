from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Book(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    status: str
    category: str
    created: datetime


class BookPage(BaseModel):
    items: list[Book]
    page: int = Field(ge=1)
    page_size: int = Field(gt=0)
    total: int = Field(ge=0)
    has_more: bool
