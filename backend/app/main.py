from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
try:
    from opensearchpy import OpenSearch, helpers  # type: ignore
except ImportError:
    OpenSearch = None  # type: ignore
    helpers = None  # type: ignore
import os, httpx
import importlib
import asyncio

from .schemas import SearchResponse, SearchResult
from .config import settings

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
client = None
if OpenSearch and OPENSEARCH_URL:
    client = OpenSearch(OPENSEARCH_URL, verify_certs=False)

app = FastAPI(title="Compass Search API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "message": "Python runtime loaded"}

# Allow frontend running on localhost ports to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# dynamically load adapter classes based on settings
# add local_index adapter if OpenSearch available
if client and "local_index" not in settings.enabled_adapters:
    settings.enabled_adapters.insert(0, "local_index")

_adapter_instances = {}
for adapter_name in settings.enabled_adapters:
    try:
        module_path = f"app.adapters.{adapter_name}"
        module = importlib.import_module(module_path)
        # Convention: Adapter class ends with Adapter and has attribute 'name'
        adapter_cls = None
        for attr in module.__dict__.values():
            if isinstance(attr, type):
                if getattr(attr, 'name', None) == adapter_name:
                    adapter_cls = attr
                    break
        if not adapter_cls:
            raise ImportError("Adapter class not found")
        api_key = settings.api_keys.get(adapter_name)
        # Special handling for Compass AI adapter
        if adapter_name == "compass_ai":
            api_key = settings.compass_api_key
        _adapter_instances[adapter_name] = adapter_cls(api_key=api_key)
    except Exception as exc:
        print(f"[Compass] Warning: could not load adapter '{adapter_name}': {exc}")


async def _aggregate_results(query: str, limit: int, search_type: str = "web", start: int = 1) -> List[SearchResult]:
    """Run searches concurrently across adapters and merge results."""
    tasks = [adapter.search(query, limit, search_type=search_type, start=start) for adapter in _adapter_instances.values()]
    results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    merged: List[SearchResult] = []
    for res in results_lists:
        if isinstance(res, Exception):
            print(f"[Compass] Adapter error: {res}")
            continue
        merged.extend(res)

    # Simple dedup by url keeping first appearance, limit output
    seen = set()
    deduped: List[SearchResult] = []
    for item in merged:
        if item.url not in seen:
            deduped.append(item)
            seen.add(item.url)
        if len(deduped) >= limit:
            break
    return deduped


import base64, json


def _encode_cursor(start: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"s": start}).encode()).decode()

def _decode_cursor(token: str | None) -> int:
    if not token:
        return 1
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        return int(data.get("s", 1))
    except Exception:
        return 1


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = 10,
    type: str = Query("web", alias="type"),
    cursor: str | None = None,
):
    if not q:
        raise HTTPException(status_code=400, detail="Query 'q' is required")
    start = _decode_cursor(cursor)
    results = await _aggregate_results(q, limit, search_type=type, start=start)
    next_cursor = _encode_cursor(start + limit)
    return SearchResponse(query=q, results=results, next_cursor=next_cursor)


SERP_KEY = os.getenv("SERP_API_KEY", "")
SERPER_KEY = os.getenv("SERPER_API_KEY", "")

async def _serperapi(q: str, limit: int = 10):
    if not SERPER_KEY:
        raise HTTPException(status_code=500, detail="SERPER_API_KEY not configured")
    params = {
        "q": q,
        "num": min(limit, 10),
        "apiKey": SERPER_KEY,
    }
    data = httpx.get("https://google.serper.dev/search", params=params, timeout=10).json()
    items = []
    for it in data.get("organic", [])[:limit]:
        items.append({"title": it.get("title"), "url": it.get("link"), "snippet": it.get("snippet", "")})
    # store to pages
    if items and client:
        actions = [{"_op_type": "index", "_index": PAGES_INDEX, "_id": it["url"], **it} for it in items]
        helpers.bulk(client, actions, refresh=True)
    return [SearchResult(**it, source="serperapi") for it in items]

@app.get("/fetch", response_model=List[SearchResult])
async def fetch_api(
    q: str = Query(..., description="Search query"),
    limit: int = 10,
    source: str = "internal",
    key: str | None = Query(None, description="Override SerpAPI key"),
    links: str | None = Query(None, description="Newline-separated URLs to store")
):
    # 1. If links provided, store them as minimal docs
    if links:
        urls = [u.strip() for u in links.splitlines() if u.strip()]
        stored: List[SearchResult] = []
        for u in urls:
            doc = {"title": u, "url": u, "snippet": ""}
            if client:
                client.index(index=PAGES_INDEX, id=u, body=doc, refresh=True)
            stored.append(SearchResult(**doc, source="manual"))
        return stored

    # 2. If source=serpapi, use optional key override
    if source == "serpapi":
        # temporarily override env key if provided
        global SERP_KEY
        old = SERP_KEY
        if key:
            SERP_KEY = key
        try:
            return await _serpapi(q, limit)
        finally:
            SERP_KEY = old

    # 3. Default: aggregate internal adapters
    return await _aggregate_results(q, limit)


# -------------------- Google Custom Search API -------------------- #
import os, httpx
if helpers is not None:
    from opensearchpy import helpers  # already imported via try-above

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX  = os.getenv("GOOGLE_CSE_ID")
CACHE_INDEX = "google_cache"
PAGES_INDEX = "pages"
# ensure pages index exists when OpenSearch available
if client and not client.indices.exists(index=PAGES_INDEX):
    client.indices.create(index=PAGES_INDEX)

if GOOGLE_KEY and GOOGLE_CX:
    # ensure cache index exists (simple mapping)
    if client and not client.indices.exists(index=CACHE_INDEX):
        client.indices.create(index=CACHE_INDEX)

    @app.get("/gapi", response_model=List[SearchResult])
    async def gapi(q: str = Query(...), size: int = 10):
        # 1. check cache
        cached = client.get(index=CACHE_INDEX, id=q, ignore=[404])
        if cached and cached.get("found"):
            return cached["_source"]["items"][:size]

        params = {
            "key": GOOGLE_KEY,
            "cx": GOOGLE_CX,
            "q": q,
            "num": min(size, 10),
        }
        data = httpx.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10).json()
        items = [
            {
                "title": it["title"],
                "url": it["link"],
                "snippet": it.get("snippet", ""),
            }
            for it in data.get("items", [])
        ]
        # store in cache
        if client:
            client.index(index=CACHE_INDEX, id=q, body={"items": items}, refresh=True)
        # also upsert into main pages index for global search
        if client:
            actions = [
                {"_op_type": "index", "_index": PAGES_INDEX, "_id": it["url"], **it}
                for it in items
            ]
            helpers.bulk(client, actions, refresh=True)
        return items[:size]


HTML_PAGE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\" />
<title>Compass Search</title>
<style>
body{font-family:sans-serif;max-width:600px;margin:2rem auto}input{width:80%}button{padding:.3rem .6rem}li{margin:.4rem 0}
</style>
</head>
<body>
<h2>Compass Search</h2>
<input id=\"q\" placeholder=\"search...\" /> <button onclick=\"go()\">Go</button>
<ul id=\"out\"></ul>
<script>
async function go(){
 const q=document.getElementById('q').value;
 const r=await fetch('/search?q='+encodeURIComponent(q));
 const data=await r.json();
 const out=document.getElementById('out');out.innerHTML='';
 data.results.forEach(i=>{
  const li=document.createElement('li');
  li.innerHTML=`<a href='${i.url}' target='_blank'>${i.title}</a> - ${i.snippet}`;
  out.appendChild(li);
 });
}
</script>
</body></html>"""

FETCH_UI = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Fetch Inserter</title><style>body{font-family:sans-serif;max-width:600px;margin:2rem auto}input,textarea{width:100%;margin:0.5rem 0}button{padding:0.3rem 0.6rem}</style></head>
<body>
<h2>Fetch &amp; Store</h2>
<input id="key" placeholder="SerpAPI key (optional, overrides env)">
<input id="q" placeholder="Search query (optional)">
<textarea id="links" rows="5" placeholder="One URL per line (optional)"></textarea>
<button onclick="go()">Fetch</button>
<p id="msg"></p>
<script>
async function go(){
 const key=document.getElementById('key').value.trim();
 const q=document.getElementById('q').value.trim();
 const links=document.getElementById('links').value.trim().split('\\n').filter(l=>l.trim());
 if(!q && links.length===0){alert('Enter a query or at least one URL');return;}
 const m=document.getElementById('msg');m.textContent='Fetching...';
 const params=new URLSearchParams({q});
 if(key) params.set('key',key);
 if(links.length>0) params.set('links',links.join('\\n'));
 try{
   const r=await fetch('/fetch?'+params.toString());
   if(!r.ok){m.textContent='Error '+r.status;return;}
   const data=await r.json();
   m.textContent='Stored '+data.length+' results';
 }catch(e){m.textContent='Network error';}
}
</script>
</body></html>"""

@app.get("/", response_class=HTMLResponse)
async def root() -> Response:
    return HTML_PAGE


@app.get('/fetch-ui', response_class=HTMLResponse)
async def fetch_ui() -> Response:
    return FETCH_UI


@app.get('/debug')
async def debug():
    loaded = [name for name in _adapter_instances.keys()]
    return {
        "opensearch_url_set": bool(OPENSEARCH_URL),
        "client_exists": client is not None,
        "loaded_adapters": loaded,
        "enabled_adapters": settings.enabled_adapters,
    }


# avoid 404 spam in browser for favicon
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get('/favicon.png', include_in_schema=False)
async def favicon_png():
    return Response(status_code=204)
