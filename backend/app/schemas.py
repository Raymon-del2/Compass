from pydantic import BaseModel, HttpUrl
from typing import List

class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str | None = None
    source: str  # identifier of the adapter
    thumb: HttpUrl | None = None
    display_link: str | None = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    next_cursor: str | None = None
