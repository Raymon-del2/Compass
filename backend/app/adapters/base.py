from abc import ABC, abstractmethod
from typing import List
from ..schemas import SearchResult


class SearchAdapter(ABC):
    """Abstract base class for search adapters."""

    name: str  # unique identifier

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @abstractmethod
    async def search(self, query: str, limit: int = 10, search_type: str = "web", start: int = 1) -> List[SearchResult]:
        """Return a list of SearchResult given a query."""
        raise NotImplementedError
