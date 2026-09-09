# MADBOOTS — Screenshot capture list

**One capture session, ten videos.** Every still the nine unshot scripts need, with the page to open, the
state to set up first, and what to crop to. Built from the scripts in `Video_Scripts.md` and verified against
the app at **2026-09-09** (post ADR-181).

---

## Why a list and not a shot list

The intro (§0) proved the format: **studio bookends, stills through the middle, Maddie in a PiP circle.**
Screen recording was considered and rejected — Streamlit reruns the whole script on every interaction, so
filming means editing around spinners and repaints. A still captures the app at its best and crops to the one
number the voiceover is naming.

### The rule that matters most

> **One panel per beat.**

The intro contains both the right answer and the wrong one. At **1:02** it shows the Signals page alone —
full width, readable, one idea. At **0:26** it shows four panels at once and none of them can be read at
900px, let alone on a phone. The voiceover only ever names one thing at a time; a second panel adds nothing
and costs legibility. **If a beat needs two things, it is two beats.**

### Capture settings — set once

| | |
|---|---|
| **Browser width** | ~1440px, zoom **125%** — the app is designed for a phone but filmed on a desktop; 125% makes body text hold up when the frame is later cropped |
| **Theme** | **Dark**, throughout. The intro is dark and the studio set is dark; a light-mode still would flash |
| **Data** | Reseed first, so no stale deadline or dead gameweek is on screen |
| **Squad** | Load **RoboTS** (or your own) — never an empty state |
| **Format** | PNG, full-window, then crop. Keep the uncropped original: a later script often wants a different crop of the same shot |
| **Naming** | `NN-surface-state.png`, matching the IDs below, so the edit can find them |

⚠️ **Player photos are CDN-blocked in the artifact renderer** — anything photo-heavy (the big player-card
headshot, the pitch kits) must come from the **live app**, not the hero-shots page.

---

## The capture list

Each row: what to open → what to set up → what to crop to. **Bold** is the thing the voiceover names, so the
crop should make it the largest readable element.

### A · The trust line and the week's answer

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **A1** | My Squad ▸ **This week** | Default. It renders on load | The **✓/⚠ trust line** and the sentence above it. Tight — this is a *proof* shot, not a page shot |
| **A2** | My Squad ▸ **This week** | Default | The **Confidence · Edge · Risk** block, whole. Include the ⚠ Risk line — the honesty beat is the point (§4) |
| **A3** | My Squad ▸ **This week** | Default | The **captain line** alone: name, xP, opponent, confidence |
| **A4** | My Squad ▸ **This week** | Default | The **transfer line** alone, including *Longer view: +X over the next 5 GWs* |
| **A5** | My Squad ▸ **This week** | A squad with a flagged player | The **Flags** line — *"players to watch"* in §1/§7 |

*Used by:* §1 (0:00, 0:39) · §2 (0:00, 0:25) · §4 (0:33, 0:55) · §7 (0:13)

### B · The pitch

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **B1** | My Squad, default | Captain and vice set | The **whole pitch** — formation, kits, xP chips, **(C)** and **(V)** badges |
| **B2** | My Squad | Tap a shirt | The **selected shirt + its card** underneath. One player, not the pitch |
| **B3** | My Squad ▸ ⚙ panel | A player selected | The **full player card**: xP chip, per-GW row, stats, set-piece glyphs |
| **B4** | My Squad ▸ ⚙ panel | — | **Make captain / Substitute** controls |

⚠️ **B1 shows set-piece glyphs only** — ADR-178/179 took the market flags off this pitch. If a script's
voiceover wants ownership or momentum on a shirt, that is the **Lab** pitch (D3), not this one.

*Used by:* §1 (0:59) · §4 (0:12)

### C · Boot Battle

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **C1** | My Squad ▸ ⚙ panel ▸ ⚔️ Boot Battle | Two **midfielders**, close on points | The **compare card alone**, full width. The teal winner-tint per row is the payload |
| **C2** | Same | Two **forwards** | Same crop — a second pairing so §1 and §9 do not reuse one image |
| **C3** | Same | — | The **pool selector**: My team / All / By club |

*Used by:* §1 (0:59) · §2 (0:44) · §9 (all three beats)

### D · The Lab

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **D1** | My Squad ▸ **Lab** | Default, *Build a new squad* | The **top controls**: Start from · Budget · Objective · Build mode · Name this squad |
| **D2** | My Squad ▸ Lab | **Open ⚙ Constraints** | The **expanded panel** — archetypes, must-include/exclude |
| **D3** | My Squad ▸ Lab | After a build | The **built 15 on the pitch**, with the **full glyph set** and the key beneath it |
| **D4** | My Squad ▸ Lab | After a build | The **table**, showing the **per-gameweek columns** — GW3, GW4, GW5… |
| **D5** | My Squad ▸ Lab | After a build | **Use this squad →** and **Download** together |
| **D6** | My Squad ▸ Lab | *Start from* → an existing squad | The **plan view** — your squad, week by week |

⚠️ **D1/D2 are new.** ADR-180 moved the archetypes behind **⚙ Constraints**, so §6's *"add a strategy"* beat
is now **two shots** — the controls, then the panel opening. That is a better beat than a slider that was
already sitting there, but the script's shot note still says one.

*Used by:* §1 (0:18) · §2 (0:12) · §6 (0:11, 0:38, 0:49)

### E · Transfers

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **E1** | My Squad ▸ **Transfer** | Bank set | The **ranked list**, headed by the **XI-improvement** column |
| **E2** | My Squad ▸ Transfer | — | The **bank slider** |
| **E3** | My Squad ▸ Transfer | A multi-move plan | The **coordinated plan** + **Apply this plan →** |

*Used by:* §7 (0:35)

### F · Research — Scout, Radar, Team DNA, FDR

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **F1** | Players ▸ **Scout** | Default | The **worth-a-look shortlist**, with the *worth a look, not worth points* caption **in frame** |
| **F2** | Players ▸ Scout | — | The **board selector** behind it — the five boards |
| **F3** | Players ▸ **Radar** | Default | The **target list** from the easiest fixture runs |
| **F4** | **Team DNA** | A strong club | The **eight-axis radar**, whole, plus the grade |
| **F5** | Team DNA | A club with an **unrankable axis** | The radar **with the gap** — §H's honesty beat, and the hardest shot to get. Worth hunting for |
| **F6** | **FDR** | Default | The **difficulty ticker** |

⚠️ **F1's caption is not optional.** ADR-167: two of Scout's five signals sit at weight **0** in
`decision_xp`, so *worth a look* is the claim and *worth points* is not. If the caption is cropped out, the
still says something the app deliberately does not.

⚠️ **§G has a timing constraint.** Four of Scout's five boards need 900 minutes to speak for *this* season
and no player clears it yet, so they honestly show **last season**. Either shoot §G after ~GW10, or keep the
voiceover off *"this season"* — the script is already written to survive either.

*Used by:* §1 (1:32) · §2 (0:53) · §5 (0:33) · §G (all) · §H (all)

### G · Crowd — Trending and Signals

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **G1** | **Trending** | Default | The **👀 Worth noticing** strip |
| **G2** | Trending | — | One **crowd board**, not four |
| **G3** | **Signals** | Default | **Right now** — the top of the evidence ladder, headline + sell-off together |
| **G4** | Signals | Scrolled | The **four sections in order**, showing the ladder itself |
| **G5** | Players ▸ Pool | A **💎 differential** in view | The **ownership tier glyph** on a row — §5's *"what is a differential"* beat |

⚠️ **G4 is the one shot where more than one panel is correct** — the *ordering* is the claim (ADR-150), so
the frame has to show it. Everywhere else, one panel.

*Used by:* §1 (1:32) · §5 (0:11, 0:33)

### H · Leagues

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **H1** | My Squad ▸ **Leagues** | A loaded league | The **standings table** with movement arrows |
| **H2** | Leagues | After *Read N squads* | **Effective ownership vs global** — the differential-or-template number |
| **H3** | Leagues | — | The **captain split** |
| **H4** | Leagues | A rival picked | The **head-to-head strip** — You · Rival · Gap, with the season line above it |
| **H5** | Leagues | Same | **What they have that you don't** — the differential table. This is §8's payload |

⚠️ **Never film or say a win probability.** ADR-161 measured it and refused to ship it: one starter's points
have sd **3.51**, so a three-differential H2H has a gap sd of ~8.6 against typical margins of 2-5 points — it
would read *"it's close"* every week. §8's script is explicit about this.

*Used by:* §1 (2:00) · §8 (all)

### I · Import and close

| ID | Open | Set up | Crop to |
|---|---|---|---|
| **I1** | Sidebar ▸ **⚙ Your team** | Empty state | The **manager-ID field** |
| **I2** | Same | After import | The **team banner** — *YOUR TEAM · <name>* + synced |
| **I3** | **madboots.com** | — | The **landing hero** — already used as §0's end-card; reuse it |

*Used by:* §1 (0:18, 2:18) · §2 (0:12) · every close

---

## Per-script assembly

Each beat, one still. Where a beat needs two ideas it is split, which is why some scripts have more stills
than script beats.

| Script | Stills, in order |
|---|---|
| **§1 hero, 2:27** | A1 → D1, D2, D3 → I1, I2 → A2, A3, A4, A5 → B1, B2, B3, B4 → C1, C3 → F1, F3, F4, F6 → G1, G3 → H1, H2, H4, H5 → I3 |
| **§2 60-sec** | A1 → D1, D3 → I1 → A2, A3, A4 → C1 → F1 → I3 |
| **§4 xP & Confidence, 90s** | B3 (xP chip + per-GW) → A3 → A2 → A2 again, tight on the ⚠ Risk → I3 |
| **§5 Differentials, 90s** | G5 (💎 tier) → F1, F2 → G1 → F3 → I3 |
| **§6 Build, 45s** | D1 → D2 → D3 → D4 → D5 → I3 |
| **§7 Your Week, 45s** | A2 → A3, A4, A5 → E1, E2, E3 → I3 |
| **§8 Leagues, 45s** | H1 → H2, H3 → H4 → H5 → I3 |
| **§G Scout, 45s** | F1 → F2 → F1 again, tight on the *worth a look* caption → I3 |
| **§H Team DNA, 45s** | F4 → F4 tight on one axis → F6 (pair with FDR) → **F5** (the gap) → I3 |
| **§9 Boot Battle, 40s** | C1 → C2 → C3 → I3 |

**Total: 38 stills, one session.** Fourteen of them carry three or more scripts.

---

## Composition notes, from the intro

Three things the intro already gets right, and two to change.

**Keep:** the studio bookends; the circular PiP; the landing-page end-card.

**Change — one panel per beat.** Covered above; it is the single biggest lift available.

**Change — the PiP overlaps body text.** At 1:02 Maddie's circle clips a word of the Signals paragraph. Park
her in a corner with clear space, or shrink her slightly. Easiest rule: **crop the still so the corner she
occupies is empty**, rather than moving her per scene.

**And one fix outside the frame:** her tracksuit reads **"MsdBoots"** in the opening shot — a generation
artifact. A tighter head-and-shoulders crop puts the chest logo out of frame without a re-render.

---

## The staleness problem, stated once

⚠️ **The intro's stills show an app that no longer exists.** It was rendered 2026-09-01; ADR-175 → 181 all
landed after. Visible in its 0:10 frame alone: the `1 2 3 4 5 10` horizon selector (removed from My Squad,
ADR-179), *"Squad name"* (now *"Name this squad"*, ADR-178), the archetype controls in the open (now behind
⚙ Constraints, ADR-180), the accent in **red** (now purple, ADR-180), five top tabs including Transfer (now
four, ADR-175), and heavy market flags on the pitch (now set-pieces only, ADR-178/179).

That is not urgent on its own. It matters because **shooting the other nine from the current UI makes the
intro the odd one out** — and the intro is the one wired into madboots.com as *"See how it works."*

**Recommended order:** shoot these 38 stills → cut §9, §7, §8 first (short, high-value, cheap to redo if the
format needs adjusting) → then the long-form pieces → **re-render §0's stills last**, keeping Maddie's audio
and the studio bookends. The app has produced five UI ADRs in the past week; re-cutting the intro before it
settles would just buy the problem twice.

---

## Maintenance

This list describes surfaces that move. It is **not** swept by `tests/test_navigation_copy.py` — that guard
covers `src/web_streamlit` only, and the ADR template's checklist names this file and `Video_Scripts.md` as
the two documents a navigation change has to be checked against **by hand**.

Re-read it after any ADR that renames, moves or retires a surface. The audit on 2026-08-31 found every script
describing an app that had moved underneath it; this file will drift the same way.
