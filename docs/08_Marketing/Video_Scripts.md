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

## 1 · The explainer — 2-minute hero cut  *(status: drafted 2026-08-13)*

> **[Hook – 0:00]** Fantasy Premier League is drowning in hot takes and AI that just… guesses. MADBOOTS is different:
> **the analytics decide — and every call is checked against real data**, so you always know what to trust.
> *(UI: the ✓/⚠ trust line.)*
>
> **[0:12 – Build or import]** Getting started takes seconds. In **Squad Lab**, set your budget and strategy and
> MADBOOTS builds your optimal 15. Already play FPL? **Import your real team with your manager ID.** One tap — it's
> your active squad.
>
> **[0:30 – My Squad]** **My Squad** is your team on a live pitch — set your captain, make subs, plan transfers, all
> with legality checked as you go. Tap any player for a rich card: form, expected points, fixtures, set-pieces. Torn
> between two? **Boot Battle** puts them head-to-head and highlights the winner, stat by stat.
>
> **[0:50 – AI Tips]** Short on time? **AI Tips** gives your whole gameweek in seconds — who to captain, any lineup
> change, the one transfer worth making, and the injuries to watch — each with the **Edge** for it, the **Risk**
> against, and a confidence score. All checked against the data.
>
> **[1:12 – Research]** Want to go deeper? Explore every player, rate them against each other, scan fixture
> difficulty, and use **Radar** to find the form buys from the easiest runs — plus transfer trends and injury news.
>
> **[1:32 – Ask]** Or just **ask**, in plain English: *"Who should I captain?" … "Build me a squad with three
> differentials." … "How does Bench Boost work?"* MADBOOTS routes every question — and tells you when it's
> **data-verified** versus general guidance.
>
> **[1:50 – Close + CTA]** No paid black boxes. No AI guessing. Just honest analytics you can check. **The analytics
> decide. The AI explains. You make the call.** Try MADBOOTS **free** at **madboots.com**.

---

## 2 · The explainer — 60-second social cut  *(status: drafted 2026-08-13)*

> **[0:00 – Hook]** Fantasy Premier League, minus the guesswork. MADBOOTS is the FPL assistant where **the analytics
> decide** — and every call is checked against real data. *(UI: the ✓/⚠ line.)*
>
> **[0:10 – Build / import]** Build your optimal squad in **Squad Lab** — or **import your real team** with your
> manager ID. One tap and it's live.
>
> **[0:20 – AI Tips]** Short on time? **AI Tips** gives your whole gameweek in seconds: who to captain, the transfer
> worth making, the injuries to watch — each with the **Edge** for it, the **Risk** against, and a confidence score.
>
> **[0:35 – Boot Battle]** Torn between two players? **Boot Battle** puts them head-to-head and highlights the winner,
> stat by stat. *(UI: the two-player compare card.)*
>
> **[0:44 – Ask]** Or just **ask** — *"Who should I captain?"* — and MADBOOTS tells you when the answer's
> **data-verified**.
>
> **[0:52 – Close + CTA]** Honest analytics. No guessing. **Try MADBOOTS free at madboots.com.**

*(~150 words ≈ 60s at a natural pace. Trim the Ask beat first if it runs long.)*

---

## ⚠️ Audit — every script below §2 predates the app it describes  *(2026-08-31)*

Found while revising §0. **None of §§1-9 have been produced**, so this is cheap now and expensive after nine
renders. Each needs the same pass §0 just had:

| what the scripts say | what the app does | since |
|---|---|---|
| six sign-offs close on *"The AI explains"* | there is no AI on Cloud; the mantra is *"Every answer shows its working"* | ADR-168 |
| **§8 is a full 45s script for "Ask Anything"**, and Ask features in §1 (1:32) and §2 (0:44) | **Ask is retired** — owner-gated in Admin, not a user surface | ADR-168 |
| **Squad Lab** is a destination (§1, §2, §6, series row A) | it is **My Squad ▸ Lab** | ADR-166 |
| **AI Tips** is a destination (§1, §2, §7, series row B) | it is the *This week* section at the top of My Squad | ADR-171 |
| research beats list the five stat boards separately (§5) | they are one **Scout** view behind a shortlist | ADR-167 |
| no script mentions Scout, Worth noticing, Team DNA, Leagues or head-to-head | all shipped and all differentiators | ADR-141/161/167/169/170 |

Two smaller notes: §5 uses *"analyze"* where the rest of the project is British (`analyse` is the CLI command
name), and the CTA *"free at madboots.com"* is wrong for the in-app **Maddie Explains** hub, where the viewer
is already inside the app — that tail wants a second cut.

---

## 3 · The series roadmap  *(owner-planned + candidates)*

One feature/idea per short (30–45s for Reels/TikTok/Shorts); each ends on the same trust line + CTA.

| # | Title | Angle | Status |
|---|-------|-------|--------|
| A | **Build the Perfect Squad** *(Squad Lab)* | Budget · objective · archetypes · build modes → an optimised 15 in seconds; "Use this squad →". A wildcard/season-start hook. | **drafted (§6)** |
| B | **Master AI Tips & Transfers** | The whole gameweek plan in seconds + ranking transfers by XI improvement; Apply-this-plan. Edge/Risk/Confidence on show. | **drafted (§7)** |
| C | **Ask Anything** *(natural language)* | Type plain-English questions → routed + **data-verified** (vs clearly-labelled general guidance). Shows the ✓/⚠. | **drafted (§8)** |
| D | **Finding Differentials** 💎 | *Educational + trust.* Low-owned + set-piece/xGI → a differential edge; Radar + the ownership steer. (Searchable topic.) | **drafted (§5)** |
| E | **Understanding xP & Confidence** | *Educational + trust — the moat piece.* What Expected Points is, and why our number is honest (grounded, ✓/⚠, no paid black box). | **drafted (§4)** |
| F | **Boot Battle** ⚔️ *(candidate — Claude's add)* | The most visual + shareable: two same-position players head-to-head, the better stat tinted. My-team / All / By-club. | **drafted (§9)** |

**Suggested order to shoot:** F (most visual, easy win) → B (the "wow") → A → C → D → E (the educational two anchor
the brand and age well). Draft each here before producing.

---

## 4 · Understanding xP & Confidence — short (~55s)  *(status: drafted 2026-08-13 — the moat/educational piece)*

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
> **[0:53 – Close + CTA]** Expected Points you can actually trust. **The analytics decide. The AI explains. You make
> the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors (all true to the app):** xP = one honest number from `decision_xp` (minutes-weighted · xGI ·
fixtures · form), ADR-041's one-xP-metric. Confidence · Edge · Risk = the explainability block (ADR-089) — a
**heuristic, not a probability** (the honest framing). "Traces to the data · ✓" = the grounding check (ADR-037). "No
paid black box" = the real position (no bought Opta; analytics decide, not an LLM guessing).

**Creative note:** the differentiator is **selling the uncertainty as a feature** — "a lean, not a lock, and here's
the risk." Everyone else projects false certainty; the honest confidence score is the heart of the brand.

---

## 5 · Finding Differentials — short (~50s)  *(status: drafted 2026-08-13 — educational/searchable; pairs with §4)*

> **[0:00 – Hook]** Everyone owns the same big names. To climb your mini-league, you need the players your rivals
> *don't* have — **differentials**.
>
> **[0:10 – What]** A differential is a low-owned player — often under a few percent. When they haul, you gain rank on
> everyone who missed them. But most low-owned players are low-owned for a reason — the trick is finding the *good*
> ones. *(UI: the 💎 ownership tier.)*
>
> **[0:24 – How]** MADBOOTS crosses ownership with the underlying data. Sort the player pool by ownership to surface
> under-owned takers and in-form picks. Use **Radar** to find hidden value from the easiest fixtures. Or just ask:
> *"Best differential midfielders under £8m"* — or *"Build me a squad with three differentials."* *(UI: Players sorted
> by Own%; Radar; the Ask query.)*
>
> **[0:42 – The edge]** Because a differential's only an edge if the numbers back it. MADBOOTS shows you the ones that
> are low-owned *and* genuinely good — a real edge, not a punt.
>
> **[0:52 – Close + CTA]** Find your edge. **The analytics decide. The AI explains. You make the call.** Try MADBOOTS
> **free** at **madboots.com**.

**Accuracy anchors:** 💎 = low ownership (`ownership_tier`); "sort by Own% to surface under-owned takers" = the
Set-pieces view; **Radar** = best value from the easiest-run teams (`targets.py`); both Ask lines are real Help
examples. The honesty hook (*"low-owned **and** good"*) holds because crowd/ownership is only ever a **lens**, never
`decision_xp` (the invariance rule) — a MADBOOTS differential is one the grounded xP supports.

**Pairing:** §4 (xP & Confidence) teaches *"trust the number"*; §5 shows *"use it to win"* — a one-two.

---

## 6 · Build the Perfect Squad — short (~50s)  *(status: drafted 2026-08-13; Squad Lab)*

> **[0:00 – Hook]** New season? Wildcard burning a hole? Fitting 15 players under budget is a puzzle — MADBOOTS solves
> it in seconds.
>
> **[0:10 – Controls]** Open **Squad Lab**. Set your budget, pick what to optimise for — **expected points, value, or
> goal threat** — add a strategy (cheap enablers, premium-heavy, or differentials), and lock in your must-haves.
> *(UI: the Squad Lab controls.)*
>
> **[0:28 – Build]** Hit build, and MADBOOTS returns your **optimal 15** — the best squad your money can buy, every
> position filled.
>
> **[0:38 – Use it]** Love it? **Use this squad →** and it's your active team. Or download it as a backup.
>
> **[0:48 – Close + CTA]** Your perfect squad, built on the data. **The analytics decide. The AI explains. You make
> the call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** the ILP optimiser (ADR-008); the **objective** toggle xP/Points/Value/xGI (ADR-011);
**archetypes** cheap/premium/differential; include/exclude must-haves (ADR-009); **build modes**
(Balanced/Weekly/Bench Boost); **Use this squad →** + Download.

---

## 7 · Master AI Tips & Transfers — short (~50s)  *(status: drafted 2026-08-13)*

> **[0:00 – Hook]** Every gameweek, the same questions: who to captain, who to bring in, who to bench. **AI Tips**
> answers all of them — in seconds.
>
> **[0:10 – The plan]** One tap gives your full gameweek plan: **who to captain**, any **lineup change**, the **one
> transfer** worth making, and the **injuries** to watch — each with the **Edge** for it and the **Risk** against,
> all checked against the data. *(UI: the AI-Tips plan block.)*
>
> **[0:30 – Transfers]** Going further? MADBOOTS ranks every transfer by how much it **improves your starting XI** —
> set your bank, get a coordinated two- or three-move plan, and **apply it in one tap**.
>
> **[0:45 – Close + CTA]** Your sharpest gameweek, sorted. **The analytics decide. The AI explains. You make the
> call.** Try MADBOOTS **free** at **madboots.com**.

**Accuracy anchors:** the gameweek plan (ADR-070); Edge · Risk · Confidence (ADR-089) + ✓/⚠ grounding (ADR-037);
transfers ranked by **XI improvement**, the bank slider, a coordinated 2–3 plan + **Apply this plan →** (ADR-055/046).

---

## 8 · Ask Anything — short (~45s)  *(status: drafted 2026-08-13)*

> **[0:00 – Hook]** Don't want to click through menus? Just **ask** — in plain English.
>
> **[0:10 – Examples]** *"Who should I captain?" … "Best differential midfielders under £8m." … "Build me a squad
> with three differentials." … "How does Bench Boost work?"* MADBOOTS understands, and routes each question to the
> right place. *(UI: the Ask box + a grounded answer.)*
>
> **[0:28 – The trust twist]** And here's what matters: it tells you when an answer is **data-verified** — checked
> against the numbers — versus general football guidance. No pretending. You always know what to trust.
>
> **[0:42 – Close + CTA]** Just ask. **The analytics decide. The AI explains. You make the call.** Try MADBOOTS
> **free** at **madboots.com**.

**Accuracy anchors:** intent routing (ADR-034); grounded answers with the ✓/⚠ trust line (ADR-037); the honest third
state — general tactics **clearly labelled "not checked against your data"** (ADR-085). All four example queries are
real (from Help §6). Works **data-only** on the live app (routing + verification + facts, no prose needed).

---

## 9 · Boot Battle ⚔️ — short (~40s)  *(status: drafted 2026-08-13; the most visual/shareable)*

> **[0:00 – Hook]** Two players, one spot — who gets in? Settle it with a **Boot Battle**.
>
> **[0:08 – What]** Pick any player, choose a rival in the same position, and MADBOOTS puts them **head-to-head** —
> points, goals, expected points, form, fixtures — highlighting the winner, stat by stat. *(UI: the two-player
> compare card, winners tinted teal.)*
>
> **[0:24 – Where]** Compare anyone — your own squad, the whole league, or a specific club — right from any player
> card.
>
> **[0:32 – Close + CTA]** Stop guessing. Let the stats fight it out. **The analytics decide. The AI explains. You
> make the call.** Try MADBOOTS **free** at **madboots.com**.

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

**Clip library:**
1. **Trust line** — an Ask captain/transfer answer showing **✓/⚠**.
2. **Squad Lab — build** — set budget/objective/archetypes → build → the 15.
3. **Use this squad → / Download.**
4. **Manager-ID import** — the Squads sidebar (post-GW1).
5. **My Squad pitch** — the green formation, kits, xP chips, (C).
6. **Player card** — the xP chip + the per-GW row + stats/trends.
7. **Boot Battle** — pick a player → the winner-tinted compare card → the **pool selector** (My team/All/By club).
8. **Make captain / Substitute** — the ⚙ panel controls.
9. **AI Tips plan** — captain · lineup · transfer · injuries + **Edge/Risk/Confidence**.
10. **Transfer** — rank by **XI improvement** + bank slider + coordinated plan + **Apply this plan →**.
11. **Players sorted by Own%** — the 💎 differential surfacing + a stat board.
12. **Fixtures** — the difficulty ticker + **🎯 Radar**.
13. **Trending** — the crowd boards.
14. **News** — the injury/doubt feed.
15. **Ask** — the box + a grounded answer (✓/⚠ + the "not checked" label).

**Per-video (which library clips):**
- **2-min explainer:** 1 → 2,3,4 → 5,6,7 → 9 → 11,12,13,14 → 15.
- **60-sec cut:** 1 → 2,4 → 9 → 7 → 15.
- **§4 xP & Confidence:** 6 (xP chip + per-GW) → 9 (Confidence·Edge·Risk).
- **§5 Finding Differentials:** 11 (Own% 💎) → 12 (Radar) → 15 (the "best differentials" Ask).
- **§6 Build:** 2 (the controls + build) → 3.
- **§7 AI Tips & Transfers:** 9 → 10.
- **§8 Ask Anything:** 15 (a few queries + the ✓/⚠ + "not checked").
- **§9 Boot Battle:** 7 (pick → compare card → pool selector).

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
