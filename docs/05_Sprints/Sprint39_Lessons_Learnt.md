# Lessons Learned

**Sprint:** Sprint 039 — Trust the numbers (sane xP + consistent recommendations)

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Answer the owner's challenge of three RoboTS outputs: (1) make the raw xP honest so a cameo can't
project like a star; (2) fix the transfer bug that suggested the same buy twice; (3) make the
raw-vs-xMins consistency legible (and structural). No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Root-cause diagnosis on real data before writing a fix.
- Pinning a model parameter (the prior) on the data, not a guess.
- Turning "these happen to agree" into "these call the same function".

### New Skills Acquired

- Evidence-weighted shrinkage toward a prior (regress the unknown, don't invent it).
- Greedy disjoint selection (each buy + each sell once) for a recommendation menu.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The owner's challenge was exactly right** — all three "that looks wrong" outputs traced to real
  causes (an un-gated ppg fallback, a per-out dedup gap, a flag mismatch).
- **Diagnosis before code** — the gate found each root cause, so the fixes were targeted; the prior was
  pinned below the p10 of real regulars, not invented.
- **Consistency made structural** — extracting `best_legal_xi` means `analyse` and start/bench can't
  drift, not just don't today.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Benitez 35 xP | ppg fallback had no sample gate (1 game → 7.0 ppg) | Shrink career pp90 toward a prior by evidence |
| Enes Ünal 47 xP (found in smoke) | Career-sum confidence let scattered cameos compound | Confidence from the **biggest single season**, not the sum |
| Benitez suggested twice | `suggest_transfers` picked best-in per out, no cross-dedup | Greedy disjoint moves (each buy + each sell once) |
| "start/bench ≠ my lineup" | `analyse --no-xmins` vs start/bench (xMins) — a flag mismatch | Extract `best_legal_xi`; confirm + a note (not a bug) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe broadly | One convincing example (Benitez) hid the multi-example bug (Enes Ünal) — probe many shapes |
| Don't mask, fix | xMins hid the bad raw number in the default view; the raw number still had to be honest |
| Shrinkage | Regress a low-evidence estimate toward a prior; confidence from your biggest real sample |
| Structural consistency | Two paths that must agree should call one function, not merely coincide |
| Pin params on data | The prior sits below the p10 of real 900-min players — grounded, documented, tunable |

---

# Development Lessons 💻

- Treat an implausible output as a lead: trace it to a cause before touching code.
- The smoke step earns its place — it caught Enes Ünal after the unit tests were green.
- Remove duplication when it encodes an invariant (one "best XI" primitive → can't diverge).

---

# AI Collaboration Lessons 🤖

- A sharp user "why is this number like that?" is worth more than any self-review — it found four
  implausible players I'd have shipped.
- When a fix looks done and tested, a broad live smoke is the honesty check — it corrected the design
  mid-flight (career-sum → biggest-season confidence).

### Notes _(for Tony)_

- Great i can see that the errors are fixed.
- What i still dont understand is the following:
(venv) ➜  fpl-assistant git:(master) python app.py squad --full --budget 100          
Optimal 15-man squad — objective: points, budget £100.0m

Pos Player            Team   Price   Pts
--- ----------------- ----- ------ -----
GK  Raya              ARS    £6.0m   162
GK  Kelleher          BRE    £5.0m   143
DEF Gabriel           ARS    £8.0m   209
DEF Guéhi             MCI    £6.0m   179
DEF Senesi            TOT    £6.0m   175
DEF Truffert          BOU    £5.5m   165
DEF Van Hecke         TOT    £5.0m   148
MID Semenyo           MCI    £8.5m   202
MID Gibbs-White       NFO    £8.0m   188
MID Rice              ARS    £7.5m   184
MID Anderson          MCI    £6.5m   180
MID Wilson            LEE    £6.5m   168
FWD Thiago            BRE    £8.0m   181
FWD João Pedro        CHE    £7.5m   177
FWD Calvert-Lewin     LEE    £6.0m   142

Total: £100.0m · 2603 pts
Note: Pts totals a bench that won't score — squad strength, not a weekly total. Declare your bench with --bench.
(41 unavailable excluded: Garner (i), J.Timber (i), Saliba (i)… — use --include-unavailable to keep them.)
(venv) ➜  fpl-assistant git:(master) python app.py transfer  --squad RoboTS           
Transfer suggestions for 'RoboTS' — by xP gain over the next 5 gameweeks (bank £0.0m)

#   Out                  £     xP → In                   £     xP    ΔxP
--- ---------------- ----- ------ - ---------------- ----- ------ ------
1   Thiago             8.0   16.3 → Watkins            8.0   24.1   +7.8
2   Kelleher           5.0   12.1 → Roefs              5.0   17.5   +5.4
3   Senesi             6.0   15.4 → Mukiele            5.5   19.5   +4.1
4   Wilson             6.5   16.9 → E.Le Fée           6.0   19.0   +2.1
5   Van Hecke          5.0   15.2 → Mitchell           4.5   16.9   +1.7

Each is a single, legal, affordable swap (same position, ≤3/club, within the sale price + bank). `(b)` = the player you'd sell is on your bench (less weekly impact). xP is weighted by expected minutes (xMins v0; `--no-xmins` for raw).

- I create a squad designed to give max points, and the output looks great. I then ask for transfers, and i get suggestions that will give me more points. So my question is why was this not given at the start? There should be no transfers that will give extra points when nothing else has changed or am i confused?

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-040 | Sane low-evidence xP: shrink a no-baseline player's career pp90 toward a replacement prior (2.0) by confidence from their biggest single season (not the career sum); a three-tier rate on `player_xp` (`hist`/`fallback`/`current`). Transfer dedup: disjoint moves (each buy + sell once). Consistency: `best_legal_xi` shared by `analyse` + start/bench; a note on raw vs xMins | Accepted |

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

- (GW1) Revisit optimistic ≥900-min partial-season baselines (Okafor/Cherki); consider positional
  priors. Then more Phase 4, the web UI, or Data Hardening.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate probe broad (many players/shapes); keep the 3-part DoD — the smoke is the safety net.

---

# Key Commands Learned

```text
python app.py transfer --squad RoboTS --no-xmins   # raw xP now sane (no cameo tops the list); no repeated buy
python app.py analyse  --squad RoboTS              # default XI == the start/bench XI (shared best_legal_xi)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Shrinkage / regression to the mean | Pull a low-evidence estimate toward a prior by how much data backs it |
| Prior (replacement level) | The rate we assume for an unknown player (~2.0 pp90 here) |
| Disjoint selection | A menu where each buy and each sell appears at most once |
| Structural consistency | Two features agree because they call one function, not by coincidence |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-040 | The low-evidence damping + dedup + consistency design |
| ADR-028 / ADR-038 | The ≥900-min baseline this extends + xMins (which was masking the raw number) |
| Sprint 026 lessons | The original "probe broadly" lesson — it recurred here (Enes Ünal) |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Diagnosing implausible output | | |
| Shrinkage / priors | | |
| Structural consistency | | |
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

- US-115 Gate — ADR-040 (diagnosis + shrinkage/dedup/consistency decisions)
- US-116 Sane low-evidence xP (shrink toward a prior; biggest-season confidence)
- US-117 Transfer dedup (disjoint moves) + `best_legal_xi` (structural consistency)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
