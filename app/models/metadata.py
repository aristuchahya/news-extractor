from pydantic import BaseModel, Field


class Metadata(BaseModel):
    title: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    canonical_url: str | None = None

    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_site_name: str | None = None
    og_type: str | None = None

    robots: str | None = None
    author: str | None = None
    published_date: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
