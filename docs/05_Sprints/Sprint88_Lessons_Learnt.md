# Lessons Learned

**Sprint:** Sprint 088 — UX polish: clickable Ask examples · CLI availability flags · chance% on ❓

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Three small, tester-facing polish wins: make the Ask examples one-click, show the 🚑 availability flag on the
CLI ranking tables (like the web), and show *how* doubtful a ❓ player is (a chance%).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **One change, many surfaces** — a shared helper (`_ask`) and a shared flag (`availability_flag`) so a
  single edit improves both the chat box + buttons and both the web + CLI columns.
- Working *with* a byte-aligned CLI renderer instead of fighting it.

### New Skills Acquired

- `st.chat_input` can't be pre-filled programmatically, so "clickable examples" = **run-on-click** via the
  same handler as typing (then `st.rerun()`).
- In a monospace CLI table, an **emoji renders ~2 cells** but `len()` is 1 — so an emoji column belongs
  **last**, where its width can't cascade into the aligned columns before it.
- Substring-based renderer tests + statusless fixtures meant a *new* column added no test churn.

---

# What Went Well ✅

- **Shared helpers paid off twice** — `_ask()` unified two entry points; `availability_flag`'s one-line
  chance change enriched the web *and* the CLI at once.
- **The CLI alignment trap was avoided by design** — last-column placement; verified on real data that the
  columns before Fit stay aligned even with 🚑/❓ present.
- **No new ADR, no drift** — all three extend existing decisions (US-227, ADR-074); display-only.
- 622 → 625 tests; ruff + CI-parity green; seed.db clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Can't pre-fill the chat box | `st.chat_input` has no programmatic value | Buttons **run** the example via a shared `_ask()` + `st.rerun()` |
| Emoji could break CLI alignment | emoji ≈ 2 terminal cells, `len()` = 1 | Put the Fit column **last** — its width can't cascade |
| Would adding a column churn the byte-exact tests? | ADR-025 tables are alignment-sensitive | The tests are substring-based + fixtures lack `status` → no changes needed |
| Enriching the ❓ flag in two places | web + CLI both use the flag | Change the one shared `availability_flag` — both inherit `❓ 75%` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Run-on-click | A "clickable prompt" runs the same handler as typing, then reruns |
| Emoji width in monospace | Keep emoji columns last so their 2-cell width doesn't misalign the rest |
| Shared helper leverage | One `_ask` / one `availability_flag` change reaches every surface using it |
| Substring tests are forgiving | Adding a column doesn't break assertions that check for content, not layout |

---

# Development Lessons 💻

- Prefer a shared entry point (`_ask`) over duplicating the answer-and-record flow.
- When adding to an alignment-sensitive renderer, add at the end and verify with a real, flagged row.
- Enrich a signal at its source (the helper) so every consumer benefits from one edit.

---

# AI Collaboration Lessons 🤖

- A "polish bundle" of small, independent items is a good low-risk sprint between features — each ships and
  tests on its own, and they compound (US-236 improved the US-235 column for free).

### Notes _(for Tony)_

---

# Decisions Made 📋

No new ADR — all three stories **extend** existing decisions:
- **US-234** extends **US-227** (Ask example prompts) — copy-paste → clickable.
- **US-235 / US-236** extend **ADR-074** (availability flags) — to the CLI ranking views, and a chance% on ❓.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the momentum boards go live.
- Backlog still open: bench order (auto-sub priority); a season countdown / deadline banner; pronoun-aware
  chat; server-side squad persistence (Path 2).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep bundling small, independent polish items into a single low-risk sprint between features.

---

# Key Commands Learned

```text
python app.py table          # the CLI ranking table now has a Fit column (🚑/🚫/⛔/❓; ❓ shows a chance%)
python -m src.web_streamlit  # Ask → click an example to run it
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Run-on-click | A clickable prompt that runs the question (no box to pre-fill) |
| Last-column flag | An emoji column placed last so its width can't misalign a monospace table |
| Chance% on ❓ | A doubtful flag that shows the player's chance of playing (`❓ 75%`) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/pages/4_Ask.py` | The shared `_ask()` helper + clickable examples |
| `src/ui/table.py` · `src/ui/xg.py` | The CLI Fit column (last) |
| `src/analytics/crowd.py` | `availability_flag` — now with the doubtful chance% |

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

- US-234 Clickable Ask examples — a button per example runs it (shared `_ask` helper)
- US-235 CLI availability flags — a last-column Fit flag on table/search/filter + xg (extends ADR-074)
- US-236 chance% on ❓ — `availability_flag` appends the doubtful chance (`❓ 75%`)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
