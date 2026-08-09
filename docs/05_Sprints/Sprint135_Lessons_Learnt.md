# Lessons Learned

**Sprint:** Sprint 135 — Confirm on Log out + surface ☁ Save/Load in the Squads sidebar

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two small UI wins now that remember-me is verified: (1) a **confirm before "Log out"** so a mis-click can't reset a
device; (2) surface the **☁ Save / Load across devices** in the **Squads sidebar** so it's visible on every
sub-view, not buried under My Squad. Both off by default; no analytics change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Right-size the change** — a confirm is a gate in front of existing `logout()`; the ☁ move is a widget relocation.
- **Match a control's data to where it renders** — the sidebar saves the *active* squad, not a view-local pick.

### New Skills Acquired

- **A `st.dialog` needs its body re-called each run to stay interactive.** Calling the decorated function opens the
  modal, but the *next* run (clicking a button inside it) doesn't re-open it unless something re-calls the function
  — and AppTest doesn't auto-persist an open dialog. A `_beta_confirming` **session flag** (opener sets it,
  `_render_account` re-calls the dialog while set, each choice pops it) fixes both the AppTest flow and the browser.
- **A relocated widget must *move*, not duplicate.** The ☁ block uses fixed keys (`cloud_handle`/`cloud_save`/…);
  rendering it in both the sidebar and My Squad would be a duplicate-key crash. So it moves; a one-line pointer
  caption covers anyone who looked for it in the old place.
- **The sidebar renders before the sub-view runs.** `render_sidebar()` is called at page top, before the segmented
  control picks a view — so a sidebar control can only see the session state as it was at the *start* of the run.
  The ☁ Save reflects a just-built squad on the *next* rerun (Streamlit's normal cycle) — fine, but a real ordering
  constraint to remember when hoisting UI into the sidebar.
- **`squad_picker` returns a squad without making it active.** Picking a *demo* is display-only; only build / upload
  / import / load / an edit calls `set_active_squad`. So gating the sidebar Save on `active_squad()` is correct —
  you save *your* squad, not the read-only demo — and it's why Save is disabled until you have one.

---

# What Went Well ✅

- **Both right-sized** — no new ADR, no dependency, no analytics; a confirm gate + a widget relocation.
- **Dialog gotcha caught in the test** — the `_beta_confirming` flag fixed the cross-rerun interactivity.
- **Honest semantics** — the sidebar Saves the active squad; Save disabled without one; ADR-094 write posture intact.
- **Clean move** — moved not duplicated (keys), a pointer caption left behind. 864 → 867; ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The confirm's "Log out" did nothing | `st.dialog` body wasn't re-called on the next run (opener not re-clicked) | A `_beta_confirming` flag re-calls the dialog until a choice is made |
| Where should the ☁ block live? | it needs the active squad + `cloud_store`, both session/global | `squads.render_cloud_sync()` in `render_sidebar()` (Squads-tab-scoped) |
| Save with only a demo picked | `squad_picker` doesn't make a demo active | Gate Save on `active_squad()` (disabled + a hint until you have one) |
| Duplicate widget keys | can't render the same block in two places | Move it (sidebar) + a pointer caption in My Squad |
| Tests targeted My Squad | the block moved | Re-point to the sidebar + seed an active squad; add a disabled-Save test |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| `st.dialog` lifecycle | Re-call the decorated function each run (a session flag) to keep the modal interactive |
| Sidebar render order | The sidebar renders before the sub-view — it sees start-of-run session state |
| Active vs picked squad | `squad_picker` ≠ `set_active_squad`; gate a global Save on the active squad |
| Move vs duplicate | Fixed widget keys mean a widget can only render once — relocate, don't copy |

---

# Development Lessons 💻

- For a modal that must survive interaction, drive it from a session flag, not just the opener's click.
- When hoisting a control into the sidebar, feed it session/global state — it can't see a sub-view's local pick.
- Relocating a keyed widget is a move; leave a pointer where it used to be so nobody loses it.

---

# AI Collaboration Lessons 🤖

- Both changes stay outside the grounded/read-only analytics core: the confirm is session UI over `logout()`, and
  the ☁ relocation reuses the existing opt-in, secret-gated squad-save (ADR-094) — no new server write, no analytics
  touched. The read-only invariant's two exceptions are unchanged.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-329 extends **ADR-099** (logout family): a `@st.dialog` confirm in front of `logout()`, kept open
across reruns by a `_beta_confirming` flag. US-331 extends **ADR-094**: the ☁ cross-device Save/Load relocated from
the My Squad body to `squads.render_cloud_sync()` in the Squads sidebar (Saves the active squad, secret-gated,
moved-not-duplicated). Docs: Sprint doc + Lessons, CLOUD_SQUADS.md, Help, PROJECT_STATUS, Architecture._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (light smoke):** on the Squads tab, the ☁ Save/Load shows in the sidebar on every sub-view; build/upload a
  squad → Save enables → Load on another device. Log out → confirm/Cancel behave.
- **Deferred:** a **signed token** instead of the raw cookie value; native **`st.login()`** (hard identity — the
  product path).
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep controls' data-source aligned with where they render; keep modal state in a flag so it survives reruns.

---

# Key Commands Learned

```text
python -m pytest tests/test_access.py tests/test_web_streamlit.py -q   # the confirm modal + the sidebar ☁ Save/Load
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Dialog persistence flag | A session flag that re-calls a `st.dialog` each run so it stays interactive |
| Active vs picked squad | The session squad (built/uploaded) vs a display-only pick from `squad_picker` |
| Sidebar render order | The sidebar renders at page top, before the sub-view sets state |
| Move-not-duplicate | Relocating a keyed widget (can't render twice) + a pointer where it was |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/access.py` (`_confirm_logout`, `_beta_confirming`) | The confirm modal + its persistence flag |
| `src/web_streamlit/squads.py` (`render_cloud_sync`, `render_sidebar`) | The ☁ Save/Load now in the sidebar |
| `docs/CLOUD_SQUADS.md` | Owner setup — the ☁ is in the Squads sidebar now |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-329 A confirm modal before Log out (`st.dialog`, kept open by a session flag)
- US-331 The ☁ cross-device Save/Load moved into the Squads sidebar (Saves the active squad)

**Stories Carried Forward:**

- None. (A signed token and `st.login()` remain deferred follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
