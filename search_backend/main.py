from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from opensearchpy import OpenSearch
from pathlib import Path

client = OpenSearch(hosts=[{"host": "localhost", "port": 9200}])
INDEX = "pages"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# optional Google HTML scraper
try:
    from google_scraper import search_google  # type: ignore
except ModuleNotFoundError:
    search_google = None


@app.get("/search")
def search(q: str = Query(...), size: int = 10):
    """Full-text search across indexed pages."""
    resp = client.search(
        index=INDEX,
        body={
            "query": {"multi_match": {"query": q, "fields": ["title^2", "body"]}},
            "_source": ["title", "url", "body"],
            "size": size,
        },
    )
    return [
        {
            "title": h["_source"]["title"],
            "url": h["_source"]["url"],
            "snippet": h["_source"]["body"][:180] + "…",
        }
        for h in resp["hits"]["hits"]
    ]

# -------------------- static HTML -------------------- #
static_dir = Path(__file__).resolve().parent.parent / "search_frontend"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# -------------------- Google HTML endpoint -------------------- #
if search_google:
    @app.get("/ghtml")
    def ghtml(q: str = Query(...), size: int = 10):
        return search_google(q, num=size)

