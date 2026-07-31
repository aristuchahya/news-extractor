from pydantic import BaseModel, HttpUrl


class ExtractRequest(BaseModel):
    url: HttpUrl


class LatestBySourceRequest(BaseModel):
    

    source: str
    limit: int = 10
