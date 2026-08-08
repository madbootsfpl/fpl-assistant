# Sprint 116: Two feedback fixes + a web-native Captain Pick card

**Dates:** 2026-08-17 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (two small fixes + a visual card — display only)
**Carried Over:** none

> **Direction:** back to the backlog (a **web-native Captain Pick card**), plus two tester-feedback checks:
> *"Hover-overs seem to have stopped working"* and *"does `reseed` call ClubElo? It used to — I don't see it
> now."*

---

### 🔎 Verified at planning (diagnosed both feedback items)

- **Tooltips — the `help=` is all still there.** The ADR-065 coverage test (`test_help_tooltips.py`) **passes**
  — every input widget carries a non-empty `help=`, and no injected `<style>` is global (the pitch CSS is
  scoped to `.fpl-pitch`). The likely cause: **Streamlit is unpinned** in `requirements.txt`, so the Community
  Cloud deploy auto-upgrades to the **latest** Streamlit while we build/test on **1.61.1** (where the tooltips
  were verified) — a newer Streamlit changing hover rendering fits "worked before, stopped now". Fix: **pin
  Streamlit** so dev == deploy.
- **ClubElo — `reseed` still calls it, but doesn't *report* it.** `reseed` → `ingest.refresh` →
  `_refresh_elo` (best-effort) — and ClubElo is reachable now (a live check returned **20** English clubs). But
  `cmd_reseed` does `…, _ = ingest.refresh(store)` — it **discards `n_elo`** and its summary omits the Elo line
  that `cmd_refresh` prints. So it *looks* gone. Fix: capture + report the Elo count (and the degrade note).
- **The Captain card already has all its data.** The web **Captain** view computes `captain_picks` +
  `explain_captain` and renders them as a **monospace `st.code` block** (US-278). A native card needs no new
  analytics — just the same pick / Team·Pos / projected xP / confidence·band / Why(✓) / Risks(⚠) / Alternatives,
  rendered as HTML/CSS like the **pitch** (`render_pitch`, ADR-084).

---

### 🎯 Sprint Goal

**Objective:** tooltips work on the deploy again and `reseed` visibly refreshes ClubElo; and the web **Captain
Pick** reads as a **styled card** (matching the mockup's look) rather than a mono block. Fixes + display only;
the analytics/grounding untouched.

#### Success Criteria
- [ ] **US-293 (two feedback fixes)** — (a) **pin Streamlit** in `requirements.txt` to the tested version
      (`==1.61.1`) so the deploy renders tooltips as dev does (the app still imports/runs); (b) **`reseed`
      reports ClubElo** — capture `n_elo` and print *"…and N Elo ratings (ClubElo)"* (or the "kept last-known"
      note on a ClubElo failure), matching `refresh`.
- [ ] **US-294 (web-native Captain Pick card)** — a self-contained, theme-aware HTML/CSS
      `web_streamlit/captain_card.py::render_captain_card(...)` — the 🥇 pick (name · **Team · Pos** · a
      **Projected xP** chip) · a **Confidence NN/100 · Band** pill · **Why** (✓) / **Risks** (⚠) · **Alternatives**
      (🥈/🥉 + xP) — rendered via `st.markdown(unsafe_allow_html=True)`, every value `html.escape`d, readable on
      both themes. Shown on the web **Captain** tab (replacing the mono block; the rich picks table stays above);
      a faithful **Artifact preview** published for owner sign-off before finalising (per the visual-sign-off
      habit). Reuses `explain_captain` + the picks — no analytics change.
- [ ] **No drift** — display/fixes only; `decision_xp`/`explain_*`/the analytics unchanged; the read-only web
      guardrail holds; existing **746** stay green (+ reseed-reporting + card-render tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log, DEPLOY (the Streamlit pin).

---

### 🧭 Design sketch

**US-293.**
- `requirements.txt`: `streamlit` → **`streamlit==1.61.1`** (a comment noting: pinned so the Community Cloud
  deploy matches the tested version — an unpinned upgrade changed tooltip rendering).
- `cli.py::cmd_reseed`: `n_players, n_teams, n_fixtures, n_elo = ingest.refresh(store)`; extend the printed
  summary with the Elo count. A test monkeypatches `ingest.refresh` + `shutil.copyfile` and asserts the message
  names the Elo ratings.

**US-294.** A new `web_streamlit/captain_card.py` (the `pitch.py` pattern): a scoped `.cap-card` `<style>` +
one HTML block, all text `html.escape`d, colours as CSS tokens that read on light + dark (like the pitch). The
web **Captain** view builds it from `captain_picks(...)[0]` + `explain_captain(...)` + a `short_name → name` map
+ the runner-ups, and renders it above/instead of the `render_captain_picks` mono block (kept as the no-CSS
fallback / for the CLI). A faithful **Artifact preview** (real pick, SVG/inline for any CDN-blocked images) goes
to the owner for approval before the code is finalised. Tests read the emitted HTML via `AppTest.markdown`.

**Deferred:** a web-native **worth** card (same pattern, a follow-up); the card on **My Squad** (the pitch's
(C) armband already flags the captain there); a CLI restyle (the mono card stays the terminal surface).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-293 | **Two feedback fixes** — pin Streamlit (tooltips) + report ClubElo in `reseed`. | High | ⬜ To do | ~¼ session |
| US-294 | **Web-native Captain Pick card** — a styled HTML/CSS card on the Captain tab (reuses `explain_captain`). | High | ⬜ To do | ~¾ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `requirements.txt` pins `streamlit==1.61.1` (and the suite still runs on it); `cmd_reseed`'s
   summary names the Elo count (a fake `refresh`/`copyfile`); `render_captain_card` emits one HTML block with
   the pick (Team·Pos·Projected), the confidence/band pill, the ✓ Why / ⚠ Risks and the 🥈/🥉 Alternatives, with
   every value escaped (a `"<script>"`-in-a-name test); the web Captain tab renders the card (AppTest markdown)
   without the mono block crashing. Existing **746** stay green. No `.save(` / no analytics change.
2. **Manual smoke** — tooltips show locally on 1.61.1; `python app.py reseed` prints the Elo count; the web
   Captain tab shows the styled card (and the Artifact preview is approved).
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log, DEPLOY.

---

### 📝 Session Progress Log

**US-293 — two feedback fixes.** ✅ Done.
- **Tooltips → pin Streamlit.** `requirements.txt`: `streamlit` → **`streamlit==1.61.1`** (with a comment) so
  the Community Cloud deploy renders on the **same version we build/test on** — an unpinned auto-upgrade is the
  likely cause of "hover-overs stopped working" (the `help=` coverage test still passes; no global CSS). The
  suite runs on 1.61.1 (installed matches the pin). _(Honest caveat: the actual hover behaviour is a
  browser/deploy concern — if the pin doesn't restore it live, it's a Streamlit-version tooltip regression to
  chase.)_
- **ClubElo → `reseed` reports it.** `cmd_reseed` now captures `n_elo` from `refresh` (it was discarded) and
  the summary reads *"…and N Elo ratings (ClubElo)"* — or *"0 Elo ratings (ClubElo kept last-known)"* when the
  best-effort fetch fails. `reseed` always **did** call ClubElo (via `refresh`→`_refresh_elo`; verified
  reachable — 20 clubs); only the print dropped the count.
- **Tests (+1, 1 extended):** the reseed test asserts *"20 Elo ratings (ClubElo)"*; a new test asserts the
  *"kept last-known"* note on a zero-Elo (ClubElo-down) refresh. **747** green, ruff clean.
- **Manual smoke:** `import streamlit` → 1.61.1; the reseed summary names the Elo count.

_(US-294 next — "start US-294".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
