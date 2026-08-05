# Lessons Learned

**Sprint:** Sprint 057 — Cloud squads: build · download · upload (per-user, no server)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Give the deployed app **per-user squads** without a server. Community Cloud's disk is ephemeral *and*
shared across users, so there's nowhere safe to save. The chosen model (ADR-054): a session **"active
squad"** in `st.session_state`, set by **building** (Build → Download a `squad.json` + Use this squad) or
**uploading** one; persistence is the user's own file; **Analyse · Transfer · Captain** run the engine on
the squad dict; a committed demo seed populates the pages. The web never writes server-side.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Choosing an architecture from the *deployment reality* (ephemeral + multi-user disk → no server writes).
- Reusing one engine across edges — the web pages call the same functions the CLI does.
- Proving a round-trip (build → download → upload → the same dict) before trusting the format.

### New Skills Acquired

- Streamlit session state as per-user memory (`st.session_state`) with `download_button` / `file_uploader`
  as the persistence layer — no database.
- Applying a file upload exactly once by keying on its `file_id` (so a re-run doesn't clobber a built squad).
- A guardrail expressed as a source scan (no web edge may contain `.save(`).

---

# What Went Well ✅

- **The format round-tripped exactly as probed at planning** — a built squad → `download_button` →
  `file_uploader` → `parse_uploaded` → the same dict, so no rework.
- **Dict-based pages were nearly free** — Transfer already consumed `squad["player_ids"]`, so it only
  needed the shared picker.
- **"No server writes" stayed a one-line test**, not a design headache — a scan of both edges for `.save(`.
- **The demo seed + `SQUADS_PATH` fallback** mirrored the `seed.db` pattern, so first-visit pages aren't
  empty.
- Core analytics untouched — this was all edge wiring.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| An empty `squads.json` (`{}`) would crash the picker | `st.selectbox([])` → `None` → a `KeyError` lookup | Guard `squad_picker`: no squads → an info + `st.stop()` |
| A re-run could re-apply an upload over a freshly built squad | Streamlit re-runs the whole script each interaction | Apply an upload once, keyed by `uploaded.file_id` |
| A stale demo seed vs a refreshed DB could reference departed players | The seed's ids are a point-in-time snapshot | Validate ids on upload; the pages filter to current players |
| Analyse-by-name couldn't fit an *uploaded* squad | It went through `ask "analyse {name}"` (name lookup) | Run `analyse_squad` on the squad **dict** directly |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Deployment shapes state | An ephemeral, shared disk rules out server writes — persistence must be the user's own file |
| Session state = per-user memory | `st.session_state` + download/upload gives per-user squads with no DB and no accounts |
| Apply uploads idempotently | A whole-script re-run means "did I already apply this?" — key on `file_id` |
| One engine, many edges | Running the CLI's own functions on a dict keeps the web from drifting from the CLI |
| Guardrails as tests | "The web never writes" is enforceable as a source scan, not just a convention |

---

# Development Lessons 💻

- Let the runtime environment (here: a shared, ephemeral disk) drive the design, not the other way round.
- Verify the *data path* end-to-end (round-trip the file) before building UI on top of it.
- Prefer feeding the engine a plain dict over a name lookup — it works for built *and* uploaded state.
- Encode an invariant ("no server writes") as a test so it can't silently regress.

---

# AI Collaboration Lessons 🤖

- The owner's reframing — "each user needs to save their own squad somewhere" — pointed straight at Path 1
  (files + session), avoiding a premature server/accounts build.
- A gate (ADR-054) before code kept the model settled — the two owner calls (sidebar upload; a Captain
  page) were folded in up front, not retrofitted.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-054 | Cloud squads — a session **"active squad"** (build/upload) + **download/upload** persistence (the user's file; no server writes); a committed demo seed (`SQUADS_PATH` fallback); Transfer/Analyse/Captain consume the dict | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner:** refresh the seed (optional) + redeploy (auto on push); gather tester feedback on the
  build/download/upload flow. Later: **Data Hardening** post-GW1 (2026-08-21: per-GW history + form); a
  differentials/value `ask` intent; possibly editing a squad player-by-player in the UI.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep letting the deployment reality choose the design; keep proving the data path before the UI.

---

# Key Commands Learned

```text
python -m src.web_streamlit           # run the multipage Streamlit app locally
grep -rn "\.save(" src/web src/web_streamlit   # the no-server-writes guardrail, by hand
git check-ignore -q data/seed_squads.json; echo $?   # 1 = tracked (the demo is committed)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Session state (`st.session_state`) | Per-user, per-session memory in Streamlit — here, the active squad |
| Active squad | The session's chosen squad dict (built or uploaded) that pages run the engine on |
| Demo seed (`seed_squads.json`) | A committed squad so cloud pages aren't empty on a first visit |
| Idempotent upload | Applying a file once (keyed by `file_id`) despite Streamlit's per-interaction re-runs |
| No server writes | The web edge never persists to disk — persistence is the user's downloaded file |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-054 | The cloud-squad model (session active squad; files; no server writes) |
| `src/web_streamlit/squads.py` | The edge helper — state, picker, upload validation, sidebar |
| Handbook Ch 12 | The web-UI chapter, now with the cloud-squads section |

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

- US-168 Gate — ADR-054 (session active squad; download/upload; demo seed; no server writes)
- US-169 The mechanism — `web_squads` helper, seed + `SQUADS_PATH` fallback, Build page (Download + Use)
- US-170 Consumers — Analyse · Transfer · new Captain page on the squad dict; docs

**Stories Carried Forward:**

- Owner refreshes the seed (optional) + redeploys; gathers tester feedback

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
