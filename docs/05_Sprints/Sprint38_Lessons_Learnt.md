# Lessons Learned

**Sprint:** Sprint 038 — two new `ask` intents: start/bench + compare

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Grow the natural-language layer with the two most-asked weekly questions — *"who should I
start/bench?"* and *"A or B?"* — both grounded (the ✓/⚠ trust line), both xMins-aware, both pure
composition of the existing analytics. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Probing the deceptively-simple part (string matching on real names) before building on it.
- Giving each intent a graceful, *specific* answer for its failure modes.
- Composing a feature from parts already built (optimiser + xP + xMins + verifier + shared table).

### New Skills Acquired

- Robust name extraction: bounded substring + drop-substring-overlap + ambiguity detection.
- A soft-`message` short-circuit so a decision can reply "can't do that, here's why" cleanly.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **The gate probe pre-solved the hard part** — the name-matcher looked trivial but the probe exposed
  `Fernandes` ⊂ `B.Fernandes` and duplicate `Palmer` before any code, so US-114 implemented settled
  rules instead of discovering them mid-build.
- **Pure composition again** — both intents reuse `select_squad`, xP, xMins, the verifier, and the
  shared table; the sprint added two renderers and glue.
- **Honest edge-cases as first-class answers** — "already optimal" and specific not-found / ambiguous
  messages beat a silent wrong pick or a generic error.
- **Grounding held for free** — both intents reuse `verify_grounding`; the ✓ line just works.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Name-match overlap | `Fernandes` is a substring of `B.Fernandes` | Drop a match that is a substring of another matched name |
| Ambiguous names | Two players named `Palmer` | Detect duplicates → a disambiguate message (never a silent pick) |
| A decision that must say "can't" | not-found / <2 / ambiguous aren't facts-to-narrate | A soft `message` on the decision + an `assemble` short-circuit |
| start/bench "no change" on TS | The squad is already optimal | Treat "already optimal" as a first-class answer; value grows in-season |
| "or" over-routing | `start X or Y` matches start/bench first | Accept for v0; compare needs ≥2 players and bails gracefully |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe the simple bit | String matching on real names is where the bugs hide — verify it early |
| Specific > generic failure | Each intent should explain its own failure, not fall back to a catch-all |
| Distinct overlapping surfaces | Lineup decision vs health check — keep them distinct; routing order disambiguates |
| Analytics decide, LLM narrates | compare states the higher xP as a fact; the model only explains it |
| Compose, don't rebuild | Two intents, zero new analytics — just renderers + glue |

---

# Development Lessons 💻

- A one-off probe of the fiddly input (overlapping/duplicate names) saved a mid-build rewrite.
- Model a soft failure as data (`{"message": ...}`) so the pipeline handles it uniformly.
- Reuse the seam you already have (the shared table, the verifier) rather than growing a new one.

---

# AI Collaboration Lessons 🤖

- One focused UX question up front (how to show the weight, last sprint) and a gate probe this sprint
  meant the builds were mechanical — the thinking happened before the code.
- The grounding verifier makes new intents cheap to trust: wire `subjects`, reuse the check, done.

### Notes _(for Tony)_

#   Player             Team  Pos       £   GW1   GW2   GW3   GW4   GW5     xP
--- ------------------ ----- ---- ------ ----- ----- ----- ----- ----- ------
1   Raya               ARS   GK      6.0   4.5   3.7   3.7   4.1   4.1   20.2
2   Gabriel            ARS   DEF     8.0   6.2   5.1   5.1   5.7   5.7   27.8
3   Senesi             TOT   DEF     6.0   4.3   4.8   4.3   4.3   4.3   22.1
4   Guéhi              MCI   DEF     6.0   4.3   4.3   4.7   3.8   4.7   21.8
5   Wilson             LEE   MID     6.5   5.7   5.7   5.7   6.3   5.7   29.0
6   Semenyo            MCI   MID     8.5   5.2   5.2   5.7   4.7   5.7   26.4
7   Gibbs-White        NFO   MID     8.0   5.6   4.5   5.1   4.5   5.6   25.3
8   Rice               ARS   MID     7.5   5.3   4.3   4.3   4.8   4.8   23.6
9   Anderson           MCI   MID     6.5   4.4   4.4   4.8   3.9   4.8   22.2
10  João Pedro         CHE   FWD     7.5   5.7   6.3   4.6   6.3   5.7   28.7
11  Thiago             BRE   FWD     8.0   5.0   5.0   5.5   5.0   4.5   24.8

Bench:
#   Player             Team  Pos       £   GW1   GW2   GW3   GW4   GW5     xP
--- ------------------ ----- ---- ------ ----- ----- ----- ----- ----- ------
1   Calvert-Lewin      LEE   FWD     6.0   4.3   4.3   4.3   4.8   4.3   22.1
2   Truffert           BOU   DEF     5.5   3.5   4.4   4.4   4.4   4.0   20.7
3   Kelleher           BRE   GK      5.0   3.9   3.9   4.3   3.9   3.5   19.6
4   Van Hecke          TOT   DEF     5.0   3.4   3.8   3.4   3.4   3.4   17.4

Captain lead : Wilson (29.0 xP) — `captain --squad RoboTS`.
Weakest links: Raya (20.2), Guéhi (21.8), Senesi (22.1) — `transfer --squad RoboTS`.

GWn = projected xP that gameweek (rounded; the xP total is authoritative). Projected xP is the XI's expected points over the horizon (a mean; assumes they play). `--load` shows the current state; `--sort xp` orders the XI by xP.
(venv) ➜  fpl-assistant git:(master)  python app.py transfer  --squad RoboTS --no-xmins
Transfer suggestions for 'RoboTS' — by xP gain over the next 5 gameweeks (bank £0.0m)

#   Out                  £     xP → In                   £     xP    ΔxP
--- ---------------- ----- ------ - ---------------- ----- ------ ------
1   Kelleher           5.0   19.6 → Benitez            4.5   35.0  +15.4
2   Raya               6.0   20.2 → Benitez            4.5   35.0  +14.8
3   Anderson           6.5   22.2 → Okafor             6.0   32.2  +10.0
4   Calvert-Lewin      6.0   22.1 → Wilson             5.5   32.0   +9.9
5   Van Hecke          5.0   17.4 → De Cuyper          4.5   26.9   +9.5

Each is a single, legal, affordable swap (same position, ≤3/club, within the sale price + bank). `(b)` = the player you'd sell is on your bench (less weekly impact). xP is a mean over the horizon and assumes the incoming player starts.
(venv) ➜  fpl-assistant git:(master) python app.py ask " best start/bench for RoboTS"  
Q:  best start/bench for RoboTS

Recommended lineup — 'RoboTS' (best legal XI by xMins-weighted xP)

  Projected XI xP : 217.1

Start (XI):
#   Player             Team  Pos   xMins     xP
--- ------------------ ----- ---- ------ ------
1   Raya               ARS   GK       86   19.4
2   Gabriel            ARS   DEF      70   21.7
3   Truffert           BOU   DEF      89   20.4
4   Guéhi              MCI   DEF      77   18.7
5   Semenyo            MCI   MID      79   23.3
6   Gibbs-White        NFO   MID      79   22.2
7   Rice               ARS   MID      79   20.9
8   Anderson           MCI   MID      72   17.8
9   Wilson             LEE   MID      52   16.9
10  João Pedro         CHE   FWD      61   19.5
11  Thiago             BRE   FWD      59   16.3

Bench:
#   Player             Team  Pos   xMins     xP
--- ------------------ ----- ---- ------ ------
1   Senesi             TOT   DEF      63   15.4
2   Van Hecke          TOT   DEF      78   15.2
3   Calvert-Lewin      LEE   FWD      59   14.6
4   Kelleher           BRE   GK       56   12.1

Change: your squad has no saved bench — this is the best legal XI.

`xMins` = expected minutes next GW (xMins v0); the XI is chosen on xMins-weighted xP over the horizon (a mean; assumes availability). Use `analyse --squad --no-xmins` for the raw view.

The recommended lineup change is to use the current starting XI, as it has no saved bench and is considered the optimal lineup. The projected points over 5 gameweeks for this lineup are 217.1.

✓ Checked: every figure and name in the explanation traces to the data above.

- First gives me a good squad answer, looks strong, but what is not logical is when i ask for transfers, it gives me other players with higher points output for th esame cost, why would this not be in the original output/result. Also transfer gives same player (Benitez) as incoming player twice.
- why is th estart/bench different from original line-up, I thought the original would be optimised.

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-039 | Two new `ask` intents: **start/bench** (best legal XI on xMins-weighted xP vs the declared XI; "already optimal" is first-class) and **compare** (robust name-matching — bounded substring, drop-overlap, ambiguity, not-found; a side-by-side table; analytics decide the ranking, LLM narrates). Both grounded (✓/⚠), optional, pure composition | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A smarter router (reconcile "start X or Y" → compare when there's no squad + two players). More
  Phase 4 (further intents / a chat mode / stronger verification), the web UI, or GW1 Data Hardening.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep probing the fiddly input at the gate; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py ask "who should I start from TS?"   # best legal XI (xMins-weighted) vs your bench
python app.py ask "Haaland or B.Fernandes?"       # compare two players side by side
python app.py ask "compare Saka and Palmer"       # ambiguous name → a disambiguate message
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Intent (ask) | The question type keyword-routed before the analytics decide |
| Bounded substring | A name match flanked by non-letters (a whole name, not part of a word) |
| Ambiguous name | A web_name shared by >1 player → ask to disambiguate |
| Soft message | A decision's specific "can't do that, here's why" reply (not a generic error) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-039 | The two intents' design + the name-matching rules |
| ADR-037 / ADR-036 | The grounding verifier + structured-detail pattern both intents reuse |
| ADR-038 | xMins — both intents weight xP by it |

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

- US-112 Gate — ADR-039 (name-matching + start/bench, pressure-tested)
- US-113 start/bench intent (best legal XI vs declared; "already optimal")
- US-114 compare intent (robust name-matching; side-by-side; analytics decide)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
