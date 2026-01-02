import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

/* ---------- Types ---------- */
interface Result {
  title: string;
  url: string;
  snippet?: string;
  source: string;
  thumb?: string;
  display_link?: string;
}
type Suggestion = { title: string; img?: string; desc?: string };

/* ---------- Helpers ---------- */
const API_BASE =
  import.meta.env.VITE_COMPASS_API || 'http://localhost:8000';
const useQueryParam = (k: string) =>
  new URLSearchParams(useLocation().search).get(k) || '';
const initPager = () => ({
  cursor: null as string | null,
  prev: [] as string[],
  next: null as string | null,
  page: 1,
});

/* ---------- Component ---------- */
const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const q = useQueryParam('q');

  /* autocomplete -------------------------------------- */
  const [query, setQuery] = useState(q);
  const [sugs, setSugs] = useState<Suggestion[]>([]);
  const timer = useRef<number>();
  const inputRef = useRef<HTMLInputElement | null>(null);

  /* core data ----------------------------------------- */
  const [tab, setTab] =
    useState<'all' | 'images' | 'news' | 'videos'>('all');
  const [web, setWeb] = useState<Result[]>([]);
  const [news, setNews] = useState<Result[]>([]);
  const [videos, setVideos] = useState<Result[]>([]);
  const [images, setImages] = useState<Result[]>([]);
  const [viewImg, setViewImg] = useState<Result | null>(null); // right-panel
  const [panel, setPanel] = useState<
    | { title: string; description?: string; extract?: string; thumb?: string }
    | null
  >(null);
  const [error, setError] = useState('');

  /* paging */
  const [webP, setWebP] = useState(initPager);
  const [newsP, setNewsP] = useState(initPager);
  const [vidP, setVidP] = useState(initPager);

  /* misc flags */
  const [lWeb, setLWeb] = useState(false);
  const [lNews, setLNews] = useState(false);
  const [lVid, setLVid] = useState(false);
  const [lImg, setLImg] = useState(false);
  const [hasMoreImg, setHasMoreImg] = useState(true);

  /* img infinite-scroll cursor */
  const [imgCursor, setImgCursor] = useState<string | null>(null);
  const sentinel = useRef<HTMLDivElement | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null); // for outside-click

  const url = (t: string, c?: string | null) =>
    `${API_BASE}/search?type=${t}&q=${encodeURIComponent(q)}${
      c ? `&cursor=${encodeURIComponent(c)}` : ''
    }`;

  /* ------------- data fetch helpers ------------- */
  const fetchList = async (
    t: string,
    p: any,
    setP: any,
    setLoading: any,
    setItems: any,
  ) => {
    setLoading(true);
    try {
      const r = await fetch(url(t, p.cursor));
      const d = await r.json();
      setItems(d.results);
      setP((x: any) => ({ ...x, next: d.next_cursor || null }));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  /* pager component */
  const step = (p: any, setP: any, dir: 'next' | 'prev') => {
    if (dir === 'next' && p.next) {
      setP({
        cursor: p.next,
        prev: [...p.prev, p.cursor || ''],
        next: null,
        page: p.page + 1,
      });
    } else if (dir === 'prev' && p.prev.length) {
      const pr = [...p.prev];
      const cur = pr.pop();
      setP({ cursor: cur || null, prev: pr, next: null, page: p.page - 1 });
    }
  };
  const Pager = ({ p, setP }: { p: any; setP: any }) => (
    <div className="pager">
      <button
        className={`page-btn${p.prev.length ? '' : ' disabled'}`}
        disabled={!p.prev.length}
        onClick={() => step(p, setP, 'prev')}
      >
        ← Previous
      </button>
      <span className="page-info">Page {p.page}</span>
      <button
        className={`page-btn${p.next ? '' : ' disabled'}`}
        disabled={!p.next}
        onClick={() => step(p, setP, 'next')}
      >
        Next →
      </button>
    </div>
  );

  const doSearch = (term: string) =>
    navigate(`/search?q=${encodeURIComponent(term)}`);

  /* ---------------- effects ---------------- */
  useEffect(() => setQuery(q), [q]);

  /* fetch lists per tab */
  useEffect(() => {
    if (!q) return;
    if (tab === 'all') fetchList('web', webP, setWebP, setLWeb, setWeb);
    if (tab === 'news') fetchList('news', newsP, setNewsP, setLNews, setNews);
    if (tab === 'videos')
      fetchList('videos', vidP, setVidP, setLVid, setVideos);
    // eslint-disable-next-line
  }, [tab, q, webP.cursor, newsP.cursor, vidP.cursor]);

  /* wiki panel */
  useEffect(() => {
    if (!q || tab !== 'all') return;
    (async () => {
      try {
        const r = await fetch(
          `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(
            q,
          )}`,
        );
        const d = await r.json();
        if (d.extract)
          setPanel({
            title: d.title,
            description: d.description,
            extract: d.extract,
            thumb: d.thumbnail?.source,
          });
        else setPanel(null);
      } catch {
        setPanel(null);
      }
    })();
  }, [q, tab]);

  /* reset images on new search */
  useEffect(() => {
    setImgCursor(null);
    setImages([]);
    setViewImg(null);
    setHasMoreImg(true);
  }, [q]);

  /* image infinite scroll fetch */
  useEffect(() => {
    if (tab !== 'images' || !q || !hasMoreImg) return;
    setLImg(true);
    (async () => {
      try {
        const r = await fetch(url('images', imgCursor));
        const d = await r.json();
        if (!d.results.length) setHasMoreImg(false);
        else setImages((prev) => [...prev, ...d.results]);
        if (!d.results.length) setError('No images found');
        setImgCursor(d.next_cursor);
        if (!d.next_cursor) setHasMoreImg(false);
      } finally {
        setLImg(false);
      }
    })();
  }, [q, tab, imgCursor]);

  /* scroll fallback */
  useEffect(() => {
    if (tab !== 'images') return;
    const onScroll = () => {
      if (!hasMoreImg || lImg) return;
      if (window.innerHeight + window.scrollY + 1500 >= document.body.scrollHeight)
        setImgCursor((c) => c || '');
    };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, [tab, hasMoreImg, lImg]);

  /* IntersectionObserver sentinel */
  useEffect(() => {
    if (tab !== 'images') return;
    const obs = new IntersectionObserver(
      (e) => {
        if (e[0].isIntersecting && hasMoreImg && !lImg)
          setImgCursor((c) => c || '');
      },
      { rootMargin: '1000px 0px' },
    );
    if (sentinel.current) obs.observe(sentinel.current);
    return () => obs.disconnect();
  }, [tab, hasMoreImg, lImg]);

  /* outside click hides suggestions */
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node))
        setSugs([]);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  /* autocomplete input */
  const onInput = (val: string) => {
    setQuery(val);
    setSugs(val ? [{ title: val }] : []);
    clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => {
      if (!val) return setSugs([]);
      try {
        const r = await fetch(
          `https://en.wikipedia.org/w/api.php?origin=*&action=opensearch&limit=8&format=json&search=${encodeURIComponent(
            val,
          )}`,
        );
        const j = await r.json();
        const titles: string[] = j[1] || [];
        const enriched: Suggestion[] = await Promise.all(
          titles.map(async (t) => {
            try {
              const r2 = await fetch(
                `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(
                  t,
                )}`,
              );
              const d = await r2.json();
              return {
                title: t,
                img: d.thumbnail?.source,
                desc: d.description,
              } as Suggestion;
            } catch {
              return { title: t } as Suggestion;
            }
          }),
        );
        const custom = { title: val } as Suggestion;
        setSugs([
          custom,
          ...enriched.filter((s) => s.title.toLowerCase() !== val.toLowerCase()),
        ]);
      } catch {
        setSugs([]);
      }
    }, 300);
  };

  const anyLoad = lWeb || lNews || lVid || lImg;

  /* ---------------- render ---------------- */
  return (
    <div
      className={`results-page ${tab === 'images' ? 'images-mode' : ''} ${
        viewImg ? 'viewer-open' : ''
      }`}
    >
      <div className={`top-loader ${anyLoad ? 'visible' : ''}`} />

      {/* header */}
      <header className="results-header">
        <a href="/" className="logo-small">
          <img src="/Compass.png" alt="Compass" />
        </a>

        <div className="search-wrapper" ref={wrapRef}>
          <form
            className="search-box"
            onSubmit={(e) => {
              e.preventDefault();
              setSugs([]);
              doSearch(query.trim());
            }}
          >
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => onInput(e.target.value)}
              className="search-input"
              placeholder="Search the web…"
              autoComplete="off"
            />
            {query && (
              <button
                type="button"
                className="clear-btn"
                aria-label="Clear"
                onClick={() => {
                  setQuery('');
                  setSugs([]);
                  inputRef.current?.focus();
                }}
              >
                <i className="bi bi-x-lg" />
              </button>
            )}
            <button type="submit" className="search-btn" aria-label="Search">
              <i className="bi bi-search" />
            </button>
          </form>

          {sugs.length > 0 && (
            <ul className="suggestions">
              {sugs.map((s) => (
                <li
                  key={s.title}
                  onMouseDown={() => {
                    setSugs([]);
                    doSearch(s.title);
                  }}
                >
                  {s.img ? (
                    <img src={s.img} className="sug-icon" alt="" />
                  ) : (
                    <i className="bi bi-search" />
                  )}
                  <span>{s.title}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </header>

      {/* tabs */}
      <nav className="result-tabs">
        {(['all', 'images', 'news', 'videos'] as const).map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? 'active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>

      {error && <p className="error">{error}</p>}

      {/* container */}
      <div className="results-container">
        {/* ------- All / Web results ------- */}
        {tab === 'all' && (
          <>
            <ul className="results">
              {web.map((r) => (
                <li key={r.url} className="result-item">
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="favicon-box"
                  >
                    <img
                      src={`https://www.google.com/s2/favicons?domain=${new URL(r.url).hostname}&sz=64`}
                      alt=""
                      className="favicon"
                    />
                  </a>
                  <div className="result-body">
                    <a href={r.url} target="_blank" rel="noreferrer">
                      {r.title}
                    </a>
                    {r.snippet && <p className="snippet">{r.snippet}</p>}
                    <span className="source-tag">
                      {r.display_link || r.source}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
            {!lWeb && web.length === 0 && (
              <p className="no-results">No results</p>
            )}
            <Pager p={webP} setP={setWebP} />

            {/* knowledge panel */}
            {(() => {
              const fallback =
                web.length && web[0].thumb
                  ? {
                      title: web[0].title,
                      description: web[0].display_link || web[0].source,
                      extract: web[0].snippet,
                      thumb: web[0].thumb,
                    }
                  : null;
              const kp = panel || fallback;
              return kp ? (
                <aside className="knowledge-panel">
                  {kp.thumb && <img src={kp.thumb} alt="" />}
                  <h3>{kp.title}</h3>
                  {kp.description && <p>{kp.description}</p>}
                  {kp.extract && <p>{kp.extract}</p>}
                </aside>
              ) : null;
            })()}
          </>
        )}

        {/* ------- News results ------- */}
        {tab === 'news' && (
          <>
            {lNews ? (
              <p className="loading">Loading…</p>
            ) : (
              <>
                <ul className="results">
                  {news.map((n) => (
                    <li key={n.url} className="news-item">
                      <div className="news-text">
                        <a href={n.url} target="_blank" rel="noreferrer">
                          {n.title}
                        </a>
                        {n.snippet && <p className="snippet">{n.snippet}</p>}
                        <span className="source-tag">
                          {n.display_link || n.source}
                        </span>
                      </div>
                      {n.thumb && (
                        <img src={n.thumb} className="news-thumb" alt="" />
                      )}
                    </li>
                  ))}
                </ul>
                {!lNews && news.length === 0 && (
                  <p className="no-results">No news found</p>
                )}
                <Pager p={newsP} setP={setNewsP} />
              </>
            )}
          </>
        )}

        {/* ------- Videos results ------- */}
        {tab === 'videos' && (
          <>
            {lVid ? (
              <p className="loading">Loading…</p>
            ) : (
              <>
                <ul className="results">
                  {videos.map((v) => (
                    <li key={v.url} className="video-item">
                      <img
                        src={v.thumb || '/placeholder.jpg'}
                        alt=""
                        className="video-thumb"
                      />
                      <div className="video-text">
                        <a href={v.url} target="_blank" rel="noreferrer">
                          {v.title}
                        </a>
                        {v.snippet && <p className="snippet">{v.snippet}</p>}
                        <span className="source-tag">
                          {v.display_link || v.source}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
                {!lVid && videos.length === 0 && (
                  <p className="no-results">No videos found</p>
                )}
                <Pager p={vidP} setP={setVidP} />
              </>
            )}
          </>
        )}

        {/* ------- Images ------- */}
        {tab === 'images' && (
          <>
            <div className="image-grid">
              {images.map((img) => (
                <a
                  key={img.url}
                  href={img.url}
                  target="_blank"
                  rel="noreferrer"
                  className={`image-card ${
                    viewImg?.url === img.url ? 'selected' : ''
                  }`}
                  onClick={(e) => {
                    e.preventDefault();
                    setViewImg(img);
                  }}
                >
                  <img
                    src={(img.thumb || img.url).replace(/^http:/, 'https:')}
                    alt={img.title}
                    onLoad={(e) => e.currentTarget.classList.add('loaded')}
                    onError={(e) => {
                      const el = e.currentTarget;
                      if (el.src !== img.url)
                        el.src = img.url.replace(/^http:/, 'https:');
                      else el.classList.add('broken');
                    }}
                  />
                </a>
              ))}
              {lImg &&
                [...Array(10)].map((_, i) => (
                  <div key={i} className="image-card skeleton" />
                ))}
            </div>

            <div ref={sentinel} style={{ height: '1px' }} />

            {!lImg && images.length === 0 && (
              <p className="no-results">No images found</p>
            )}
            {!hasMoreImg && images.length > 0 && (
              <p className="end-msg">You have reached the end of the pictures</p>
            )}

            {/* right-panel */}
            {viewImg && (
              <aside className="img-viewer">
                <div className="viewer-header">
                  <span className="viewer-source">
                    {viewImg.display_link || viewImg.source}
                  </span>
                  <button
                    className="close-btn"
                    aria-label="Close"
                    onClick={() => setViewImg(null)}
                  >
                    <i className="bi bi-x-lg" />
                  </button>
                </div>

                <img
                  src={(viewImg.thumb || viewImg.url).replace(/^http:/, 'https:')}
                  alt={viewImg.title}
                />

                <h4 className="viewer-title">{viewImg.title}</h4>

                <div className="viewer-buttons">
                  <a
                    href={viewImg.url}
                    target="_blank"
                    rel="noreferrer"
                    className="viewer-btn"
                  >
                    Visit
                  </a>
                  <a href={viewImg.thumb || viewImg.url} className="viewer-btn" download>
                    Download
                  </a>
                </div>
              </aside>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default SearchPage;