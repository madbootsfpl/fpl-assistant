# Chapter 8 — APIs

**Badges:** 📖 🧪 💻

---

## Purpose

An API (Application Programming Interface) is a way for one program to ask another
program for information. This project uses the **official FPL API** to fetch
player, team and fixture data.

---

## Why We Use It — and where it sits in the architecture

The FPL API is our **source of truth** for prices, points and fixtures. In our
layered design it is the *very first* step: the **ingestion** layer talks to it,
and nothing else does. The rest of the app never calls the API — it reads from the
local database instead. That boundary is deliberate: the network is slow, rate-
limited and sometimes down, so we keep it isolated in one place.

```
FPL API  →  FplClient (the ONLY thing that touches the network)  →  everything else
```

---

## Concepts

- **Endpoint:** a specific web address the API answers on. We use
  `/bootstrap-static/` — one payload containing all players, teams and gameweeks.
- **HTTP GET:** the request type used to *read* data (we never write to the FPL API).
- **Response:** the data sent back, as JSON (see [Chapter 9](./09_JSON.md)).
- **Status codes:** 200 = OK; 429 = "too many requests" (rate limited); 4xx/5xx = error.
- **Timeout:** how long we wait before giving up, so a hung request can't freeze the app.

---

## Examples (from this project)

Our client lives in `src/api/client.py`. The important idea is not the syntax but
the **single responsibility**: fetch raw data, return it, and turn any failure into
one clear error type.

```python
class FplClient:
    def get_bootstrap_static(self) -> dict:
        url = self.base_url + config.BOOTSTRAP_STATIC_PATH
        response = requests.get(url, timeout=self.timeout, headers={"User-Agent": ...})
        response.raise_for_status()   # turn a bad status into an error
        return response.json()        # hand back raw data — no interpreting here
```

The endpoint and timeout live in `src/config.py`, not hard-coded in the client —
so there's one obvious place to change them.

---

## Common Mistakes

- **No `User-Agent`.** The FPL API can reject requests that don't look like a
  browser. We send a simple honest one from config.
- **Hammering the API.** Fetching on every action risks a 429. We fetch once and
  cache to SQLite.
- **Letting network errors leak everywhere.** We wrap them in `FplApiError` so
  callers deal with one clear error, not a raw `requests` traceback.

---

## Best Practices

- One layer owns the network; everything else reads from storage.
- Keep endpoints/timeouts in config, not scattered through the code.
- Return raw data from the client; map/interpret it in a *later* layer.

---

## Lessons Learned

- The value of isolating the API is resilience: because ingestion is separate, the
  app still shows data when the internet is down — it just reads the last save.

---

## Related Documents

- [Architecture v0.1 §3–§5](../03_Architecture/Architecture.md)
- [Chapter 9 — JSON](./09_JSON.md) · [Chapter 10 — SQLite](./10_SQLite.md)
- Code: `src/api/client.py`, `src/config.py`
