"""Turso database adapter
Returns results from a Turso (libSQL) database table called `search_index`.
The table must contain at least `title`, `url`, and `snippet` columns.
"""

from typing import List
from libsql_client import create_client

from ..schemas import SearchResult
from ..config import settings


class TursoAdapter:
    """Adapter that queries a Turso DB and maps rows to SearchResult."""

    name = "turso"

    def __init__(self, api_key: str | None = None):  # api_key unused but keeps signature
        if not settings.turso_db_url or not settings.turso_auth_token:
            raise RuntimeError("Turso credentials not configured (TURSO_DB_URL / TURSO_AUTH_TOKEN)")
        self._client = create_client(
            url=settings.turso_db_url,
            auth_token=settings.turso_auth_token,
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        start: int = 1,
        **kwargs,
    ) -> List[SearchResult]:
        """Performs a simple LIKE match on the `title` column.
        Adjust SQL as needed for your schema.
        """
        sql = "SELECT title, url, snippet FROM search_index WHERE title LIKE ? LIMIT ? OFFSET ?"
        # naive pagination using start param (1-indexed)
        rows = await self._client.execute(sql, [f"%{query}%", limit, max(start - 1, 0)])
        return [
            SearchResult(title=row[0], url=row[1], snippet=row[2] or "", source=self.name)
            for row in rows
        ]
