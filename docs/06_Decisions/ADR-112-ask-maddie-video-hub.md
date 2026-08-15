# Architectural Decision Record: Ask Maddie — a Supabase-backed video hub

**Decision ID:** ADR-112
**Date:** 2026-08-15
**Status:** Accepted
**Superseded By / Replaces:** New feature. Complements **ADR-111** (the text Help guide) and the marketing
video series (`docs/08_Marketing/Video_Scripts.md`). **Not** a change to `ask`/`chat` (ADR-04x, the grounded
LLM) — this is scripted video content, no LLM. Reuses the Supabase store pattern (ADR-100/106).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner has named the MADBOOTS mascot **Maddie** and is producing a series of **60-second explainer videos**
(one per topic — captains, Boot Battle, differentials, build-a-squad, AI-Tips, Ask; see
`docs/08_Marketing/Video_Scripts.md`). He made the first with HeyGen (2026-08-15) and wants an **"Ask Maddie"**
home for them **inside the app** — a place new users can learn each feature from Maddie herself.

Two constraints shape the design:

- **"Ask Maddie" must not become a live chatbot.** The deployed cloud app is **data-only** (owner decision:
  the `ask`/`chat` LLM runs on local Ollama, absent from Streamlit Cloud). More importantly, a free-chat AI
  *persona* is exactly what the brand positions **against** — *"most FPL AI just guesses; MADBOOTS shows its
  working."* So "Ask Maddie" is a **grounded, scripted FAQ-by-video**, not a conversational agent.
- **The owner must be able to add / remove / refresh videos over time without a redeploy.** A hard-coded list
  in a Python module (`VIDEOS = [...]`) would need an edit + commit + Streamlit redeploy per change — that *is*
  rebuilding the app, which the owner explicitly wants to avoid.

#### Decision Drivers
- **On-brand & honest** — scripted, controlled content; no "AI that guesses", no over-promise of a chatbot.
- **Dashboard-managed, no redeploy** — the owner curates videos from the Supabase dashboard; the app reads them
  live. Add a row → it appears; `published=false` → it hides; new URL → it swaps.
- **Reuse existing infra** — Supabase already backs beta users, the waitlist and per-user squads (ADR-100/106);
  a videos table is the same pattern, no new dependency.
- **Read-only from the app** — the app only *reads*; the owner *writes* via the dashboard. This sidesteps the
  RLS-upsert pain hit with the waitlist (insert+update policies) — a public **read** policy is all that's needed.
- **Resilient & lightweight** — best-effort like the news feeds: if Supabase is unreachable the page still works
  from a tiny built-in fallback; no heavy mp4s in the repo.
- **Ships now, grows later** — launches with the one existing video and grows as clips are recorded.

---

### ✅ Decision

**1. Content lives in a Supabase table `maddie_videos`** — columns: `topic` (text), `blurb` (text),
`youtube_url` (text), `sort_order` (int), `published` (bool). The owner manages rows entirely from the
**Supabase dashboard**. **Public read policy only** (anon/publishable key, like the other reads); **no app write
path** — writes are dashboard-only. Videos are hosted on **YouTube (unlisted)** and embedded via `st.video(url)`
(the `app.heygen.com` player is auth-gated and not embeddable; unlisted YouTube keeps mp4s out of the repo and
respects Streamlit Cloud size limits, and doubles as the public marketing channel).

**2. The app reads the table live, cached + best-effort.** A `maddie.py` helper fetches published rows ordered by
`sort_order`, wrapped in `@st.cache_data(ttl≈10 min)` so edits appear automatically within the TTL — or
**instantly via "Reboot app"** (the same refresh trick used for the DB snapshot). On any fetch error it returns a
**tiny built-in fallback list** (the current video) so the page never breaks — same best-effort resilience as the
media feeds (ADR-093).

**3. A new page `pages/…_Ask_Maddie.py`** — the hub: a short "Meet Maddie" intro line + one entry per published
video (`topic` heading · `blurb` · embedded clip). Entries without a URL render a subtle **"coming soon"** rather
than a broken player, so the page reads well while the series is still being filmed.

**4. A compact teaser on Home** — a small **"🎥 New here? Ask Maddie"** card linking to the page, sitting with the
existing New-here / Testing nudges. Cross-linked with the text **Help** tab (they complement, not duplicate).

**5. What this is *not*.** Not a live chatbot and not the `ask`/`chat` feature (no LLM, no cloud model). Not a
repo of committed mp4s. Not an app-side write path (dashboard-managed). Not an analytics/engine change. The
in-app Admin editor (below) is explicitly **out of scope** for this sprint.

---

### 🔀 Alternatives Considered

- **Hard-coded `VIDEOS` list in a Python module.** Rejected — simplest to build, but every add/remove needs a
  commit + redeploy, failing the owner's "refresh without rebuilding" requirement.
- **A JSON/YAML file committed to the repo.** Rejected for the same reason — still a commit + redeploy per change.
- **Rename `ask`/`chat` to "Ask Maddie" (a live assistant).** Rejected for now — the cloud app has no LLM
  (data-only), and a chat persona risks the "AI that guesses" read the brand fights. Revisit only if a *grounded*
  cloud answer path (with visible ✓/⚠ working) ever lands.
- **Commit mp4s to `assets/`.** Rejected — repo bloat + Streamlit Cloud size limits; unlisted YouTube is free,
  reliable, embeddable, and also the marketing channel.
- **In-app Admin editor now** (`pages/10_Admin.py` writes the table). Deferred — the Supabase dashboard already
  meets the requirement; an app-side write path reintroduces the RLS-write complexity. A clean **follow-up**.

---

### 🧭 Consequences

**Positive**
- The owner **curates videos live from the dashboard** — add / hide / reorder / swap, **no redeploy**.
- **On-brand**: scripted, grounded content fronted by Maddie; no chatbot over-promise.
- **Reuses** the Supabase pattern; **read-only** avoids the waitlist RLS-write headache; **fallback** keeps it safe.
- Ships **now** with one video and grows painlessly; no repo bloat, no new dependency.

**Negative / risks (mitigations)**
- **"Dynamic" = within the cache TTL**, not instant. *Mitigation:* ~10-min TTL + the documented "Reboot app" for
  an immediate refresh; note it in the runbook/Help.
- **Depends on Supabase reachability.** *Mitigation:* best-effort fetch + built-in fallback list; the page never
  breaks.
- **YouTube dependency / unlisted links can be shared.** *Mitigation:* unlisted is fine for public marketing
  content; nothing sensitive. A blocked embed degrades to the fallback/coming-soon.
- **One more table to seed.** *Mitigation:* one-time `create table` + a public-read policy + one seed row; SQL in
  the sprint plan, same shape as the waitlist setup.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**Sprint 157**): **US-382** the `maddie.py` reader (Supabase read, cached, fallback) + the
  `pages/…_Ask_Maddie.py` hub; **US-383** the Home teaser. DoD: pytest (page renders; only published rows show;
  fallback on fetch error; Home teaser links) · manual smoke · docs (this ADR + Journal + Roadmap + the Supabase
  setup SQL in the runbook). No new dependency.
- **Not this ADR / follow-ups:** the in-app **Admin** video editor (write path); a live "Ask Maddie" assistant
  (only if a grounded cloud LLM path lands); per-video view analytics.
