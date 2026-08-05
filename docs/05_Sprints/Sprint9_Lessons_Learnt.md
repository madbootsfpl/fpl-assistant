# Lessons Learned

**Sprint:** Sprint 009 — External Data: ClubElo (team strength)

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring real team strength (ClubElo Elo) into the app as a second, gracefully-degrading
data source, and use it to power an Elo-based FDR that works even in preseason.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a source in its own module without disturbing the first.
- Reusing a seam (`--type`) for a third variant.
- Verifying a data source at planning (reachability + shape + matching).

### New Skills Acquired

- Multi-source design (FPL + ClubElo).
- **Graceful degradation** — best-effort external data, keep last-known on failure.
- Parsing CSV (stdlib `csv`) and matching names across sources.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- Tony's strategic question drove a landmark direction (first second source).
- The planning check verified the source *and* found the effort (6 name mismatches).
- Graceful degradation proven live — a simulated outage left the app fully working.
- The `--type` seam absorbed a third FDR source cleanly.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Team names differ across sources | FPL "Spurs" vs ClubElo "Tottenham" | 14 exact + a 6-entry mapping; fail loudly on gaps |
| ClubElo could be down | External source, not ours | Best-effort: log + keep last-known Elo, non-fatal |
| Elo scale (~1500–2100) vs 1–5 | Different units | Rank bands (4 teams per band, strongest → 5) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Multi-source | Keep each source isolated in its own module |
| Graceful degradation | Wrap the fetch; a non-critical failure is data missing, not fatal |
| Keep last-known | Write Elo separately so a refresh (or failure) never wipes it |
| Verify the source | Check reachability + shape + name matching at planning time |

---

# Development Lessons 💻

- Resilience is designed in: isolate, wrap, keep last-known, separate the write.
- A well-placed seam (`--type`) makes a new variant a single branch.
- Verify an external source before building on it — not just your own data.

---

# AI Collaboration Lessons 🤖

- Turning a strategic question into a small, safe first step (one source) kept it manageable.
- The gate's worked examples verified the design before code (a standing habit).

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-010 | ClubElo as a best-effort second source; 14+6 name mapping; graceful degradation; Elo → 1–5 rank bands | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- FBref xG/xA (player-level), or extend `--type elo` to `xp`/`fixtures`.
- Revisit data-dependent FPL work once the season starts.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying sources at plan time + pressure-testing ADRs + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py refresh                 # now also fetches ClubElo (best-effort)
python app.py fdr --type elo --next 5 # fixture difficulty from real team Elo
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Multi-source | Data from more than one place (FPL + ClubElo) |
| Graceful degradation | A non-critical source failing is non-fatal |
| Best-effort | Try it; carry on if it's unavailable |
| Elo | A relative team-strength rating |
| Rank band | Grouping teams into 5 tiers by a value |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ClubElo (`api.clubelo.com`) | Free team Elo, no API key |
| ADR-010 | Records the ClubElo integration design |
| Handbook Ch 23 | External data & graceful degradation |

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

- US-030 ClubElo design + ADR-010
- US-031 ClubElo client + team-name mapping
- US-032 Store Elo + graceful refresh
- US-033 Elo-based FDR

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
