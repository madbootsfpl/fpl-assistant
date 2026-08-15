"""Ask Maddie video store (ADR-112) — the explainer clips fronted by the mascot (Maddie).

A `maddie_videos(topic, blurb, youtube_url, sort_order, published, …)` table in the **same Supabase project** as
the squads / `beta_users` — endpoint derived from `FPL_STORE_URL`'s base, reusing `FPL_STORE_KEY` (**no new
secret**). The owner curates rows from the **Supabase dashboard**, so videos can be added / hidden / reordered /
swapped **without a redeploy** — the app only **reads** (RLS stays on with a public-read policy; no write path).

**Best-effort + fail-soft:** `videos()` never raises — an unreachable/unconfigured store (or a table with no
published rows yet) falls back to a small built-in welcome so the hub always renders. The page wraps `videos()`
in `st.cache_data` (a ~10-min TTL), so dashboard edits appear within the window — or instantly on **Reboot app**.
"""

import requests

from src.api.retry import with_retry
from src.web_streamlit.access import secret

_TIMEOUT = 6

# Shown when the store isn't configured, is unreachable, or has no published videos yet — so the hub is never
# blank. No hard-coded YouTube URL (those live in the dashboard, not the code): a friendly "coming soon" welcome.
_FALLBACK = [{
    "topic": "Meet Maddie",
    "blurb": "Your MADBOOTS guide. Short video explainers are on the way — check back soon.",
    "youtube_url": None,
}]


def _endpoint():
    """`(url, key)` for the `maddie_videos` table — derived from `FPL_STORE_URL`'s base (same project as squads),
    or `(None, None)` when the store isn't configured."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/squads -> .../rest/v1
    return f"{base}/maddie_videos", key


def is_configured() -> bool:
    """True when the (shared) Supabase store is configured, so the hub can read `maddie_videos`."""
    url, key = _endpoint()
    return bool(url and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _clean(row: dict) -> dict:
    """A display-ready `{topic, blurb, youtube_url}` — trimmed strings; a blank/absent URL becomes `None` so the
    page can render a "coming soon" caption instead of an empty player."""
    return {
        "topic": (row.get("topic") or "").strip(),
        "blurb": (row.get("blurb") or "").strip(),
        "youtube_url": ((row.get("youtube_url") or "").strip() or None),
    }


def videos() -> list[dict]:
    """The **published** videos, ordered by `sort_order`, as `[{topic, blurb, youtube_url}, …]`. **Read-only,
    best-effort:** returns the built-in fallback when the store is unconfigured/unreachable or has no published
    rows — it never raises, so the hub always renders."""
    url, key = _endpoint()
    if not (url and key):
        return list(_FALLBACK)

    def _get():
        r = requests.get(url, params={"select": "topic,blurb,youtube_url,sort_order",
                                      "published": "eq.true", "order": "sort_order"},
                         headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        rows = with_retry(_get, retries=1).json()
    except Exception:
        return list(_FALLBACK)

    rows = sorted((r for r in rows if isinstance(r, dict)),
                  key=lambda r: r["sort_order"] if isinstance(r.get("sort_order"), int) else 0)
    cleaned = [_clean(r) for r in rows if (r.get("topic") or "").strip()]
    return cleaned or list(_FALLBACK)
