from typing import List

from .base import SearchAdapter
from ..schemas import SearchResult


class BingStubAdapter(SearchAdapter):
    name = "bing_stub"

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        # In real implementation, this would call Bing API.
        # Here we return static placeholder results.
        results = []
        for i in range(limit):
            results.append(
                SearchResult(
                    title=f"Bing Stub Result {i+1} for '{query}'",
                    url=f"https://example.com/bing/{i+1}?q={query}",
                    snippet=f"This is a placeholder snippet from Bing for '{query}'.",
                    source=self.name,
                )
            )
        return results
