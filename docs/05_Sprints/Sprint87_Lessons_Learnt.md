# Lessons Learned

**Sprint:** Sprint 087 — "Talked about": count mentions across a bigger sample

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix the Trending → "Talked about" board reading as "everyone has 1 mention": count mentions across the latest
**~100** Reddit posts (not 25), and paginate the now-longer board — while staying a best-effort, cached,
degrade-gracefully **buzz lens** that never touches xP.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reproducing a bug on real data before fixing it** — a live fetch showed the counter was fine, redirecting
  the fix from "the maths" to "the sample size".
- Making a UI-gated + cached + networked feature **testable** with a monkeypatched fetch + a cache clear.

### New Skills Acquired

- Reddit's public `.rss` returns only **25 posts** by default but honours **`?limit`** up to **100** — a
  bigger, cheap sample for a buzz count.
- `st.cache_data.clear()` in a test makes a `@st.cache_data` code path deterministic (no inherited fetch).
- A `429` in planning is a *signal*, not just a failure — it confirmed the degrade path and the need for the
  cache + button gate.

---

# What Went Well ✅

- **Diagnosis first.** The distribution `{1: 35, 2: 8, 3: 3, 4: 5}` from a real fetch made the root cause
  obvious (small sample), so the fix was a one-param change, not a rewrite of the counter.
- **Minimal, reused parts** — `?limit=100` + the shared `paginate`; the counter and the degrade contract were
  untouched.
- **Backward-compatible** — a defaulted `limit` param left the fake clients and `community_signals` working.
- 619 → 622 tests; ruff + CI-parity green; seed.db clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "1 mention regardless" | the default `.rss` is 25 posts → 35/51 players at 1 | Request `?limit=100` → count across ~100 posts |
| Couldn't re-verify a larger fetch | Reddit `429` after the first call | Trust the documented RSS `limit` max; unit-test the request URL + count; live count = a DoD smoke |
| Testing a button-gated + cached + networked board | it fetches Reddit | Monkeypatch `get_subreddit_rss` to a fixture + `st.cache_data.clear()`; click the button |
| A 100-post sample mentions many players | more mentions found | Paginate the board at 30 like the other Trending boards |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reproduce before fixing | The counter was correct; the data (sample size) was the bug |
| RSS `?limit` | Reddit's `.rss` defaults to 25, accepts up to 100 — a cheap way to widen a buzz count |
| Deterministic cache tests | `st.cache_data.clear()` + a monkeypatched fetch make a cached UI path testable |
| Degrade path as signal | A 429 in planning validated the graceful-degradation design |

---

# Development Lessons 💻

- When a count "looks stuck", check the *input size* before the logic.
- Keep a defaulted new param so existing callers/fakes don't break.
- Reuse a shared helper (`paginate`) rather than hand-rolling a list cap.

---

# AI Collaboration Lessons 🤖

- Grounding the tester's report in a live fetch (rather than trusting "it's capped at 1") turned a vague bug
  into a precise, small fix — and avoided "fixing" a counter that was already correct.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-076 | **"Talked about" — count mentions across a bigger sample** (refines ADR-059) — request `?limit=100` (`config.REDDIT_RSS_LIMIT`) so `community_buzz` counts across ~100 posts (the counter already sums every match); paginate the longer board at 30. Stays a cached, button-gated, degrade-on-failure buzz lens; `decision_xp` untouched; no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Live-verify** the higher counts on the deployed app once Reddit isn't throttling (and confirm the Cloud
  IP isn't blocked).
- Post-**GW1 (2026-08-21)**: buzz sharpens as real discussion picks up; the Data Hardening flip + calibration.
- Possible: a chance% on the ❓ availability flag; the Fit flag on the CLI ranking views.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reproducing "it shows wrong data" reports on a real fetch/DB before touching the logic.

---

# Key Commands Learned

```text
python -m src.web_streamlit      # Trending → 💬 Talked about → counts across ~100 posts, paginated at 30
python -m pytest tests/test_community.py -q   # the buzz counter + the ?limit=100 request
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| RSS `?limit` | Reddit's post-count query on `.rss` (default 25, max 100) |
| Buzz lens | Mention frequency (not sentiment); display-only, never xP |
| Sample size | The number of posts counted — the real driver of the mention counts |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-076 | The bigger-sample decision + the "counter was fine, sample was small" evidence |
| `src/api/reddit.py` | `get_subreddit_rss(..., limit=…)` — the `?limit` request |
| `src/community.py` | `community_buzz` — the (unchanged) counter |

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

- US-232 Bigger RSS sample — request `?limit=100` so "Talked about" counts mentions across ~100 posts (ADR-076)
- US-233 Paginate the "Talked about" board at 30 (shared `paginate`)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
