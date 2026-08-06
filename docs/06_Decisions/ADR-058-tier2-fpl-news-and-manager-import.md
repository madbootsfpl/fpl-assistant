# Architectural Decision Record: Phase 6 Tier 2 (start) — an FPL news lens + import team by manager-ID

**Decision ID:** ADR-058
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** Opens **Phase 6 Tier 2** (external / extended signals), following the Tier-1
crowd lens (ADR-057). Reuses the degrade-gracefully external-source pattern (ClubElo, ADR-010/021) and the
session-squad model (ADR-054).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants Phase 6 to grow beyond the free Tier-1 crowd fields into *"social media news, feeds &
trends, manager input"*. That external layer is a big, risky step (third-party APIs, keys/secrets, rate
limits, ToS, reliability) — cutting against the project's *lightweight, FPL-is-truth, degrade-gracefully*
ethos. An investigation found two **free, no-key** starting points that deliver most of the value now:

- **FPL official news** — 58 players currently carry a `news` string (injuries / doubts / return dates),
  which we **already ingest** as `player.news`, plus `scout_news_link` URLs. Zero new dependencies.
- **Import your team by manager-ID** — the **public** FPL entry API (`/entry/{id}/` + the post-deadline
  `/entry/{id}/event/{gw}/picks/`) lets a user pull their real squad in — no auth, no secret.

The owner's calls: **start with FPL official news**, and **"manager input" = import my FPL team by ID**;
keyed social (Reddit/X) + pundit NLP stay deferred.

#### Verified at planning (live FPL API)
- `/entry/1/` returns `{name, summary_overall_rank, started_event, …}` **now**.
- `/entry/1/event/1/picks/` → **HTTP 404** preseason — a manager's squad is **not public until the GW1
  deadline (2026-08-21)**. So the import is **GW1-gated**.
- 58 players carry `news` today → the news lens works immediately.

#### Decision Drivers
- **Value now, no infra** — free FPL data; no secrets, no third-party services this sprint.
- **Degrade gracefully** — external/entry fetches must never crash the app (ClubElo pattern).
- **Keep xP grounded** — news + import are display/state, never inputs to `decision_xp`.
- **Keep the architecture** — the import is *another way to set the session squad*; no server writes.

---

### ✅ Decision

**1. Tier 2 opens with two free, no-key pieces.** (a) An **FPL official-news lens** — surface the ingested
`player.news` (+ `scout_news_link`) as a **News** view; (b) **import a team by manager-ID** via the public
FPL entry API. **Keyed social (Reddit/X) + pundit/YouTube NLP are deferred** to a later, gated sprint, only
if they prove worth the secrets/infra.

**2. Degrade gracefully (ClubElo pattern, ADR-021).** Any entry fetch that fails / is absent / 404s → a
clear message, never a crash. FPL remains the source of truth; the news lens shows "no current news" when
clear.

**3. The import sets the session squad — no server writes.** The public picks (`/entry/{id}/event/{gw}/
picks/`) map to a **`SquadStore`-shaped dict** (`player_ids` · `bench_ids` · `captain_id`) written to
`st.session_state["squad"]` — a third way to set the active squad alongside **build** and **upload**
(ADR-054). So Analyse / Transfer / Captain / My Squad then run on *your* team. Nothing is written
server-side (the no-`SquadStore.save` guardrail holds).

**4. Public, no auth, no secret.** We use the **public** post-deadline picks endpoint — not the auth-only
`/my-team/{id}/` (a manager's pre-deadline private team). Manager-ID + `/entry/{id}/` is public data.

**5. GW1-gated import.** Picks are 404 until the GW1 deadline. **Build now** (the api fetch + a pure
`picks → squad dict` mapper, unit-tested against a **mocked** payload; ID validated live via
`/entry/{id}/`), **degrade preseason** ("your team is available after the GW1 deadline"), **live at GW1**.

**6. Not xP.** News + import are display / session state, never inputs to `decision_xp` (a test guards it).

---

### 🔀 Alternatives Considered

- **Start with Reddit/X social.** Richer "social trends", but needs app credentials + a Cloud secret,
  rate-limited, ToS/policy-volatile (X is paid). Deferred — not worth the infra to *start*.
- **Pundit / YouTube NLP.** Heavy (YouTube API + LLM summarisation). Deferred.
- **The auth-only `/my-team/` endpoint** (pre-deadline team). Needs session auth/cookies — rejected; the
  public post-deadline picks give the team with no secret.
- **Defer the import to a GW1 sprint** (like the trends intent). Reasonable, but the mapper is unit-testable
  now against the known payload and GW1 is ~2 weeks out — so build now, degrade preseason.
- **Blend news/sentiment into xP.** Rejected (ADR-057 precedent) — keeps the prediction grounded.

---

### 🧭 Consequences

**Positive**
- Real value from **free** data: an official-news lens **now**, and importing your **real team** at GW1 —
  no secrets, no new services.
- **Architecture intact** — degrade-gracefully fetch; import is session-only (no server writes); xP grounded.
- A clean Tier-2 opener that keeps the risky keyed sources behind a future gate.

**Negative / risks (mitigations)**
- **Import GW1-gated** → build + unit-test the mapper against a mock now; validate the ID + a clear "after
  GW1" message preseason; confirm live at GW1.
- **A flaky/absent entry response** → retry/degrade (ADR-021); a bad ID / down API → a clear error.
- **News is injury/status, not "social sentiment"** → honest framing; richer social is the deferred Tier-2b.

---

### 📊 Validation

Probed live: `/entry/1/` works (name / rank / started_event); `/entry/1/event/1/picks/` is 404 preseason
(→ GW1); 58 players carry `news` now. Acceptance for the sprint: the News lens renders the flagged players
(+ the empty case); the picks→squad mapper is unit-tested (mocked payload, incl. captain/bench); ID
validation + the preseason/404 message; a test asserts `decision_xp` is unchanged; no server writes; the
existing 504 tests stay green.
