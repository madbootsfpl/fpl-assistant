# Sprint 116: Two feedback fixes + a web-native Captain Pick card

**Dates:** 2026-08-17 (planned)
**Status:** ✅ Complete (2/2 stories)
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
- [x] **US-293 (two feedback fixes)** — (a) **pin Streamlit** in `requirements.txt` to the tested version
      (`==1.61.1`) so the deploy renders tooltips as dev does (the app still imports/runs); (b) **`reseed`
      reports ClubElo** — capture `n_elo` and print *"…and N Elo ratings (ClubElo)"* (or the "kept last-known"
      note on a ClubElo failure), matching `refresh`.
- [x] **US-294 (web-native Captain Pick card)** — a self-contained, theme-aware HTML/CSS
      `web_streamlit/captain_card.py::render_captain_card(...)` — the 🥇 pick (name · **Team · Pos** · a
      **Projected xP** chip) · a **Confidence NN/100 · Band** pill · **Why** (✓) / **Risks** (⚠) · **Alternatives**
      (🥈/🥉 + xP) — rendered via `st.markdown(unsafe_allow_html=True)`, every value `html.escape`d, readable on
      both themes. Shown on the web **Captain** tab (replacing the mono block; the rich picks table stays above);
      a faithful **Artifact preview** published for owner sign-off before finalising (per the visual-sign-off
      habit). Reuses `explain_captain` + the picks — no analytics change.
- [x] **No drift** — display/fixes only; `decision_xp`/`explain_*`/the analytics unchanged; the read-only web
      guardrail holds; **751** green (746 → +5: reseed report + 4 card tests); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log, DEPLOY (the Streamlit pin).

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
| US-293 | **Two feedback fixes** — pin Streamlit (tooltips) + report ClubElo in `reseed`. | High | ✅ Done | ~¼ session |
| US-294 | **Web-native Captain Pick card** — a styled HTML/CSS card on the Captain tab (reuses `explain_captain`). | High | ✅ Done | ~¾ session |

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

**US-294 — web-native Captain Pick card.** ✅ Done (owner approved the preview).
- New `web_streamlit/captain_card.py` (the `pitch.py` pattern, ADR-084): a pure `captain_card_html(ranked,
  explanation, *, scope, team_names)` + a `render_captain_card` that `st.markdown`s it — **one self-contained
  HTML/CSS block** (no JS): the 🥇 pick (**Team · Pos** + a **Projected-xP chip**) · a **Confidence·Band pill**
  (green High / amber Medium / red Low) · **Why** (✓) / **Risks** (⚠) in two columns · **Alternatives** (🥈/🥉 +
  xP). Scoped `.cap-card` CSS with **theme-neutral** rgba-grey neutrals (text inherits the theme; chips carry
  their own colour); **every value `html.escape`d**; empty-safe.
- The web **Captain** tab renders the card in place of the mono `st.code` block (the rich picks table stays
  above; `render_captain_picks` stays the CLI/terminal surface). Reuses `explain_captain` + the picks — no
  analytics change; no server writes.
- **Sign-off:** published a faithful **Artifact preview** (real pick, both Streamlit themes) → owner approved.
- **Tests (+4, 1 updated):** the card shows pick/Team·Pos/projected/confidence/Why/Risks/Alternatives; the band
  drives the pill class; a `<script>`-in-a-name is escaped; empty-safe (no picks → ""); the web Captain render
  test now checks the card markdown (`cap-card` + 🥇). **751** green, ruff clean.
- **Manual smoke:** the web Captain tab shows the styled card reading correctly on light + dark.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **746 → 751** (+5: the reseed "kept last-known" case
+ 4 card tests). Ruff clean; CI-parity green. **No new ADR** (US-293 fixes; US-294 extends ADR-084 pitch-style
HTML + ADR-089). No analytics change.

**Delivered**
- **US-293 — two feedback fixes.** Pinned `streamlit==1.61.1` (deploy == tested version → the likely tooltip
  fix) + `reseed` now reports the ClubElo count (it always called ClubElo; only the print dropped it).
- **US-294 — web-native Captain Pick card.** A styled, theme-neutral, escaped HTML/CSS card on the web Captain
  tab (owner approved the preview).

**What went well**
- **Diagnosed both feedback items to a precise cause.** The tooltip `help=` test passing + the scoped pitch CSS
  ruled out a code regression → the unpinned dependency was the real suspect; and `reseed` *did* call ClubElo,
  only the printout dropped the count (a one-word `_`). Naming the cause made each fix small.
- **The card reused the pitch pattern wholesale.** Scoped `.cap-card` CSS, `html.escape` everything, one
  `st.markdown` block, theme-neutral colours — no new approach, and the picks table + `explain_captain` were
  already there, so it was pure presentation.
- **The preview closed the loop.** A faithful Artifact (real pick, both themes) got sign-off before the code
  was final — the visual-sign-off habit paid off again.
- **Testable HTML.** Splitting a pure `captain_card_html` from `render_captain_card` let the tokens/escaping/
  band/empty-safety be unit-tested with no Streamlit context.

**Watch-outs / follow-ups**
- **The tooltip fix is a hypothesis.** Pinning restores dev == deploy and is good practice, but the actual
  hover behaviour is browser/deploy-side — needs a live check; if it persists, it's a Streamlit-version tooltip
  regression to chase.
- **A pinned Streamlit needs occasional bumping** — deliberate upgrades (test, then re-pin) instead of silent
  drift.
- **Deferred:** a matching web-native **worth** card (same pattern); a confidence *bar/gauge* instead of the
  pill if wanted.

See `Sprint116_Lessons_Learnt.md` for the detailed retro.
