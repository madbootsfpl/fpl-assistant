# MADBOOTS — Marketing Video Scripts

A living home for the AI-video scripts + the series plan. Draft here, refine, then produce.

## Brand & production notes (apply to every script)

- **Name:** always **MADBOOTS** (all-caps, one word). Never "MadBoots" / "Mad Boots".
- **Throughline / sign-off:** *"The analytics decide. **Every answer shows its working.** You make the call."*
  ⚠️ **Changed by ADR-168 (2026-08-29) and this file did not follow until 2026-08-31.** The old middle clause
  was *"The AI explains"* — a three-part promise the deployed app kept two thirds of, because there is no
  Ollama on Streamlit Cloud. `brand.MANTRA` is the source of truth; **§§1-2 and 4-9 below still close on the
  retired line and need re-cutting before they are produced.**
- **Presenter & voice** *(owner decision, 2026-08-13):* the **MADBOOTS avatar/mascot** — named **Maddie**
  *(owner, 2026-08-15; avatar generated, first HeyGen video made)* — **not** an AI human, so it stays on-brand and
  dodges the uncanny-valley that would undercut an honesty brand. Voice: a **strong female** — calm, clear,
  authoritative (the *trusted analyst*, never FPL-bro hype). Keep the **same avatar (Maddie) + voice + music across
  every video** — consistency is where the brand compounds. *Series plan: one 60-sec explainer per topic, hosted by
  Maddie.*
- **The moat is trust — lead with it.** Position *against* the "AI that guesses" / paid black-box crowd:
  **"Most FPL AI just guesses. MADBOOTS shows its working."** Every claim is checked against the data (✓/⚠).
- **❌ Never mention Ollama / "run it locally".** The live app is **data-only**; naming a local dev tool confuses
  viewers and undercuts the honest-analytics story. Frame explanation as the **Edge · Risk · Confidence** + the ✓/⚠
  that everyone sees.
- **Always end on a CTA:** *"Try MADBOOTS **free** at **madboots.com**."* (Say **free** — kills friction.)
- **Conversion beat for existing managers:** *"Import your real team with your manager ID."* (⚠ live from the **GW1
  deadline, 21 Aug 2026** — dormant if a video launches preseason.)
- **Show, don't tell:** mark where real UI shots go — the green pitch · Boot Battle head-to-head · the AI-Tips plan ·
  the ✓/⚠ trust line. Visuals sell harder than the voiceover.
- **Cuts:** a 2-min explainer (hero), a 60-sec social cut, and 30–45s single-feature shorts (Reels/TikTok/Shorts).
- ⏱️ **Maddie reads at ~119 wpm — measured, not assumed** *(2026-08-31)*. The produced §0 cut is **159 words
  in ~80s**. Every draft in this file was written to a faster pace (~150 wpm), so **every stated duration was
  optimistic by 25-70%**: the "2-minute" hero is really **2:27**, the "~50s" shorts run **61-90s**. Budget
  **~2 words per second** when drafting, and treat the numbers below as the real ones:

  | § | script | words | real length | its target | verdict |
  |---|---|---:|---:|---:|---|
  | 0 | Maddie's intro | 178 | **~90s** | ~80s | trim the Leagues clause → ~84s |
  | 1 | Hero explainer | 291 | **~2:27** | 2:00 | fine as a hero; retitled honestly |
  | 2 | Social cut | 125 | **~63s** | 60s | ✅ lands |
  | 4 | xP & Confidence | 172 | **~87s** | ~55s | **needs a real cut** for a short |
  | 5 | Finding Differentials | 178 | **~90s** | ~50s | **needs a real cut** — or split into two |
  | 6 | Build the Perfect Squad | 134 | **~68s** | ~50s | trim |
  | 7 | Your Week, Answered | 121 | **~61s** | ~50s | close |
  | 8 | Leagues & Head-to-Head | 107 | **~54s** | ~45s | close |
  | 9 | Boot Battle | 97 | **~49s** | ~40s | close |

  §§4 and 5 are the two that genuinely do not fit a Reels/Shorts slot as written — worth deciding whether to
  cut them hard or let them be 90-second YouTube pieces, since both are educational and age well.

---

## 0 · Maddie's intro — ~85s  *(PRODUCED: <https://youtu.be/a7WG0MBDLFg>; **revised 2026-08-31, needs a re-record**)*

The only script here that has been rendered — it fronts the madboots.com hero lightbox and seeds the in-app
**Maddie Explains** hub. **⚠ Screens marked "NEW SHOT" changed under it** (ADR-166 folded Squad Lab into
My Squad ▸ Lab; ADR-171 put the week's answer at the top of My Squad).

> **[0:00 — Open · the MADBOOTS mark]**
> Hi — I'm Maddie. Welcome to MADBOOTS, the Fantasy Premier League assistant that shows its working.
>
> **[0:08 — Build or import · ⚠ NEW SHOT: My Squad ▸ Lab, not a sidebar page]**
> In My Squad, open the Lab: set your budget, what to optimise for, and how strong you want your bench — and
> MADBOOTS builds an optimised fifteen in seconds. Already play? Import your real team with your manager ID.
>
> **[0:29 — Adopt it · the *Use this squad* button]**
> Happy with it? Tap *Use this squad*, and it's your active team.
>
> **[0:35 — ⚠ NEW SHOT: the top of My Squad — the *This week* block]**
> My Squad then gives you the whole week on one screen: who to captain, any lineup change, and the one
> transfer worth making — each with the edge for it, the risk against, and a confidence score.
>
> **[0:53 — The pitch · tap a shirt → card → Boot Battle, then scroll to Captaincy + Chips]**
> Below it, your team on a live pitch. Tap any player for their card, or compare two with Boot Battle. Then
> captaincy ranked, and when to play each chip.
>
> **[1:07 — ⚠ NEW SHOT: Players ▸ Scout, then My Squad ▸ Leagues]**
> Going deeper? Scout reads five stat boards at once and names the players worth a look — and Leagues puts
> your picks against your rivals'.
>
> **[1:18 — Close · the ✓ trust line, then the mark]**
> The analytics decide. Every answer shows its working. And you make the call. MADBOOTS — free at
> **madboots.com**.

*176 words ≈ **89s** at Maddie's measured pace (~119 wpm, derived from the produced 80s cut). To land nearer
80s, drop the Leagues clause — "— and Leagues puts your picks against your rivals'" — for ~84s.*

**What changed from the produced version, and why:**

| was | now | why |
|---|---|---|
| "**AI** clarifies the data" | "shows its working" · "every answer shows its working" | **The deployed app has no AI.** ADR-168 removed this exact clause from `brand.MANTRA` for this exact reason. An honesty brand whose *first sentence* over-promises is the worst possible place for it |
| "MadBoots" | **MADBOOTS** | this file's own first brand rule |
| "your **ultimate** FPL assistant" | "the FPL assistant that shows its working" | *"never FPL-bro hype"* — and an unfalsifiable superlative is a strange opener for a tool whose pitch is that every claim is checkable |
| "you take the reins" | "you make the call" | the actual mantra, and sharper |
| "Open **Squad Lab**" | "In My Squad, open the **Lab**" | ADR-166 folded it in from the sidebar |
| "set your budget, **formation**, strategy, and objectives" | "your budget, what to optimise for, and how strong you want your bench" | **Formation is not a build input** — it is a *preview* control ("preview the best XI in a shape"). The real inputs are budget · objective · build mode · archetypes |
| "complete **transfers**" *(in the My Squad beat)* | moved into the *This week* answer | ADR-115 moved the transfer picker off that screen to its own tab; the script had it in the wrong place |
| — | "the whole week on one screen" | **ADR-171**, and the strongest beat in the product — the old script did not mention the gameweek answer at all |
| "discover differentials" | "Scout … names the players worth a look" | ADR-167. Say **worth a look, not worth points** — two of Scout's signals are not priced into xP, and the counterweight is the claim |
| "Analytics decide. **AI explains.** You make the call." | the current mantra | ADR-168 |

---

## 1 · The explainer — hero cut, ~2:27  *(drafted 2026-08-13; **re-cut 2026-08-31** for ADR-166/168/171)*

> **[Hook – 0:00]** Fantasy Premier League is drowning in hot takes and AI that just… guesses. MADBOOTS is
> different: **the analytics decide — and every answer shows its working**, so you always know what to trust.
> *(UI: the ✓/⚠ trust line.)*
>
> **[0:12 – Build or import]** Getting started takes seconds. In **My Squad**, open the **Lab**: set your
> budget and strategy, and MADBOOTS builds your optimal 15. Already play FPL? **Import your real team with
> your manager ID.** One tap — it's your active squad.
>
> **[0:30 – Your week, answered]** Then **My Squad opens on the answer**: who to captain, any lineup change,
> the one transfer worth making, and the players to watch — each with the **Edge** for it, the **Risk**
> against, and a confidence score. *(UI: the* This week *block at the top of My Squad.)*
>
> **[0:50 – The pitch]** Below it, your team on a live pitch — set your captain, make subs, set your bench,
> legality checked as you go. Tap any player for a rich card: form, expected points, fixtures, set-pieces.
> Torn between two? **Boot Battle** puts them head-to-head and highlights the winner, stat by stat. Then your
> captaincy options ranked, and when to play each chip.
>
> **[1:16 – Research]** Want to go deeper? **Scout** reads five stat boards at once and names the players
> **worth a look**. **Radar** finds the form buys from the easiest fixture runs. **Team DNA** grades every
> club at both ends. And **Trending** and **Signals** keep what the crowd is *doing* separate from what is
> being *said*.
>
> **[1:38 – Leagues]** Then take it to your mini-league. **Leagues** shows effective ownership, the captain
> split, and a head-to-head that prices only the players you *don't* share — because the ones you both own
> cancel out.
>
> **[1:52 – Close + CTA]** No paid black boxes. No AI guessing. Just honest analytics you can check. **The
> analytics decide. Every answer shows its working. You make the call.** Try MADBOOTS **free** at
> **madboots.com**.

**Accuracy anchors:** the Lab is a My Squad tab (ADR-166); *This week* leads the golden page (ADR-171); Scout
= five boards behind a *worth a look* shortlist (ADR-167) — **never "worth points"**, two of its signals are
unpriced; Team DNA is its own page since the FDR split (ADR-169); Trending-vs-Signals is the *doing vs saying*
axis (ADR-149/150); the H2H decomposition is ADR-161 — **the win-probability half is gated and must not be
claimed**.

**What changed from the 2026-08-13 draft:** the **Ask** beat (1:32) is gone — ADR-168 retired the page — and
its slot went to **Leagues**, a real differentiator that had no marketing at all. **AI Tips** stopped being a
separate destination and became the top of My Squad, which also fixed an ordering problem: the old cut showed
the pitch first and the answer twenty seconds later, which is not how the app works or how the week is
decided.

---

## 2 · The explainer — 60-second social cut  *(drafted 2026-08-13; **re-cut 2026-08-31**)*

> **[0:00 – Hook]** Fantasy Premier League, minus the guesswork. MADBOOTS is the FPL assistant where **the
> analytics decide** — and every answer shows its working. *(UI: the ✓/⚠ line.)*
>
> **[0:10 – Build / import]** Build your optimal squad in **My Squad ▸ Lab** — or **import your real team**
> with your manager ID. One tap and it's live.
>
> **[0:20 – Your week, answered]** Short on time? **My Squad opens on the answer**: who to captain, the
> transfer worth making, the players to watch — each with the **Edge** for it, the **Risk** against, and a
> confidence score.
>
> **[0:35 – Boot Battle]** Torn between two players? **Boot Battle** puts them head-to-head and highlights the
> winner, stat by stat. *(UI: the two-player compare card.)*
>
> **[0:44 – Scout]** And when you're hunting? **Scout** reads five stat boards at once and names the players
> **worth a look**.
>
> **[0:52 – Close + CTA]** Honest analytics. No guessing. **Try MADBOOTS free at madboots.com.**

*(~150 words ≈ 60s. Trim the **Scout** beat first if it runs long — it replaced the retired **Ask** beat,
which used to carry that instruction.)*

---

## ✅ Audit — closed 2026-08-31: every script re-cut against the app

Every script here predated the app it described. Found while revising §0; all of it actioned the same day,
before production, which is the only reason it was cheap.

| what the scripts said | what the app does | since | fixed |
|---|---|---|---|
| six sign-offs closed on *"The AI explains"* | there is no AI on Cloud; the mantra is *"Every answer shows its working"* | ADR-168 | ✅ all six, plus the file's own throughline |
| **§8 was a full 45s script for "Ask Anything"**, and Ask featured in §1 (1:32), §2 (0:44), §5 (0:24) | **Ask is retired** — owner-gated in Admin, not a user surface | ADR-168 | ✅ §8 → **Leagues & Head-to-Head**; the draft archived as §8b with its trigger |
| **Squad Lab** was a destination (§1, §2, §6, series row A, clips 2 & 4) | it is **My Squad ▸ Lab** | ADR-166 | ✅ |
| **AI Tips** was a destination (§1, §2, §7, series row B, clip 9) | it is *This week*, at the top of My Squad, rendering **on load** | ADR-171 | ✅ §7 retitled *Your Week, Answered* — the hook is now *"before you ask"*, which is better than the tap it replaced |
| §6 listed **three build modes** (Balanced/Weekly/Bench Boost) | **two**: All-round (strong bench) · Strong XI (cheap bench) | ADR-137 | ✅ |
| clip 12 said *"Fixtures"*, clip 14 *"News"* | FDR + Team DNA are separate pages; News is Signals | ADR-150/169 | ✅ |
| **nothing mentioned Scout, Worth noticing, Team DNA, Leagues or head-to-head** | all shipped, all differentiators | ADR-141/161/167/169/170 | ✅ all five now have beats and shots |

**Two claims deliberately withheld.** Scout is *worth a look*, **never** *worth points* — two of its signals
are unpriced (ADR-167). And no script may offer a **win probability**: ADR-161 measured it as a coin flip
(gap sd ≈ 8.6 against margins of 2-5) and gated it, so selling it would market the one thing we refused to
ship.

One smaller note: the CTA *"free at madboots.com"* is wrong for the in-app **Maddie Explains** hub, where the
viewer is already inside the app — that tail wants a second cut. *(An earlier version of this audit said §5
used the US spelling "analyze". It does not — that was in the **produced §0 script**, and the rewrite drops
it. Corrected 2026-08-31.)*

---

## 3 · The series roadmap  *(owner-planned + candidates; **re-cut 2026-08-31**)*

One feature/idea per short (30–45s for Reels/TikTok/Shorts); each ends on the same trust line + CTA.

| # | Title | Angle | Status |
|---|-------|-------|--------|
| A | **Build the Perfect Squad** *(My Squad ▸ Lab)* | Budget · objective · archetypes · build modes → an optimised 15 in seconds; "Use this squad →". A wildcard/season-start hook. | **drafted (§6)** |
| B | **Your Week, Answered** *(This week + Transfers)* | The whole gameweek plan the moment the page opens, then transfers ranked by XI improvement; Apply-this-plan. Edge/Risk/Confidence on show. | **drafted (§7)** |
| C | ~~**Ask Anything**~~ → **Leagues & Head-to-Head** | *Replaced.* Ask was retired (ADR-168). The slot goes to the mini-league layer: effective ownership · captain split · a head-to-head that prices only your differentials. | **drafted (§8)** |
| D | **Finding Differentials** 💎 | *Educational + trust.* Low-owned + the underlying data → a real edge; Scout, Trending's *Worth noticing*, and Radar. (Searchable topic.) | **drafted (§5)** |
| E | **Understanding xP & Confidence** | *Educational + trust — the moat piece.* What Expected Points is, and why our number is honest (grounded, ✓/⚠, no paid black box). | **drafted (§4)** |
| F | **Boot Battle** ⚔️ | The most visual + shareable: two same-position players head-to-head, the better stat tinted. My-team / All / By-club. | **drafted (§9)** |
| G | **Scout — worth a look** *(candidate)* | Five stat boards become one shortlist. The honest hook is the counterweight: *worth a look, **not** worth points* — two signals are unpriced. | *candidate* |
| H | **Team DNA** *(candidate)* | Every club graded at both ends on an eight-axis fingerprint, and the players to target there. Highly visual (the radar). | *candidate* |

**Suggested order to shoot:** F (most visual, easy win) → B (the "wow") → A → C → D → E (the educational two
anchor the brand and age well). G and H are the strongest un-scripted candidates — both shipped, both
differentiators, neither mentioned in any cut before 2026-08-31.

---

## 4 · Understanding xP & Confidence — short (~55s)  *(drafted 2026-08-13; sign-off updated 2026-08-31 — the moat/educational piece)*

> **[0:00 – Hook]** Fantasy Premier League comes down to points — but the points haven't happened yet. So how do you
> choose between two players?
>
> **[0:09 – xP]** That's **Expected Points — xP**: MADBOOTS's honest projection of how many points a player is
> *likely* to score, built from the real numbers — minutes, chances created, fixtures, form. One number, so you can
> compare anyone at a glance. *(UI: the player card's xP chip + the per-GW row.)*
>
> **[0:26 – Confidence]** But a number alone can mislead. So every pick comes with a **Confidence** score — how
> strongly the data actually backs it — plus the **Edge** for it, and the **Risk** against. *(UI: the
> Confidence · Edge · Risk block.)*
>
> **[0:40 – The honesty]** And here's the difference: it's a heuristic, not a crystal ball. A "Medium" means a
> *lean, not a lock* — and the ⚠ risk is right there. Every figure traces back to the data, with a ✓ when it's
> verified. No paid black box. No guessing.
>
> **[0:53 – Close + CTA]** Expected Points you can actually trust. **The analytics decide. Every answer shows its working. You make the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors (all true to the app):** xP = one honest number from `decision_xp` (minutes-weighted · xGI ·
fixtures · form), ADR-041's one-xP-metric. Confidence · Edge · Risk = the explainability block (ADR-089) — a
**heuristic, not a probability** (the honest framing). "Traces to the data · ✓" = the grounding check (ADR-037). "No
paid black box" = the real position (no bought Opta; analytics decide, not an LLM guessing).

**Creative note:** the differentiator is **selling the uncertainty as a feature** — "a lean, not a lock, and here's
the risk." Everyone else projects false certainty; the honest confidence score is the heart of the brand.

---

## 5 · Finding Differentials — short (~50s)  *(drafted 2026-08-13; **re-cut 2026-08-31**; pairs with §4)*

> **[0:00 – Hook]** Everyone owns the same big names. To climb your mini-league, you need the players your rivals
> *don't* have — **differentials**.
>
> **[0:10 – What]** A differential is a low-owned player — often under a few percent. When they haul, you gain rank on
> everyone who missed them. But most low-owned players are low-owned for a reason — the trick is finding the *good*
> ones. *(UI: the 💎 ownership tier.)*
>
> **[0:24 – How]** MADBOOTS crosses ownership with the underlying data — three ways. **Scout** names the
> players standing out on two or more stat boards at once. **Trending's** *Worth noticing* finds the ones
> **in form but still under-owned** — which is the definition of a differential, spotted before the crowd
> catches up. And **Radar** finds hidden value from the easiest fixture runs. *(UI: Scout's shortlist;
> Trending's* Worth noticing *strip; Radar.)*
>
> **[0:42 – The edge]** Because a differential's only an edge if the numbers back it. MADBOOTS shows you the ones that
> are low-owned *and* genuinely good — a real edge, not a punt.
>
> **[0:52 – Close + CTA]** Find your edge. **The analytics decide. Every answer shows its working. You make the call.** Try MADBOOTS
> **free** at **madboots.com**.

**Accuracy anchors:** 💎 = low ownership (`ownership_tier`); **Scout** = five boards behind a *worth a look*
shortlist (ADR-167); **Worth noticing** = *in form, still under-owned* is one of its three named patterns, and
every threshold it uses is an existing calibrated constant (ADR-170); **Radar** = best value from the
easiest-run teams (`targets.py`). The honesty hook (*"low-owned **and** good"*) holds because crowd/ownership
is only ever a **lens**, never `decision_xp` (the invariance rule) — a MADBOOTS differential is one the
grounded xP supports. ⚠ Scout is *worth a look*, **not** *worth points*: say the former.
*(Re-cut 2026-08-31 — the old 0:24 beat routed through **Ask**, retired by ADR-168.)*

**Pairing:** §4 (xP & Confidence) teaches *"trust the number"*; §5 shows *"use it to win"* — a one-two.

---

## 6 · Build the Perfect Squad — short (~50s)  *(drafted 2026-08-13; **re-cut 2026-08-31**; My Squad ▸ Lab)*

> **[0:00 – Hook]** New season? Wildcard burning a hole? Fitting 15 players under budget is a puzzle — MADBOOTS solves
> it in seconds.
>
> **[0:10 – Controls]** In **My Squad**, open the **Lab**. Set your budget, pick what to optimise for —
> **expected points, value, or goal threat** — add a strategy (cheap enablers, premium-heavy, or
> differentials), choose whether you want an **all-round squad or a strong XI with a cheap bench**, and lock
> in your must-haves. *(UI: the Lab controls.)*
>
> **[0:28 – Build]** Hit build, and MADBOOTS returns your **optimal 15** — the best squad your money can buy, every
> position filled.
>
> **[0:38 – Use it]** Love it? **Use this squad →** and it's your active team. Or download it as a backup.
>
> **[0:48 – Close + CTA]** Your perfect squad, built on the data. **The analytics decide. Every answer shows its working. You make the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** the ILP optimiser (ADR-008); the **objective** toggle xP/Points/Value/xGI (ADR-011);
**archetypes** cheap/premium/differential; include/exclude must-haves (ADR-009); **Use this squad →** +
Download. ⚠ **Build modes are two, not three** — *All-round (strong bench)* and *Strong XI (cheap bench)*.
ADR-137 renamed them because *"weaker bench"* was the misleading word: the cheap bench is deliberate, bought
so the money goes into the XI. Playing Bench Boost? That is **All-round**, not a third mode.
*(Re-cut 2026-08-31 — the Lab is a My Squad tab since ADR-166, and this anchor still listed the old modes.)*

---

## 7 · Your Week, Answered — short (~50s)  *(drafted 2026-08-13 as "Master AI Tips & Transfers"; **re-cut 2026-08-31**)*

> **[0:00 – Hook]** Every gameweek, the same questions: who to captain, who to bring in, who to bench.
> **MADBOOTS answers all of them — before you ask.**
>
> **[0:10 – The plan]** Open **My Squad** and the answer is already there: **who to captain**, any **lineup
> change**, the **one transfer** worth making, and the **players to watch** — each with the **Edge** for it
> and the **Risk** against, all checked against the data. *(UI: the* This week *block, on load.)*
>
> **[0:30 – Transfers]** Going further? MADBOOTS ranks every transfer by how much it **improves your starting
> XI** — set your bank, get a coordinated two- or three-move plan, and **apply it in one tap**.
>
> **[0:45 – Close + CTA]** Your sharpest gameweek, sorted. **The analytics decide. Every answer shows its
> working. You make the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** the gameweek plan (ADR-070); Edge · Risk · Confidence (ADR-089) + ✓/⚠ grounding
(ADR-037); transfers ranked by **XI improvement**, the bank slider, a coordinated 2–3 plan + **Apply this
plan →** (ADR-055/046).

**What changed:** the old cut said *"One tap gives your full gameweek plan"* and treated **AI Tips** as a
destination. ADR-171 moved it to the top of My Squad and it renders **on load** — 123 ms on the deployed app,
because there is no model to wait for. *"Before you ask"* is now literally true, and it is a better hook than
the tap it replaced.

---

## 8 · Leagues & Head-to-Head — short (~45s)  *(**new 2026-08-31**, replacing the retired "Ask Anything")*

> **[0:00 – Hook]** You're not playing against the game. You're playing against the twelve people in your
> mini-league.
>
> **[0:08 – Import]** Import your league and MADBOOTS shows you the table — then goes past it: **effective
> ownership** against the global crowd, who the group is captaining, and where the transfers are flowing.
> *(UI: the league scan; tap any row.)*
>
> **[0:24 – Head-to-head]** Pick a rival, and here's the part that matters: **the players you both own
> cancel.** MADBOOTS prices only the ones you *don't* share — so you can see exactly where the gap will
> actually come from. *(UI: the H2H differential set.)*
>
> **[0:38 – Close + CTA]** Know your rivals, not just your team. **The analytics decide. Every answer shows
> its working. You make the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** league import + effective ownership / captain split / transfer flow (ADR-141); the H2H
**decomposition** — the shared players cancel, the differential set is priced (ADR-161); tap-a-row to select
(ADR-158).

⚠ **Do not claim a win probability.** ADR-161 built the decomposition and **gated the simulation on
evidence**: one starter's points have **sd 3.51**, and a three-differential head-to-head has a gap **sd ≈ 8.6**
against typical margins of 2-5 points — it would say *"it's close"* every single week. Saying *"your odds"*
would sell the one thing we measured and refused to ship.

---

## 8b · ~~Ask Anything~~ — ❌ **RETIRED, not produced**  *(drafted 2026-08-13; retired 2026-08-31)*

**Why it is kept here rather than deleted:** a parked idea with a recorded reason is worth more than a
forgotten one, and this one has a live trigger. **ADR-168 retired Ask as a page** — *"Ask is not being used"*,
and there is **no AI on Cloud**, so the written paragraph the script sold was the one thing a deployed viewer
would never get. The feature survives owner-gated in Admin, with a decision point at the **GW4-6 calibration
sitting**; if it comes back as a user surface, this draft is the starting point — but the *"just ask, in plain
English"* framing would still need re-checking against what the hosted app can actually do.

**The half worth salvaging:** its real subject was never the text box, it was the **honest third state** —
*data-verified* versus *general guidance, clearly labelled*. That idea is alive and shipping everywhere (the
✓/⚠ line, ADR-085's *"not checked against your data"*), and §4 already carries it better.

---

## 9 · Boot Battle ⚔️ — short (~40s)  *(drafted 2026-08-13; sign-off updated 2026-08-31; the most visual/shareable)*

> **[0:00 – Hook]** Two players, one spot — who gets in? Settle it with a **Boot Battle**.
>
> **[0:08 – What]** Pick any player, choose a rival in the same position, and MADBOOTS puts them **head-to-head** —
> points, goals, expected points, form, fixtures — highlighting the winner, stat by stat. *(UI: the two-player
> compare card, winners tinted teal.)*
>
> **[0:24 – Where]** Compare anyone — your own squad, the whole league, or a specific club — right from any player
> card.
>
> **[0:32 – Close + CTA]** Stop guessing. Let the stats fight it out. **The analytics decide. Every answer
> shows its working. You make the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** the same-position compare card (ADR-110), winner-tinted per stat (`_BETTER` direction map),
from any Player Card on **Players + My Squad**; the **pool selector** My team / All / By club (ADR-111, US-380).

---

## Presenter avatar — generation brief

**Decision:** a **MADBOOTS mascot** presenter (not an AI human) + a **strong female voice**. For it to "present"
(lip-sync in HeyGen Talking Photo) it needs a **face**; else use it as a brand element + VO over UI.

**Image-gen prompt** (Midjourney / DALL·E / Ideogram):
> *Mascot character for a football-analytics brand called MADBOOTS. A confident, friendly **female** character,
> modern minimalist sporty-tech style — flat vector illustration, premium and trustworthy (not childish, not
> photorealistic). Brand colours **deep purple #8B2FC9** and **vibrant orange #FF6A00** on a dark background.
> Football-boots motif in her outfit; a small "MB" badge emblem. **Front-facing head-and-shoulders, clear expressive
> face, mouth visible, neutral confident expression, even studio lighting** — suitable for animation and lip-sync.
> Clean, high detail on the face.*

Generate **three framings**, same character throughout: (a) head-and-shoulders, front-on, mouth-closed neutral →
**HeyGen Talking Photo**; (b) full-body → intro; (c) badge/logo lockup → end-card. Reuse the existing MB badge as the
secondary mark, not the presenter.

---

## Shot lists — record a clip **library** once, reuse across videos

Same UI moments recur, so record ~15 clips **once** (5–8s each, the **live** app, slow deliberate actions, freshly
reseeded data) and reuse. *(Manager-ID import only films properly post-GW1 — 21 Aug 2026.)*

**Clip library** *(re-cut 2026-08-31 — six of these named a surface that has moved or gone):*
1. **Trust line** — the ✓/⚠ under any grounded answer (the *This week* block is the easiest to film).
2. **The Lab — build** — My Squad ▸ Lab: set budget/objective/archetypes/build mode → build → the 15.
3. **Use this squad → / Download.**
4. **Manager-ID import** — the **⚙ Your team** panel on My Squad.
5. **My Squad pitch** — the green formation, kits, xP chips, (C).
6. **Player card** — the xP chip + the per-GW row + stats/trends.
7. **Boot Battle** — pick a player → the winner-tinted compare card → the **pool selector** (My team/All/By club).
8. **Make captain / Substitute** — the ⚙ panel controls.
9. **This week** — captain · lineup · transfer · flags + **Edge/Risk/Confidence**, *rendering on page load*.
10. **Transfer** — rank by **XI improvement** + bank slider + coordinated plan + **Apply this plan →**.
11. **Scout** — the *worth a look* shortlist, then the board selector behind it.
12. **FDR** — the difficulty ticker · **Team DNA** — the eight-axis club radar · **🎯 Radar** (a Players view).
13. **Trending** — the 👀 *Worth noticing* strip, then the four crowd boards.
14. **Signals** — official news → an unexplained exodus → headlines, in that order (the evidence ladder).
15. **Leagues** — the league scan, tap a row, then the **head-to-head** differential set.

**Per-video (which library clips):**
- **§0 Maddie intro:** 2,3 → 9 → 5,6,7 → 11 → 15.
- **2-min explainer:** 1 → 2,3,4 → 9 → 5,6,7 → 11,12,13,14 → 15.
- **60-sec cut:** 1 → 2,4 → 9 → 7 → 11.
- **§4 xP & Confidence:** 6 (xP chip + per-GW) → 9 (Confidence·Edge·Risk).
- **§5 Finding Differentials:** 11 (Scout) → 13 (Worth noticing) → 12 (Radar).
- **§6 Build:** 2 (the controls + build) → 3.
- **§7 Your Week, Answered:** 9 → 10.
- **§8 Leagues & Head-to-Head:** 15.
- **§9 Boot Battle:** 7 (pick → compare card → pool selector).

**What changed:** clip 1 filmed an **Ask** answer and clip 15 was **Ask** itself (retired, ADR-168); clip 2
said *"Squad Lab"* and clip 4 *"the Squads sidebar"* (both ADR-166); clip 9 was *"AI Tips"* as a destination
(ADR-171); clip 12 said *"Fixtures"*, a page ADR-169 split in two; clip 14 said *"News"*, renamed Signals by
ADR-150. Clips 11, 13, 14 and 15 now cover Scout, Worth noticing, the evidence ladder and Leagues — four
shipped differentiators with no shot list at all before today.

---

## Production workflow (HeyGen — $2/7-day trial; any builder works)

⚠️ **HeyGen is built for realistic human avatars, not a stylised mascot.** Its **Talking Photo** can lip-sync a
mascot **only if it has a face** (use the head-and-shoulders render above). If it doesn't animate well, use HeyGen for
the **voice + assembly** and keep the mascot as a brand element (intro/outro/corner) over **VO-on-UI**.

1. **Create video → Landscape** (16:9; also export a 9:16 crop for Reels/TikTok/Shorts).
2. **Uploads tab → drag in your screen-recording clips.**
3. **Scene by scene:** *intro* = mascot Talking Photo (or logo) + hook; *body* = each `(UI:…)` beat as a scene with
   the **uploaded UI clip full-screen** + the script line in the **script box** with your chosen **voice** (optional
   avatar **PiP** in a corner); *outro* = mascot + CTA end-card (**madboots.com · free**).
4. **Voice:** a strong female voice (HeyGen library, or its ElevenLabs integration).
5. **Auto-captions on** (social is watched muted; the trust lines must land on screen).
6. **Export**, then a **9:16** version for shorts. Keep a **consistent intro/outro + music** across all videos.

---

## Video assets (rendered)

- **Presenter avatar:** ✅ generated (owner, 2026-08-13) — a female MADBOOTS mascot in the brand tracksuit (MB badge +
  boot motif, analytics-ring background), front-facing/clear face → suitable for HeyGen Talking Photo. *To-do:* a
  tighter face crop + a **transparent-background cut-out** for corner-PiP compositing.
- **Hero-shots page** → <https://claude.ai/code/artifact/308e74eb-40bf-43e7-bff6-52eaf6d97ca2>
  (video-ready cards, real data — screenshot/screen-record each): Boot Battle (two forwards **&** two midfielders) ·
  Player Card (a forward **&** a defender, position-adaptive stats) · Captain trust block (Confidence·Edge·Risk) ·
  **AI-Tips gameweek plan** (§7 still) · Differentials board (§5). Rendered from the app's own renderers.
  *Toggle your device light/dark theme for a light-background variant.*
  *(Private Claude artifact; regenerate any time from the app renderers + live DB.)*
- **Photos:** the card renders use silhouette stand-ins (real player photos are CDN-blocked in the render) — capture
  photo-heavy shots (the big player-card headshot, the pitch kits) from the **live app**.

## Landing-page "See how it works" → the Maddie intro — ✅ WIRED (2026-08-18)

**Done:** on **madboots.com** (`~/madboots-site/index.html`, not a git repo — deploy via Cloudflare Pages), the hero
**"See how it works"** button now opens a **self-contained lightbox** that plays the **Maddie intro**
(`https://youtu.be/a7WG0MBDLFg`, autoplay, closes on outside-click / ✕ / Esc; `href="#why"` kept as a no-JS
fallback). Same clip can seed the in-app **Maddie Explains** (`maddie_videos`, BETA.md §6). *Owner: preview by
opening `index.html` locally, then deploy.* — The 90-sec-or-less explainer series (owner marketing goal).

*(Original idea, 2026-08-15 — a short video on a landing hero is a proven conversion beat:)*
- **Recommended:** a **lightbox/modal** that plays the unlisted-YouTube embed on click (keeps the visitor *on* the
  landing page — no navigation away, plays immediately). Prefer this over a raw link-out to YouTube (which loses them)
  or an inline scroll-to-embed (fine, but a modal reads as more deliberate for a hero CTA).
- **Reuses the same URL** as the app hub — the one unlisted-YouTube link that goes in `maddie_videos` (BETA.md §6).
- **Blocked on the same thing:** needs the explainer *hosted* first (paid HeyGen → download → unlisted YouTube). Until
  then leave the current scroll behaviour. Wire it when the video's live (a small `index.html` edit on `madboots-site`).
