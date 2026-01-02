from typing import List, Tuple
import asyncio
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import SearchAdapter
from ..schemas import SearchResult


class GoogleCSEAdapter(SearchAdapter):
    """Google Custom Search adapter with round-robin key rotation.

    • Reads comma-separated API keys from GOOGLE_API_KEYS
    • Reads CXs from GOOGLE_CSE_CXS (same index as keys) or GOOGLE_CSE_CX
    • Marks a key exhausted when API responds 429, then keeps rotating.
    """

    name = "google_cse"

    _idx: int = 0
    _exhausted: set[int] = set()
    _lock: asyncio.Lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @classmethod
    async def _next_credentials(cls) -> tuple[int, str, str]:  # returns idx,key,cx
        """Return (api_key, cx) pair in round-robin across the lists."""
        async with cls._lock:
            keys = [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()]
            cxs = [c.strip() for c in os.getenv("GOOGLE_CSE_CXS", "").split(",") if c.strip()]
            if not keys:
                raise RuntimeError("GOOGLE_API_KEYS not set or empty")
            total = len(keys)
            for _ in range(total):
                idx = cls._idx % total
                cls._idx += 1
                if idx in cls._exhausted:
                    continue  # skip exhausted key
                key = keys[idx]
                cx = cxs[idx % len(cxs)] if cxs else os.getenv("GOOGLE_CSE_CX")
                if not cx:
                    continue
                return idx, key, cx
            raise RuntimeError("All Google CSE keys exhausted or missing")

    async def search(self, query: str, limit: int = 10, search_type: str = "web", start: int = 1) -> List[SearchResult]:
        attempts = 0
        last_err: Exception | None = None
        total_keys = len([k for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()])
        while attempts < total_keys:
            try:
                idx, api_key, cx = await self._next_credentials()
            except RuntimeError as e:
                raise e
            try:
                service = build("customsearch", "v1", developerKey=api_key, cache_discovery=False)
                params = dict(q=query, cx=cx, num=min(limit, 10), start=start)
                if search_type == "images":
                    params["searchType"] = "image"
                elif search_type == "videos":
                    params["q"] = f"{query} site:youtube.com"
                resp = service.cse().list(**params).execute()
                items = resp.get("items", [])
                break  # success
            except Exception as e:
                from googleapiclient.errors import HttpError
                if isinstance(e, HttpError) and e.resp.status == 429:
                    # mark exhausted and retry next key
                    self._exhausted.add(idx)
                    attempts += 1
                    last_err = e
                    continue
                raise
        else:
            raise last_err or RuntimeError("No usable Google keys left")
        results: List[SearchResult] = []
        for item in items:
            if search_type == "images":
                image_link = item.get("link", "")
                page_link = item.get("image", {}).get("contextLink") or image_link
                link = page_link
                thumb = image_link
            else:
                link = item.get("link", "")
                # try thumbnail from pagemap
                thumb = None
                thumbs = item.get("pagemap", {}).get("cse_thumbnail") or []
                if thumbs:
                    thumb = thumbs[0].get("src")
            # force https when possible
            if thumb and thumb.startswith("http:"):
                thumb = thumb.replace("http:", "https:")
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("snippet", ""),
                    source="google_cse",
                    thumb=thumb,
                    display_link=item.get("displayLink", ""),
                )
            )
        return results
