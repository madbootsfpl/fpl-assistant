# Architectural Decision Record: Value above the fold

**Decision ID:** ADR-175
**Date:** 2026-09-02
**Status:** 🚧 **Proposed — owner's design, four changes in one pass. Preview before code.**
**Superseded By / Replaces:** **Reverses ADR-171 §3** (answer-first) and **supersedes ADR-174** (which put the
apply button in a stacked block). Narrows **ADR-077**'s shared horizon on this page. Moves **ADR-113**'s
Your-team panel conditionally. Re-opens what **ADR-115** settled, with a different mechanism.
**Deciders / Participants:** Tony Sheridan (Owner — design), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"Our golden page has a lot of real estate used up before we get to the value of the page."*

Counted from the owner's screenshot, **ten blocks precede the first useful thing**, and on a phone the entire
first viewport is chrome:

> title · brand mark · page caption · "Tool" label + tabs · "Gameweeks ahead" label + 1/2/3/4/5/10 ·
> deadline · "Squad" label + picker · YOUR TEAM banner · Backup/import expander · legality line ·
> **then "This week"**

The page also measures **41 blocks / 9 interactive** against the **14** ADR-115 called *"a wall"*.

---

### ✅ Decision — four changes, one pass

**1. Cut the chrome that is stale, duplicated, or explains the page you are on.**

| block | why it goes |
|---|---|
| page caption — *"squad · captain · transfers · chips · **health**…"* | **stale** (ADR-166 renamed Health → DNA six days ago) and **redundant**: it explains the page to someone already on it, under a title that names it and above tabs that list every item |
| the **"Squad" picker** as a separate control | it says *"RoboTS (yours)"*; four lines below, the banner says *"YOUR TEAM · RoboTS"*. **Two elements naming one squad.** The switcher folds into the banner, where it belongs — most managers have one team |
| the labels **"Tool"** and **"Squad"** | five tabs named My Squad/Transfer/DNA/Leagues/Lab need no caption saying "Tool" |

**Kept:** the deadline (time-critical, not derivable from the pitch) and the legality/cost line (compact, and
the one thing the pitch cannot show).

**2. The horizon becomes `GW1 | GW1–3`, on the pitch.** The owner's reasoning: *"I don't think this analysis
will be done here — yes in the Lab when you're creating your team, but not now when active."* **The project
already half-agreed:** US-374 defaults the squad tools to **1** and the Lab to **5**, because a wildcard is a
multi-week bet and a Tuesday is not. Offering **10** on an active squad offers a window nobody chose.

⚠️ **Scoped, because one control feeds five consumers** — pitch, This week, Transfer, DNA, Lab. Transfer and
DNA keep a longer range on their own tabs, where a 5-week read is defensible and where ADR-174's *Longer
view* line is measured. US-374 already precedents per-mode horizon keys, so this is that pattern extended,
not a new one.

**3. Backup / import moves to the sidebar — conditionally.** ADR-113's own words are *"import it **once**,
edit anywhere"*, and a once-a-season action holds permanent space on the most-visited page. But it was
consolidated onto the page so a new user could find it, so: **on the page while there is no squad** (the
expander already auto-expands in exactly that state), **in the sidebar once there is one.** Discoverable when
it matters, gone when it does not.

**4. The answers become one selectable line under the pitch.**

```
[ This week | Captain | Transfer | Chips ]
```

The house idiom already — Players views, Trending boards, Scout. One answer at a time instead of three
stacked, and **the pitch stays visible while you switch**, which is what makes this different from the
top-level tabs ADR-171 merged away.

**Transfer joins it, and that supersedes ADR-174 by one day.** ADR-174 declined to bring the Transfer tab in
because it meant ~10 widgets *stacked* onto a 41-block page. Behind a selector those widgets exist only when
chosen, so the density objection does not apply. The top-level nav drops to **My Squad · DNA · Leagues · Lab**.
ADR-174's apply button survives inside the *This week* panel, where it was always meant to sit.

---

### 🔀 The reversal, stated plainly

**This reverses ADR-171 §3.** Six days ago the page was made answer-first, on my recommendation and the
owner's explicit call. It now leads with the strip and the pitch.

That is legitimate, and the reason matters: **ADR-171's measurement was about cost, not order.** It proved the
answer *could* render on the page (123 ms on Cloud, against a supposed 4.4 s). Answer-first was a judgement
laid on top of that finding, and the owner has since lived with it. **Use beats argument**, and no measurement
is being contradicted.

---

### 🧭 On churn — the owner's steer, recorded as a decision

This page has changed three times in six days (ADR-166, ADR-171, ADR-174). I raised that as a cost: testers
re-learn a layout each time. The owner's answer:

> *"This is our golden page. Testers are bought in and will agree this is the best outcome, even if it reverts
> back and forward."*

**Recorded as a deliberate weighting, not an overruled objection.** For this surface, arriving at the right
page beats holding a settled one — the testers are a small, engaged group who are here for the product
getting better. That trade would not hold for a public release, and it should be re-argued if the audience
changes.

---

### 🧭 Consequences

**Positive** — value starts at line 2 rather than line 11; a stale sentence and a duplicated control go; the
horizon offers what is actually used; one answer at a time; the pitch stays visible while switching; Transfer
becomes reachable without leaving the squad.

**Negative / risks (mitigations)** — a selector is a click the stacked version did not need (*mitigation:* it
replaces a scroll, and the pitch no longer leaves the screen). ADR-174 is superseded within a day
(*mitigation:* its button survives; only its container changes, and the mechanism genuinely differs).
**ADR-135 is the standing warning** — this page's density was optimised once, hit its number exactly, and was
reverted the same day (*mitigation:* that failed on **responsiveness**, not layout; nothing here adds a
round-trip, and the owner reviews a real-data preview before any code).

---

### 📏 How this gets judged

Not by block count — that is ADR-135's trap. By one thing: **on a phone, the strip and the pitch are visible
without scrolling.** Everything above them is chrome and has to earn its line.
