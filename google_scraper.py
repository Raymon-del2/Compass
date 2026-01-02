"""Lightweight Google HTML scraper (educational / fragile).
Returns a list of dicts with title, url, snippet.
Use moderately to avoid Google rate-limits / CAPTCHA.
"""
from __future__ import annotations

import random
import re
import time
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def _parse(html: str, limit: int) -> List[Dict[str, str]]:
    """Extract organic results from Google HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, str]] = []

    for g in soup.select("div.g"):
        link = g.select_one("a")
        title_el = g.select_one("h3")
        if not link or not title_el:
            continue
        url = link["href"]
        # unwrap Google redirect URLs
        if url.startswith("/url?"):
            m = re.search(r"[?&]q=([^&]+)", url)
            if m:
                url = httpx.URL(m.group(1)).decode()
        snippet_el = g.select_one(".VwiC3b") or g.select_one(".IsZvec")
        results.append(
            {
                "title": title_el.get_text(" ", strip=True),
                "url": url,
                "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
            }
        )
        if len(results) >= limit:
            break
    return results


def search_google(query: str, *, num: int = 10, lang: str = "en") -> List[Dict[str, str]]:
    """Fetch Google search results page and parse organic results."""
    url = (
        "https://www.google.com/search?"
        f"hl={lang}&q={httpx.utils.quote(query)}&num={num}&safe=active"
    )
    html = httpx.get(url, headers=HEADERS, timeout=10).text
    # polite delay to avoid hammering Google
    time.sleep(random.uniform(2.5, 4.0))
    return _parse(html, num)
