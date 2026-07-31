

from pydantic import BaseModel, Field


class Image(BaseModel):
    url: str
    caption: str | None = None


class Tag(BaseModel):
    name: str


class Article(BaseModel):
    url: str
    title: str = ""
    author: str | None = None
    published_date: str | None = None
    language: str | None = None
    source: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    image: str | None = None
    summary: str | None = None
    content: str = ""
    text_length: int = 0
    word_count: int = 0
    extraction_method: str = ""
    scrapped_at: str = ""
    status: str = "success"
    error: str | None = None
