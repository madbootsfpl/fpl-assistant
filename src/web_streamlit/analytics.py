"""Beta usage & experience analytics — an opt-in, anonymous, **fail-silent** client (ADR-100).

Records small **usage** + **performance** events to a Supabase `events` table so the owner can see what testers
use, whether they return, and whether the app feels fast/reliable — **without ever affecting the app**.

The #1 rule: analytics can never block, slow, or crash a rerun. So every `track()`:
  - is an **immediate no-op** when analytics is off (the default) — no thread, no write;
  - otherwise builds a small **anonymised** payload on the main thread and posts it **fire-and-forget** on a daemon
    thread with a tight timeout, the whole post wrapped so **no error can ever surface**.
A lost event never matters; a broken FPL experience would. Correctness of the app always wins.

**Off by default:** writes only when **`FPL_ANALYTICS`** is truthy **and** the Supabase store is configured
(`FPL_STORE_URL`/`FPL_STORE_KEY`, reused — the `events` endpoint is *derived*, no new secret). This is the **third**
opt-in, secret-gated server write (after the squad save ADR-094 + registration ADR-098); a guardrail test pins that
no secrets → no write, no thread, the suite byte-identical.

**Anonymous + minimal:** a random per-session id + a random returning-user id (`fpl_anon` cookie, US-333) — **no
names/emails/IPs, not the squad handle, no full squad, no click/mouse/screen tracking, no third-party service.**
`meta` is small structured context only.
"""

import threading
import time
import uuid
from collections import Counter
from datetime import datetime, timezone

import requests
import streamlit as st

from src import config
from src.web_streamlit.access import secret

_TIMEOUT = 3
_SESSION = "_analytics_session"   # session: a random per-session id
_ANON = "_analytics_anon"         # session: the resolved returning-user id (cached once known)
_ANON_SETTLED = "_analytics_anon_settled"   # session: we've given the fpl_anon cookie one run to load
_ANON_COOKIE = "fpl_anon"         # a first-party, anonymous, long-lived returning-user id (US-333)
_ANON_DAYS = 365
_STARTED = "_analytics_started"   # session: session_started already emitted this session
_TRUTHY = {"1", "true", "yes", "on"}


def boot(page: str) -> None:
    """Call once per page render (right after `require_access`): emit `session_started` **once per session**, then a
    `page_viewed`. Resolving the returning-user id here primes the `fpl_anon` cookie early. Best-effort — a hard
    no-op when analytics is off, and it can **never** raise into the page."""
    try:
        if not is_enabled():
            return
        anon_id()                                   # prime the returning-user cookie resolution
        if not st.session_state.get(_STARTED):
            st.session_state[_STARTED] = True
            track("session_started", page=page)
        track("page_viewed", page=page)
    except Exception:
        return


def is_enabled() -> bool:
    """True only when analytics is **deliberately** turned on (`FPL_ANALYTICS` truthy) **and** the store is
    configured — otherwise every call below is a hard no-op (off by default)."""
    flag = (secret("FPL_ANALYTICS") or "").strip().lower()
    if flag not in _TRUTHY:
        return False
    from src.web_streamlit import cloud_store  # lazy: reuse the store's own configured check
    return cloud_store.is_configured()


def _events_endpoint():
    """`(url, key)` for the `events` table — derived from `FPL_STORE_URL`'s base (same project as squads), reusing
    `FPL_STORE_KEY`; `(None, None)` when unset. No new secret."""
    url = secret("FPL_STORE_URL")
    key = secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/events  (sibling of squads / beta_users)
    return f"{base}/events", key


def session_id() -> str:
    """A random per-session id (a `uuid4` in session state) — distinguishes sessions; no PII."""
    sid = st.session_state.get(_SESSION)
    if not sid:
        sid = uuid.uuid4().hex
        st.session_state[_SESSION] = sid
    return sid


def anon_id():
    """The returning-user id — a random `fpl_anon` cookie (US-333), or `None` until it's resolved. No PII.

    Resolution (best-effort, never raises): the session cache → the existing `fpl_anon` cookie (a *returning*
    device) → **mint** a new `uuid4` and write it, but **only once the cookie component has settled** (so a
    still-loading first run doesn't overwrite a returning id and inflate unique-users). Anonymous and independent
    of the squad handle and the `fpl_beta` gate cookie. When unresolved, events still carry `session_id`."""
    cached = st.session_state.get(_ANON)
    if cached:
        return cached
    try:
        from src.web_streamlit import remember
        existing = remember.read_cookie(_ANON_COOKIE)
        if existing:                              # a returning device
            st.session_state[_ANON] = existing
            return existing
        if _cookie_settled():                     # no cookie AND the component has had its run → mint
            minted = uuid.uuid4().hex
            remember.write_cookie(_ANON_COOKIE, minted, days=_ANON_DAYS)
            st.session_state[_ANON] = minted
            return minted
    except Exception:
        return None
    return None                                   # still loading → defer; events carry session_id only for now


def _cookie_settled() -> bool:
    """Has the `fpl_anon` cookie component had one run to deliver its value? One-shot per session, and only when a
    component is actually present — so we don't mint a fresh id (overwriting a returning one) on the first
    'loading' run, and we never wait forever when there's no component (mint session-only instead)."""
    from src.web_streamlit import remember
    if st.session_state.get(_ANON_SETTLED):
        return True
    if not remember.available():                  # no component → nothing will ever load; safe to mint now
        return True
    st.session_state[_ANON_SETTLED] = True        # give it this run to load; trust the read next run
    return False


def track(event: str, *, page=None, duration_ms=None, ok=True, **meta) -> None:
    """Record an analytics `event` — fire-and-forget, best-effort, and **never affects the app**.

    A no-op (no thread, no write) when analytics is off. Otherwise the anonymised payload is built here (on the
    main thread, so session state is safe to read) and POSTed on a daemon thread; everything is wrapped so no error
    can reach the caller. `meta` is small structured context only — never names/emails/IPs or a full squad (ADR-100).
    """
    try:
        if not is_enabled():
            return
        url, key = _events_endpoint()
        if not url:
            return
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id(),
            "anon_id": anon_id(),
            "version": config.APP_VERSION,
            "event": event,
            "page": page,
            "duration_ms": duration_ms,
            "ok": ok,
            "meta": meta or None,
        }
        threading.Thread(target=_post, args=(url, key, payload), daemon=True).start()
    except Exception:
        return          # analytics must never raise into the app


def _post(url: str, key: str, payload: dict) -> None:
    """Best-effort POST of one event (no Streamlit APIs here — runs on a daemon thread). Swallows everything."""
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Content-Type": "application/json", "Prefer": "return=minimal"}
    try:
        requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
    except Exception:
        return


def recent_events(limit: int = 2000):
    """Read the most recent events (the **first analytics READ**, US-337 — for the admin view only). Best-effort:
    a list of row dicts, or ``None`` on failure. Needs an **anon SELECT policy** on `events` (docs/ANALYTICS.md);
    the anon key is server-side (Streamlit secrets), never sent to a browser, and events are anonymous."""
    url, key = _events_endpoint()
    if not url:
        return None
    try:
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        resp = requests.get(f"{url}?select=*&order=ts.desc&limit={int(limit)}", headers=headers, timeout=6)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _percentile(sorted_vals, pct):
    """A linear-interpolation percentile of an already-sorted list (empty → None). Pure."""
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return round(sorted_vals[lo] * (1 - (k - lo)) + sorted_vals[hi] * (k - lo))


def summarise(rows):
    """Aggregate event rows into headline stats — **pure** (no I/O), so it's unit-tested directly. All anonymous:
    session/device counts, returning devices (seen on 2+ distinct days), top pages, event counts, a success rate,
    and median/P95 duration per timed op."""
    rows = rows or []
    sessions = {r.get("session_id") for r in rows if r.get("session_id")}
    devices = {r.get("anon_id") for r in rows if r.get("anon_id")}
    days_by_device = {}
    for r in rows:
        anon, ts = r.get("anon_id"), r.get("ts")
        if anon and ts:
            days_by_device.setdefault(anon, set()).add(ts[:10])      # the date part of the ISO timestamp
    returning = sum(1 for days in days_by_device.values() if len(days) >= 2)

    event_counts = Counter(r.get("event") for r in rows if r.get("event"))
    page_counts = Counter(r.get("page") for r in rows
                          if r.get("event") == "page_viewed" and r.get("page"))
    oks = [r.get("ok") for r in rows if isinstance(r.get("ok"), bool)]
    success_pct = round(100 * sum(oks) / len(oks)) if oks else None

    durations = {}
    for r in rows:
        if r.get("event") == "perf" and isinstance(r.get("duration_ms"), (int, float)):
            op = (r.get("meta") or {}).get("op") or "?"
            durations.setdefault(op, []).append(r["duration_ms"])
    perf = []
    for op, ds in sorted(durations.items()):
        ds.sort()
        perf.append({"op": op, "n": len(ds), "p50_ms": _percentile(ds, 50), "p95_ms": _percentile(ds, 95)})

    tss = [r["ts"] for r in rows if r.get("ts")]
    return {
        "events": len(rows),
        "sessions": len(sessions),
        "devices": len(devices),
        "returning": returning,
        "top_pages": [{"page": p, "views": n} for p, n in page_counts.most_common(10)],
        "event_counts": [{"event": e, "count": n} for e, n in event_counts.most_common()],
        "success_pct": success_pct,
        "perf": perf,
        "since": min(tss) if tss else None,
        "until": max(tss) if tss else None,
    }


# --- Load & concurrency (ADR-120) ------------------------------------------------------
#
# Registered ≠ concurrent. Total testers is cheap (Supabase rows); the real limit is how many people are active
# *at once* on one small Community-Cloud container running a decision_xp compute per interaction. The failure
# mode is sluggishness and cold starts, not a crash — most likely at a deadline spike.
#
# These thresholds are HEURISTIC and deliberately uncalibrated: ADR-120 says to tune them against real load,
# the same ethos as the weight calibration. They exist so "are we near the edge?" has an answer at a glance,
# not because the numbers are known to be right.
ACTIVE_WINDOW_MIN = 10       # a session with an event this recently counts as "active now"
CONCURRENT_AMBER, CONCURRENT_RED = 5, 10
P95_AMBER_MS, P95_RED_MS = 2500, 5000


def load_summary(rows, now=None, *, window_min: int = ACTIVE_WINDOW_MIN) -> dict:
    """Concurrency and latency from the same anonymous events — **pure**, so it's unit-tested directly.

    `active_now` counts distinct sessions seen in the last `window_min`; `peak_concurrent` is the busiest such
    window over the data. Both are **proxies**: an event is a click, not a held connection, so a reader who has
    the page open but idle is invisible. Directional, and the trend beside P95 is the signal — a P95 climbing
    while concurrency climbs is contention, which is the thing worth catching before testers report it.
    """
    from datetime import datetime, timedelta, timezone

    def _ts(r):
        raw = r.get("ts")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    stamped = [(t, r.get("session_id")) for r in (rows or []) if (t := _ts(r)) and r.get("session_id")]
    now = now or (max(t for t, _ in stamped) if stamped else datetime.now(timezone.utc))
    window = timedelta(minutes=window_min)

    active_now = len({sid for t, sid in stamped if now - t <= window})
    # Peak: for each event's timestamp, how many distinct sessions were live in the window ending there.
    span = window.total_seconds()
    peak = 0
    for anchor_t, _ in stamped:
        live = {sid for t, sid in stamped if 0 <= (anchor_t - t).total_seconds() <= span}
        peak = max(peak, len(live))

    p95 = None
    for op in ("analysis", "data_load"):
        ds = sorted(r["duration_ms"] for r in (rows or [])
                    if r.get("event") == "perf" and (r.get("meta") or {}).get("op") == op
                    and isinstance(r.get("duration_ms"), (int, float)))
        if ds:
            p95 = max(p95 or 0, _percentile(ds, 95))

    health = "green"
    if peak >= CONCURRENT_RED or (p95 or 0) >= P95_RED_MS:
        health = "red"
    elif peak >= CONCURRENT_AMBER or (p95 or 0) >= P95_AMBER_MS:
        health = "amber"
    return {"active_now": active_now, "peak_concurrent": peak, "p95_ms": p95,
            "health": health, "window_min": window_min}


class timed:
    """Time a user-visible operation and emit a `perf` event (duration + ok) — best-effort (ADR-100).

    `with analytics.timed("data_load", page="Squads"): …` → a `perf` event on exit. A failure inside sets
    `ok=False` and is **re-raised** (timing never suppresses the real error). Zero cost beyond a clock read when
    analytics is off (the `track` inside no-ops)."""

    def __init__(self, op: str, page=None):
        self.op = op
        self.page = page
        self._t0 = None

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        duration_ms = int((time.perf_counter() - self._t0) * 1000)
        track("perf", page=self.page, duration_ms=duration_ms, ok=exc_type is None, op=self.op)
        return False    # never suppress the real exception
