# Architectural Decision Record: A local-only data refresh + a "Data as of" freshness caption

**Decision ID:** ADR-056
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Introduces the **first write path** in the Streamlit edge, as a deliberate,
narrowly-scoped exception to the read-only web posture (ADR-050/053/054/055). Reuses the CLI's `ingest.refresh`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The CLI has `refresh` (fetch FPL API + ClubElo → write the local DB cache). The owner wants the same
convenience **in the Streamlit UI**, and a visible **data-freshness** indicator. But the deployed app is
**read-only by design** (ADR-053): its DB is the committed `seed.db`, the disk is **ephemeral**, and it's
**shared across all users**. A refresh on the cloud would be pointless (lost on restart), unsafe (one
user's refresh hits everyone; server-side API calls from a public app), and — writing `seed.db` — would
re-trigger the git-sync breakage we just hit. So refresh must exist **locally** but never on the cloud.

#### Decision Drivers
- **Local convenience** (refresh from the UI, like the CLI) — the owner's ask.
- **Keep the cloud read-only** — no writes, no server-side API calls, no shared-state surprises.
- **A freshness signal everywhere** — testers should see how old the snapshot is.
- **Reuse, don't duplicate** — the CLI's `ingest.refresh` is the one refresh path.

---

### ✅ Decision

**1. A local-only "🔄 Refresh data" button.** Shown in the **sidebar** only when running **locally** — gated
by an `FPL_LOCAL=1` env var that the **`python -m src.web_streamlit` runner sets** (the cloud runs
`Home.py` directly, so the var is absent) **and** only when the DB is a real writable cache (not the seed).
It calls the CLI's `ingest.refresh` (in an `st.spinner`, `FplApiError` → a clear error), then `st.rerun`.
This is the **first web write path** — deliberately narrow: local only, the data cache only (never a squad,
never `seed.db`).

**2. A "📅 Data as of \<date\>" caption on every tab.** Always shown (both modes), in the sidebar, from the
DB file's mtime. Locally that's the last refresh; on the cloud it's the snapshot's deploy date — a
good-enough freshness signal. *(A stored refresh timestamp would be exact; deferred as a nicety — mtime
keeps this sprint simple.)*

**3. The cloud stays read-only.** With no `FPL_LOCAL`, the button never renders on the cloud — only the
caption. The existing no-server-writes guardrail (no `SquadStore.save` in the web edges) still holds;
`ingest.refresh` writes the **data cache**, not user state, and only locally.

**4. A shared `render_data_status()` helper** (`src/web_streamlit/status.py`), called at the top of every
page, so the caption (and the local button) appear consistently everywhere.

---

### 🔀 Alternatives Considered

- **Refresh on the cloud too.** Rejected: ephemeral (lost on restart), shared across users, server-side API
  calls, and writing `seed.db` breaks Cloud's git sync. Explicitly out.
- **Detect "cloud" by a Streamlit-provided flag.** There isn't a reliable one; our own `FPL_LOCAL` (set by
  the runner) is explicit and under our control.
- **A stored `refreshed_at` in the DB for an exact date.** More accurate, but needs a schema/meta table +
  re-seeding the committed DB. Deferred — file mtime is enough for a freshness caption now.
- **Button in the main area per page.** The sidebar keeps it consistent and unobtrusive across all tabs.

---

### 🧭 Consequences

**Positive**
- Refresh from the UI locally (parity with the CLI), and a freshness signal testers can see everywhere.
- The cloud stays strictly read-only — the button simply isn't there without `FPL_LOCAL`.
- Reuses `ingest.refresh` — one refresh path, no drift.

**Negative / risks (mitigations)**
- **A new write path in the web edge** → narrowly gated (local + writable non-seed DB), documented here;
  the core still imports no web edge; no `SquadStore.save` in the web.
- **`config.DB_PATH` is import-time** → a refresh that *creates* `fpl.db` where only the seed existed won't
  be read until restart; so the button is hidden on the seed (only shown when `fpl.db` already exists),
  sidestepping this. A fresh local clone refreshes once via the CLI, then the button appears.
- **mtime freshness is approximate on the cloud** (shows the deploy date) → acceptable; a stored timestamp
  is the future nicety.

---

### 📊 Validation

Local: with `FPL_LOCAL=1` and a writable `fpl.db`, the button appears and `ingest.refresh` updates the
cache; the caption shows the file date. Cloud (seed DB, no `FPL_LOCAL`): only the caption renders, no
button, no write path. Tests assert the button's presence/absence by env + DB, and the caption always
renders; the no-server-writes guardrail stays green.
