"""Adapter that reads stored pages from the OpenSearch index.
Returns results previously written by the crawler, /gapi, /fetch source=serpapi, etc.
"""
from typing import List
import os
from opensearchpy import OpenSearch

from ..schemas import SearchResult


class LocalIndexAdapter:
    name = "local_index"

    def __init__(self, api_key: str | None = None):  # api_key kept for signature compatibility
        url = os.getenv("OPENSEARCH_URL")
        if not url:
            raise RuntimeError("OPENSEARCH_URL not set; local_index adapter disabled")
        self._client = OpenSearch(url, verify_certs=False)
        self._index = "pages"

    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        start: int = 1,
        **kwargs,
    ) -> List[SearchResult]:
        if not query:
            return []
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "snippet", "body"],
                }
            },
            "from": max(start - 1, 0),
            "size": limit,
        }
        try:
            res = self._client.search(index=self._index, body=body)
        except Exception:
            return []
        hits = res.get("hits", {}).get("hits", [])
        results: List[SearchResult] = []
        for h in hits:
            src = h.get("_source", {})
            results.append(
                SearchResult(
                    title=src.get("title") or query,
                    url=src.get("url"),
                    snippet=src.get("snippet", ""),
                    source=self.name,
                )
            )
        return results
