# Sprint 103: Deadline countdown — urgency, context, an action nudge, and a live clock

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (urgency + context + nudge as pure/server-side; then a live JS clock)
**Carried Over:** none

> **Direction (owner):** enhance the deadline countdown (Sprint 101, ADR-086) — the owner picked **all four**:
> a **live ticking clock**, **urgency colours + copy**, a **pre-deadline action nudge**, and **upcoming-GW
> context**.

---

### 🔎 Verified at planning (real data)

- **The banner today** (ADR-086) is a static server-rendered line: *"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) —
  in 14 days"*, on Home (`st.info`) + Squads (caption), from `next_deadline(fixtures, now)`.
- **A live client-side tick is feasible** — `streamlit.components.v1.html` exists (verified), so a JS
  `setInterval` clock ticks in the browser with **no server reruns**. (ADR-086 deferred this; we're now doing
  it — the first client-side JS in the app, so it warrants its own ADR.)
- **The states to handle**: **calm** (>24h) · **today** (<24h) · **imminent** (<2h) · in-progress (deadline
  passed — `next_deadline` already rolls to the next GW).
- **Upcoming-GW context is derivable** from the fixtures we already read — no new data. Verified: **GW1 = 10
  matches, first kick-off Fri 21 Aug 20:00 (UK)**, 1 match on the opening night.

---

### 🎯 Sprint Goal

**Objective:** turn the static line into a **real deadline experience** — a countdown that **escalates in
urgency** as it nears, shows **what's coming** (matches · first kick-off), **nudges the key pre-deadline
actions**, and (on Home) **ticks live**. All derived from data we already have; `now`-injected so the logic
stays deterministically tested.

#### Success Criteria
- [ ] **US-267 (urgency + context + action nudge; extends ADR-086)** — a pure `deadline_urgency(time_left)` →
      `calm` / `today` / `imminent`; a pure `gameweek_context(fixtures, gameweek)` → `{matches, first_kickoff}`;
      an urgency-aware `deadline_banner` (copy escalates: *in 14 days* → *deadline TODAY — in 6h* → *deadline in
      1h 40m — set your team!*) with the context line. Rendered with the matching widget (`st.info` / `warning`
      / `error`) on **Home** + **Squads**, plus a **"Before it locks → manage your team"** nudge (an
      `st.page_link` to Squads) shown when it's `today`/`imminent`.
- [ ] **US-268 (a live ticking clock, ADR-088)** — a `web_streamlit/countdown.py::render_countdown(deadline,
      now, urgency)` emitting a self-contained `components.html` block: a styled **Days : Hrs : Mins : Secs**
      clock that **ticks every second** client-side (JS `setInterval` off the embedded deadline ISO),
      urgency-coloured, with the date beneath. On **Home** (the static urgency banner stays as a no-JS
      fallback/caption). Display-only; degrades if the component can't load.
- [ ] **No drift** — display-only; the analytics/engine unchanged; existing **686** stay green; ruff clean.
- [ ] Docs: ADR-088 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 🧭 Design sketch

**US-267 (pure + server-side).** `analytics/deadline.py`: `deadline_urgency(time_left)` (thresholds
`_IMMINENT = 2h`, `_TODAY = 24h`); `gameweek_context(fixtures, gameweek)` → the match count + earliest
`kickoff_time` for that GW (reuses the parse from `next_deadline`). `ui/deadline.py::deadline_banner(gw,
deadline, now, context=None)` → an urgency-aware string (emoji + copy by level) + a context clause (*"· 10
matches · first kick-off Fri 20:00"*). The pages call `deadline_urgency(...)` to pick the widget
(`st.info`/`warning`/`error`) and, when not calm, render a nudge: `st.page_link("pages/3_Squads.py", label="⚙️
Set your captain · transfers · chips →")`. Everything `now`-injected → deterministic tests.

**US-268 (ADR-088).** `web_streamlit/countdown.py::render_countdown(deadline, now, urgency)` builds an HTML/CSS
+ `<script>` string and calls `components.html(html, height=…)`: a flip-style `NN : NN : NN : NN` grid that a
`setInterval` updates from `new Date(<deadline ISO>) - Date.now()` each second (stops at 0 → "deadline
passed"); colours keyed to `urgency`. Self-contained (its own theme), display-only. Home renders it **above**
the static urgency banner (which remains the accessible, no-JS truth).

**Deferred:** "N of *your* players play first" (a per-squad join — a later Squads nicety); notifications /
push; a clock on every page (Home is enough).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-267 | **Urgency + context + action nudge** — `deadline_urgency`/`gameweek_context`, an urgency-aware banner + nudge on Home/Squads. Extends ADR-086. | High | ⬜ To do | ~⅔ session |
| US-268 | **Live ticking clock** — a `components.html` Days:Hrs:Mins:Secs clock on Home. ADR-088. | High | ⬜ To do | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `deadline_urgency` returns calm/today/imminent at the right cut-offs; `gameweek_context`
   returns the match count + first kick-off (empty-safe); `deadline_banner` escalates its copy + includes the
   context; Home/Squads render the right widget + the nudge when urgent; the countdown component renders (the
   HTML block carries the deadline ISO + the tick script). Existing **686** stay green.
2. **Manual smoke** — Home shows a live ticking clock + the (calm) banner today; with an injected near time it
   goes 🟠 "deadline today" then 🔴 "set your team!"; the nudge links to Squads.
3. **Docs updated** — ADR-088 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-267 — urgency + context + action nudge (extends ADR-086).** ✅ Done.
- `analytics/deadline.py`: pure `deadline_urgency(time_left)` → **calm** (>24h) / **today** (<24h) /
  **imminent** (<2h, and passed) + `gameweek_context(fixtures, gameweek)` → `{matches, first_kickoff}`
  (empty-safe). Exported.
- `ui/deadline.py`: `deadline_banner` now **escalates** — *⏳ … in 14 days* → *🟠 GW1 deadline TODAY — in 6h* →
  *🔴 GW1 deadline in 1h 40m — set your team!* — with a **context clause** (*· 10 matches · first kick-off Fri
  20:00*). A shared `deadline_line(fixtures, now)` → `(text, urgency)` so Home + Squads don't duplicate.
- **Home**: the banner widget is picked by urgency (`st.info`/`warning`/`error`); when not calm, a
  **`st.page_link`** nudge — *"⚙️ Before it locks — set your captain · make transfers · pick a chip →"*.
  **Squads**: a compact urgency caption (the emoji conveys the level).
- **Tests (+4):** `deadline_urgency` thresholds; `gameweek_context` (count + first kick-off, empty-safe); the
  banner escalates (⏳/🟠/🔴 + context); `deadline_line` returns text+urgency (None when nothing's ahead).
  **690** green, ruff clean.
- **Manual smoke:** Home shows *"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 13 days, 20h · 10 matches · first
  kick-off Fri 20:00"* (calm → st.info, no nudge); injected near-times escalate to 🟠 then 🔴 with the nudge.

**US-268 — live ticking clock (ADR-088).** ✅ Done.
- `web_streamlit/countdown.py`: a pure `countdown_html(gw, deadline, now, urgency)` — a self-contained
  HTML/CSS + `setInterval` **Days : Hrs : Mins : Secs** clock, urgency-coloured (green/amber/red), cells
  **server-filled** (readable without JS) and ticked client-side off the embedded deadline ISO (stops at 0 →
  "deadline passed"); `render_countdown` embeds it via **`st.iframe`** (JS-enabled; the modern replacement for
  the deprecated `components.v1.html`). `deadline_line` now returns `(gameweek, deadline, text, urgency)`.
- **Home**: the **live clock** is the hero, with the US-267 text line as a `st.caption` (the accessible,
  no-JS fallback) + the nudge; Squads keeps the compact caption.
- **Tests (+3, 2 updated):** `_parts` (split + clamp); `countdown_html` embeds the ISO + tick + server-filled
  cells + UK subtitle; urgency colours; `deadline_line` returns the 4-tuple; the Home test reads the caption.
  **693** green, ruff clean (no deprecation warning).
- **Visual preview (Artifact):** a live, ticking preview of the three states (calm/today/imminent) — pure
  HTML/JS so it runs in the sandbox: https://claude.ai/code/artifact/ba067e4a-9a38-422d-b822-c2169baddf8b

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
