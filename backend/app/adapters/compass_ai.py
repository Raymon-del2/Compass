"""Compass AI Developer Portal adapter.
Uses the Compass AI REST API to query indexed corpus and fetch fresh content.
"""
from __future__ import annotations

import httpx
from typing import List, Dict, Any
from ..schemas import SearchResult
from .base import SearchAdapter


class CompassAIAdapter(SearchAdapter):
    """Compass AI search adapter for multiple verticals (web, images, videos, news, maps, reviews, shopping)."""
    
    name = "compass_ai"
    base_url = "https://compassb.vercel.app"
    
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str, limit: int = 10, search_type: str = "web", start: int = 1) -> List[SearchResult]:
        """Search using Compass AI API."""
        try:
            # First try to search stored pages
            search_url = f"{self.base_url}/search"
            params = {"q": query}
            
            if search_type != "web":
                params["type"] = search_type
            
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            stored_results = response.json()
            if isinstance(stored_results, dict):
                stored_results = stored_results.get("results", [])

            # fallback: retry without type filter if nothing returned (index may not label vertical)
            if not stored_results and search_type != "web":
                response2 = await self.client.get(search_url, params={"q": query})
                if response2.status_code == 200:
                    stored_results = response2.json()
                    if isinstance(stored_results, dict):
                        stored_results = stored_results.get("results", [])
            
            # Index-only mode: never call /api/fetch. Rely solely on stored index.
            combined_items: List[dict] = stored_results or []
            
            # Convert to SearchResult format (dedupe by url)
            results: List[SearchResult] = []
            seen_urls = set()
            for item in combined_items:
                result = self._convert_to_search_result(item, search_type)
                if result and result.url not in seen_urls:
                    results.append(result)
                    seen_urls.add(result.url)
                if len(results) >= limit:
                    break
            return results
            
        except httpx.HTTPError as e:
            print(f"Compass AI API error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in Compass AI adapter: {e}")
            return []
    
    async def _fetch_fresh_content(self, query: str, search_type: str) -> List[dict]:
        """Fetch fresh content using Compass AI fetch API."""
        fetch_url = f"{self.base_url}/api/fetch"
        
        payload = {
            "query": query,
            "kind": search_type,
            "auto": "0"
        }
        
        # Add API key for all verticals except maps
        if search_type != "maps" and self.api_key:
            payload["apiKey"] = self.api_key
        
        try:
            response = await self.client.post(
                fetch_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            # API returns either {'results': [...]} or list
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            elif isinstance(data, list):
                return data
            else:
                return []
        except httpx.HTTPError as e:
            print(f"Failed to fetch fresh content: {e}")
            return []
    
    def _convert_to_search_result(self, item: Dict[str, Any], search_type: str) -> SearchResult | None:
        """Convert Compass AI result to SearchResult format."""
        try:
            # Accept tuple-string like "('url','title',snippet,thumb)" from stored index
            if 'value' in item and isinstance(item['value'], str):
                try:
                    parts = eval(item['value'])  # trusted data from our backend index
                    url = parts[0]
                    title = parts[1]
                    snippet = parts[2] if len(parts) > 2 else ''
                    thumb = parts[3] if len(parts) > 3 else None
                    item = {
                        'url': url,
                        'title': title,
                        'snippet': snippet,
                        'thumb': thumb,
                    }
                except Exception:
                    pass

            # Handle different result formats for different verticals
            if search_type == "images":
                return SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    thumb=item.get("thumb"),
                    display_link=item.get("displayUrl")
                )
            elif search_type == "videos":
                return SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=self.name,
                    thumb=item.get("thumb"),
                    display_link=item.get("displayUrl")
                )
            elif search_type == "news":
                return SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    display_link=item.get("source")
                )
            elif search_type == "maps":
                return SearchResult(
                    title=item.get("title", item.get("formattedAddress", "")),
                    url=item.get("osmUrl", ""),
                    snippet=item.get("formattedAddress", ""),
                    source=self.name,
                    thumb=item.get("thumbnail")
                )
            elif search_type in ["reviews", "shopping"]:
                return SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    thumb=item.get("thumb"),
                    display_link=item.get("displayUrl")
                )
            else:  # web
                return SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    display_link=item.get("displayUrl")
                )
        except Exception as e:
            print(f"Error converting result: {e}")
            return None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
