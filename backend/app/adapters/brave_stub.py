from typing import List

from .base import SearchAdapter
from ..schemas import SearchResult


class BraveStubAdapter(SearchAdapter):
    name = "brave_stub"

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        # Placeholder implementation
        results = []
        for i in range(limit):
            results.append(
                SearchResult(
                    title=f"Brave Stub Result {i+1} for '{query}'",
                    url=f"https://example.com/brave/{i+1}?q={query}",
                    snippet=f"This is a placeholder snippet from Brave for '{query}'.",
                    source=self.name,
                )
            )
        return results
