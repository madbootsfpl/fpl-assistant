# Architectural Decision Record: A live client-side countdown clock (components.html)

**Decision ID:** ADR-088
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** revisits ADR-086's deferral ("no live tick — the banner recomputes each
interaction"). Adds the **first client-side JavaScript** to the app, via `st.components.v1.html`. Display-only.
Triggered by the owner's deadline-countdown enhancements.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The deadline banner (ADR-086) is a **static** server-rendered line — it only updates when the page reruns. The
owner asked for a **live ticking clock** (Days : Hrs : Mins : Secs counting down). Streamlit re-runs the whole
script server-side, so a per-second `st.rerun` would be wasteful; a real live tick needs **client-side JS**.

**Verified:** `streamlit.components.v1.html` exists — it renders arbitrary HTML/CSS/JS in a sandboxed
**iframe**, so a `setInterval` can tick in the browser with **no server reruns**. This is the first JS in the
app (everything else is pure Python + Streamlit widgets).

#### Decision Drivers
- **A real live tick** — the clock must move every second without hammering the server.
- **Self-contained + safe** — one HTML/JS block, no external scripts, no user input; the values it embeds are
  our own (a deadline ISO, a gameweek number).
- **Degrade gracefully** — if the component can't load, the countdown must still be readable.
- **Display-only** — no logic, no writes; the analytics/engine untouched.

---

### ✅ Decision

**A `web_streamlit/countdown.py::render_countdown(gameweek, deadline, now, urgency)`** that builds one
self-contained HTML/CSS + `<script>` string and renders it with `components.html(...)`:
- a styled **Days : Hrs : Mins : Secs** grid, **urgency-coloured** (calm = green · today = amber · imminent =
  red), with a *"GW1 deadline · Fri 21 Aug, 18:30 (UK)"* subtitle;
- the cells are **filled server-side** with the initial remaining time (so it's meaningful even if JS is
  blocked), and a `setInterval` recomputes from the embedded **deadline ISO** each second, stopping at 0
  (*"deadline passed"*);
- self-contained styling (an iframe has no Streamlit theme) chosen to read on both light + dark app themes; no
  external requests, no user input.

**On Home**, the clock is the hero, **above** the existing text line (the ADR-086/US-267 banner text, kept as
the accessible, no-JS-needed truth) + the pre-deadline nudge. **Squads** keeps just the compact text caption
(the clock lives on Home). `deadline_line` is extended to return `(gameweek, deadline, text, urgency)` so the
page has what both the clock and the text need from one call.

---

### 🔀 Alternatives Considered

- **`st.rerun` on a timer / `streamlit-autorefresh`.** Rejected — a full server rerun every second is wasteful
  and adds a dependency; the tick is a pure client-side concern.
- **Keep it static (ADR-086).** Rejected here — the owner explicitly wants the live tick; the static text
  remains as the fallback beneath.
- **A canvas/animation library.** Rejected — overkill; a few `<span>`s + `setInterval` is enough.

---

### 🧭 Consequences

**Positive**
- A real, moving countdown with **no server load** (the browser ticks it); urgency-coloured, self-contained.
- The static text line stays as the accessible fallback → the countdown is readable even if the iframe/JS is
  blocked.
- Display-only, no dependency, no engine change.

**Negative / risks (mitigations)**
- **First JS in the app** → kept to one self-contained block, no external scripts, no user input (only our own
  ISO/int embedded), so there's no injection surface; it can't touch app logic.
- **Iframe styling ≠ the Streamlit theme** → the clock is a deliberately self-styled card that reads on both
  themes; it's a *visual* element, not a control.
- **Testability** → AppTest doesn't execute the iframe JS, so the test asserts the emitted **HTML block**
  carries the deadline ISO + the tick script + the server-filled initial values.

---

### 📊 Validation

Verified: `components.html` exists and renders an HTML/JS iframe. Acceptance: `render_countdown` emits a block
containing the deadline ISO, the four `Days/Hrs/Mins/Secs` cells filled with the initial remaining time, and a
`setInterval` tick; Home shows the clock above the text line + the nudge; the static banner remains the no-JS
fallback; the analytics + existing **690** tests are unchanged (new tests added); ruff clean.
