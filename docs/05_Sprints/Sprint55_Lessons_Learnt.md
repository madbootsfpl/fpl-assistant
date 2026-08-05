# Lessons Learned

**Sprint:** Sprint 055 — Streamlit visual polish (Home, player photos, team badges)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the Streamlit UI *look* great: a proper Home landing (all six pages), player photos on Players, and
team badges on Fixtures + Players — via a light `team.code` ingest for the badge URLs. Thin, reuses the
stored data; core unchanged; no new ADR.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Verifying an external feature (image URLs) at planning before committing to it.
- Light additive schema migrations that `refresh` backfills.
- Keeping a new helper in the edge so the core stays edge-free (the guardrail).

### New Skills Acquired

- `st.column_config.ImageColumn` — render URL columns as images (photos + badges).
- Streamlit's classic-multipage rule: the entrypoint **filename** is the sidebar label.
- FPL image CDN URL patterns (player `p{code}.png`, team `t{code}.png`).

---

# What Went Well ✅

- **The URL probe at planning paid off** — verifying the FPL photo/badge URLs (and that `teams[].code`
  existed) meant the images just worked first time.
- **A tiny data touch, kept honest** — `team.code` was a nullable additive migration; `Team.from_api`
  reuse meant zero ingest-code change; `refresh` backfills it.
- **The edge boundary held** — the `badges.py` helper is in `src/web_streamlit/`; the guardrail confirmed
  the core imports no edge.
- **Graceful images** — the browser fetches them; a missing code → an empty cell, no crash.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Renaming the Home tab | Streamlit's classic multipage labels the entrypoint by *filename* | `app.py` → `Home.py` (+ runner/tests) |
| Two image columns collided | A dict can't have two `""` keys | Rename photo key to `"photo"`, add `"badge"` — each an `ImageColumn` |
| Asserting an image column in `AppTest` | pandas truncates a wide table's string repr | Inspect the DataFrame column directly (`df["photo"]` / `df[""]`) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe the external bit first | Confirming the image URLs resolve (200) up front removed the only real risk |
| Additive migrations stay safe | A nullable column + `_MIGRATIONS` entry; `refresh` backfills; old DBs keep working |
| Reuse the model's `from_api` | Adding a field to `Team.from_api` means ingest picks it up with no other change |
| Filename = sidebar label | In classic Streamlit multipage, rename the entrypoint file to rename the tab |
| Test the value, not the repr | `at.dataframe[0].value[col]` beats `str(df)` (which truncates) |

---

# Development Lessons 💻

- De-risk the external dependency (image CDN) at planning, not at build.
- Keep display-only metadata out of the analytics conversation — a badge URL isn't a decision, so no ADR.
- When a UI helper is shared across pages, put it in the edge package (not the core) — the guardrail keeps
  you honest.

---

# AI Collaboration Lessons 🤖

- The owner's review notes drove the sprint (Home rename, images) — small, high-satisfaction polish.
- The bigger asks (deploy/share) were captured in the Backlog rather than crammed in — sized honestly.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| — | No ADR — UI polish over the settled Streamlit edge (ADR-052) + a display-only `team.code` field (a badge URL). Confirmed with the owner at planning. | n/a |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Deploy & share** at `fpl.malahide.cc` (Backlog — a gated infra sprint; unblocks feedback); a
  **Compare/Captain** Streamlit page; or **Data Hardening** post-GW1 (per-GW history + form). GW1:
  2026-08-21.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep probing external bits at planning; keep migrations additive; keep shared UI helpers in the edge.

---

# Key Commands Learned

```text
python app.py refresh                # backfills team.code (and the rest) from bootstrap-static
python -m src.web_streamlit          # the UI (Home + 6 pages, with photos + badges)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `ImageColumn` | A `st.dataframe` column config that renders URL cells as images |
| FPL asset `code` | An id (distinct from `id`) used to build player photo / team badge URLs |
| Additive migration | A new nullable column added to an existing table; backfilled on refresh |
| Entrypoint filename = tab | Streamlit's classic multipage labels the home page by its file name |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/badges.py` | The team-badge URL helper (edge) |
| `docs/08_Handbook/12_FastAPI.md` | How the web edges + pages + images work |
| ADR-052 | The Streamlit edge these pages extend |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Streamlit images / column_config | | |
| Additive schema migrations | | |
| Probing external deps at planning | | |
| Architecture | | |
| AI-assisted Development | | |

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

- US-162 Home rename + player photos
- US-163 `team.code` ingest + team badges (Fixtures + Players)
- US-164 docs + polish + smoke

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
