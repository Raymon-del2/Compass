"""DuckDuckGo search adapter (web / images / videos / news).

- Web results come from DuckDuckGo’s public Instant-Answer API.  
- Media results come from the `duckduckgo_search` package (pip install duckduckgo_search).
"""

from __future__ import annotations

from typing import List

import httpx

# duckduckgo_search was renamed to ddgs; try new name first for compatibility
try:
    from ddgs import DDGS  # type: ignore
except ImportError:
    from duckduckgo_search import DDGS  # type: ignore

from .base import SearchAdapter
from ..schemas import SearchResult


class DuckDuckGoAdapter(SearchAdapter):
    """Unified DuckDuckGo adapter."""

    name = "duckduckgo"

    # --------------------------------------------------------------------- #
    # Web search via Instant-Answer API
    # --------------------------------------------------------------------- #
    async def _web(self, query: str, limit: int) -> List[SearchResult]:
        params = {
            "q": query,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            data = (await client.get("https://api.duckduckgo.com/", params=params)).json()

        results: List[SearchResult] = []

        # Primary “Results” array
        for item in data.get("Results", []):
            url = item.get("FirstURL", "")
            if "duckduckgo.com" in url:
                continue
            results.append(
                SearchResult(
                    title=item.get("Text", "")[:120] or query,
                    url=url,
                    snippet=item.get("Text", ""),
                    source=self.name,
                )
            )
            if len(results) >= limit:
                return results

        # Fallback: abstract block
        if (
            data.get("AbstractText")
            and data.get("AbstractURL")
            and "duckduckgo.com" not in data.get("AbstractURL")
        ):
            results.append(
                SearchResult(
                    title=data.get("Heading") or query,
                    url=data["AbstractURL"],
                    snippet=data["AbstractText"],
                    source=self.name,
                )
            )

        # Fallback: related topics
        def _walk_topics(tops):
            for t in tops:
                if "Text" in t and "FirstURL" in t:
                    if "duckduckgo.com" not in t["FirstURL"]:
                        yield t
                elif "Topics" in t:
                    yield from _walk_topics(t["Topics"])

        for t in _walk_topics(data.get("RelatedTopics", [])):
            results.append(
                SearchResult(
                    title=t["Text"].split(" - ")[0][:120],
                    url=t["FirstURL"],
                    snippet=t["Text"],
                    source=self.name,
                )
            )
            if len(results) >= limit:
                break

        if not results:
            # Last-resort link back to DuckDuckGo
            results.append(
                SearchResult(
                    title=query,
                    url=f"https://duckduckgo.com/?q={query}",
                    snippet="View more results on DuckDuckGo",
                    source=self.name,
                )
            )
        return results[:limit]

    # --------------------------------------------------------------------- #
    # Media helpers (images / videos / news) via duckduckgo_search
    # --------------------------------------------------------------------- #
    @staticmethod
    def _media_to_results(items: list[dict], kind: str, query: str, limit: int) -> List[SearchResult]:
        out: List[SearchResult] = []
        for item in items:
            url_candidate = (
                item.get("source") or item.get("url") or item.get("image")
            )
            if not url_candidate or not str(url_candidate).startswith("http"):
                continue  # skip invalid entries

            if kind == "images":
                out.append(
                    SearchResult(
                        title=item.get("title") or query,
                        url=url_candidate,
                        thumb=item.get("image") or item.get("thumbnail"),
                        snippet="",
                        source="duckduckgo",
                    )
                )
            elif kind == "videos":
                out.append(
                    SearchResult(
                        title=item.get("title") or query,
                        url=url_candidate,
                        thumb=item.get("thumbnail"),
                        snippet=item.get("description") or "",
                        source="duckduckgo",
                    )
                )
            else:  # news
                out.append(
                    SearchResult(
                        title=item.get("title") or query,
                        url=url_candidate,
                        thumb=None,
                        snippet=item.get("body") or "",
                        source="duckduckgo",
                    )
                )
            if len(out) >= limit:
                break
        return out

    # --------------------------------------------------------------------- #
    # Public entry-point
    # --------------------------------------------------------------------- #
    async def search(  # type: ignore[override]
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        start: int = 1,
        **_: object,
    ) -> List[SearchResult]:
        if search_type == "web":
            return await self._web(query, limit)

        # Media search
        with DDGS() as ddgs:
            if search_type == "images":
                items = list(ddgs.images(query, max_results=limit))
            elif search_type == "videos":
                items = list(ddgs.videos(query, max_results=limit))
            elif search_type == "news":
                items = list(ddgs.news(query, max_results=limit))
            else:
                items = []

        results = self._media_to_results(items, search_type, query, limit)
        if not results:
            results.append(
                SearchResult(
                    title=query,
                    url=f"https://duckduckgo.com/?q={query}",
                    snippet=f"View more {search_type} results on DuckDuckGo",
                    source=self.name,
                )
            )
        return results[:limit]