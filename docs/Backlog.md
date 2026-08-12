# Backlog

Captured ideas not yet scheduled into a sprint. *(The larger unbuilt features live in the
consolidated [Roadmap](04_Roadmap/Roadmap.md) — "Next / Then / Later"; this file holds the small
nice-to-haves and tech-debt.)*

> **Design principle (owner, 2026-08-12):** MADBOOTS' **branding and UX must stay clean, modern, and easy to
> navigate.** Every UI/IA change below is measured against it — don't just move clutter around, and keep the brand
> vocabulary/mascot tasteful, not gimmicky. *(Worth pinning as a design ADR.)*

## Sequencing (owner-agreed, 2026-08-12)

**Infra changeover FIRST**, then the feature work — by technical risk (see `docs/MADBOOTS_CHANGEOVER.md`):
1. ✅ **Infra changeover — DONE (2026-08-12).** Repo → **`madbootsfpl/fpl-assistant`** · Streamlit reconnected ·
   subdomain → **`madboots.streamlit.app`** · in-app URLs updated · homepage **LIVE on Cloudflare Pages at
   `madboots.com`**. Internal `fpl-assistant` package + `FPL_*` secrets unchanged.
2. **P0 quick-wins** (below) — transfer filters · captain-persist · the cold-start data floor.
3. **IA restructure** (A1/A2) — discuss/gate, then build.
4. **Persistence + Google auth** (C-cluster) — the strategic rework, on the final domain.
5. Branding vocabulary (E) · per-GW display (A5) · A6 consolidation · docs refresh (D).

## Tester feedback — 2026-08-12 intake

Triaged with priority (P0 now · P1 gate/soon · P2 polish). *(Some referenced screenshots didn't arrive — the FFH
click-menu, the points-comparison mockups, the Sangare/Shaw/Haaland snaps; triaged from the text.)*

**P0 — do soon (before recruiting more testers)**
- 🧭 **Data cold-start floor** *(Obs B1–B3)* — new/promoted players floored at **0/near-0** (Sangare 0 vs HUB 3.6;
  O'Shea 1.6 vs 4.7) reads as "broken" and erodes trust. A **position-based, minutes-weighted baseline** so a
  likely-starter never shows 0, even preseason. *(NOT chasing FFH parity — they have paid Opta + prior-season/
  lineup data we don't buy, ADR-016; the broader gap closes via GW1 calibration, ADR-101. Needs an ADR.)*
- 🧭 **Mobile data-loss** *(Save C2)* — on iPhone, app-switching + back to Safari **reruns Streamlit and wipes the
  loaded team** (session_state lost on reconnect). Severe. Fixed properly by the persistence rework (C-cluster);
  the rename resets cookies anyway, so do it **after** the changeover.
- 🩹 **Captain doesn't persist on load** *(Save C1)* — a cloud-loaded squad should carry its `captain_id`. Verify the
  save/load includes it; likely a quick fix.
- 🩹/🧩 **Transfer — add filters** *(UX A3)* — the "bring in" list is very long; add **team** + **price/amount**
  filters (extends the S143 Transfer, which already has position/affordable/injured).

**P1 — structural (discuss/gate)**
- 🧭 **IA restructure** *(UX A1+A2)* — the Squads tab is busy. Pull **Build** out to its **own top-level tab**
  (rename — *Team Builder / Draft / Squad Lab?* — not to be confused with My Squad), and make **My Squad** its own
  tab with the tools as **5 sub-tabs** (AI Tips · Chips · Health · Transfer · Captain). *Build is only for
  season-start / wildcard / revamp — its prominence confuses "why is Build here after I built my team".* **Discuss
  first** — it frames A5/A6/filters. One ADR.
- 🧭 **Persistence + auth model** *(Save C2+C3+C4)* — review save/load/persist; keep a recommended team on-device,
  cross-device. Owner's steer: **Google auth (`st.login`)** is more robust + friendlier than the code gate (clunky
  on iPhone) — a stable identity that anchors **auto-save/restore** and fixes the mobile wipe + cross-device captain
  at once. Couple these; keep the code gate as fallback. One ADR (the deferred hard-auth upgrade, ADR-098/099).
- 🧩 **Per-player weekly xP** *(UX A5 / Obs B1)* — on the My Squad pitch, show the **per-GW** points for **GW1–3**
  individually, then a **total** if >3 GW selected (the FFH per-GW breakdown the owner liked).
- 🧭 **Consolidate player actions** *(UX A6)* — FFH: **click a player → a menu** (full card · substitute · make
  captain). ⚠ **Platform wall** (S139/142): a static `st.markdown` pitch **can't do a click-menu**; the achievable
  version is a unified **"player actions" panel** under the pitch (pick → card + Substitute + Make-captain in one
  place). Sits best after the IA restructure.

**P2 — branding / polish** *(governed by the design principle above)*
- ✅ **MADBOOTS vocabulary** *(Branding E)* — **DONE (Sprint 148, ADR-107).** Adopted **Edge** (the `explain` "Why"
  heading) + **Risk** (reconciled "Risks"→"Risk") across all four render surfaces, and **🎯 Radar** (was "Target by
  fixtures"). **"Pick" deferred** — its home would be *"AI Tips"*, but that renders a whole-week plan, so "Pick"
  mis-sizes it (owner's call); "AI Tips" + "Captain" left as-is. Governed by *clean, modern, not gimmicky* (brand as a
  light signature). Owner flagged *"another pass to tweak later"* — revisit once seen in the browser.
- 🧩 **Mascot/brand into the tools** *(UX A4)* — AI Tips · Health · Captain under My Squad (the captain card already
  has the mark, S144).

**Ongoing**
- 🧩 **Docs refresh** *(D)* — a consolidation pass (PROJECT_STATUS/Roadmap/README) after the big changes land.

## Branding — MADBOOTS rebrand ✅ shipped (Sprint 141) · infra changeover ✅ done (2026-08-12)

The **rebrand shipped** (Sprint 141, ADR-103 + US-348/349/350; polished in Sprint 144): the visible product is
**MADBOOTS** — the MB badge favicon, the two-tone wordmark, the tagline, the not-affiliated footer. The **infra
changeover is done** (2026-08-12, `docs/MADBOOTS_CHANGEOVER.md`): app now at **`madboots.streamlit.app`** under
**`madbootsfpl`**, front door **`madboots.com`** (Cloudflare Pages). Internal `fpl-assistant` package + `FPL_*`
secrets unchanged. Original changeover plan (for the record):

- 🧭 **Brand infrastructure changeover** *(do it all together, in one coordinated session, alongside the rebrand —
  not piecemeal; the live beta can briefly blink offline)*. Owner secured **@madbootsfpl** across socials + GitHub.
  - **Q1 — move the repo to `madbootsfpl`.** Use GitHub **Transfer** (preserves history/issues/stars + auto-redirects
    the old URL), *not* a fresh repo. **Gotcha:** breaks the Streamlit Cloud source link → must **reconnect** the app
    + re-grant Streamlit access to the new account (GitHub Actions secrets don't transfer; Streamlit secrets are
    safe). *(An Org `madboots` is the tidier long-term home but optional — a user/org can't share the `@madbootsfpl`
    name he grabbed.)* Code-side: update the git remote + the hardcoded repo URLs in `Home.py`/`8_Feedback.py` + docs.
  - **The homepage (designed + owner-approved).** A free static **`madboots.com`** landing page — the hero boots
    lockup + tagline + ethos (one honest xP · grounded ✓/⚠ · whole-week) + a **Launch-the-app** CTA + the
    not-affiliated footer. Self-contained single HTML (hero embedded as a data URI) at
    `~/Downloads/madboots-home.html` → rename `index.html`, host **free** on **Cloudflare Pages** (owner's pick — he's
    already on **Cloudflare DNS**, so one dashboard for DNS + Pages + a `301` redirect + free SSL); point
    `madboots.com` at it. **Access stays in the app** — a static
    page can't gate a public Streamlit URL, so the landing page is **brand + CTA + (optional) signup**, not the gate;
    don't double-gate. *(Real platform gating, if ever wanted, = Streamlit **private-app/allowed-viewers** or
    **`st.login()`** — both free; a deferred upgrade, not needed now.)* Launch links target `madboots.streamlit.app`
    (live after the subdomain rename). No signup form yet (a Tally/Google Form/Formspree button is a later add).
  - **Q2 — the domain.** (1) Rename the Streamlit subdomain → **`madboots.streamlit.app`** (free, one setting).
    (2) **301-forward `madboots.com` → the app** (registrar/Cloudflare — **no masking**). **Ceiling:** Streamlit
    *Community* Cloud has **no custom-domain** support (paid/Snowflake only), so the URL bar shows `…streamlit.app`
    after the redirect; a tiny free **static landing page** (Cloudflare/GitHub Pages) is the nicer long-term front
    door (+ a home for the hero illustration). **Flags:** renaming the subdomain **logs everyone out** (the
    remember-me cookie is first-party per-domain; cloud-saved squads survive, keyed by handle) and breaks
    `_DEFAULT_ORIGIN`/`FPL_FEEDBACK_ORIGIN` (code-side, handled in the rebrand sprint).

## Tester feedback — 2026-08-10 intake

Triaged by size: 🩹 quick fix (a small sprint of these) · 🧩 small UX fix · 🧭 feature (needs a gate/decision).

- 🩹 **Player-card season label is wrong/misleading** — the card band hardcodes **"Season 24/25"**, but preseason
  the stats shown are **last season's carryover**. Label it **"Last season"** (preseason) — and the **current
  season** once GW1 has played — not a fixed/likely-wrong year. `player_card.py` (`plc-title` band). *(One-liner.)*
- 🧩 **Player-card hover popover truncates** — the compact hover card on the My Squad pitch cuts off / shows too
  much to fit. Shrink it (fewer stats, smaller type) and/or fix clipping (it may be cut by a container). Verify on
  the deploy (esp. bench kits). `pitch.py` (`.kit-pop`) + the `compact` card in `player_card.py`.
- 🩹 **Trending — surface "🔥 Top discussions" first** — the **Community Signals** list is long and buries the
  **🔥 Top discussions this week**; reorder so Top discussions shows first (it's the sharper lens). `6_Trending.py`
  (the "💬 Talked about" tab).
- 🩹 **Players price filter excludes the most expensive player** — the Max-price slider caps at **£15.0m**, so
  **Haaland (£15.5m)** is filtered out. Set the max to the **highest player price** (0 → max), not a fixed 15.0.
  `filters.py` (`filter_controls`, `with_price`). *(One-liner.)*
- 🧭 **Waitlist capture at the cap (ADR-098 extension)** — when registration is **full**, **record the would-be
  tester's email** (a `waitlist` row in the existing Supabase, reusing the store) so the owner can invite them
  later — instead of only linking `FPL_SIGNUP_URL`. Consented (they're trying to join); a small opt-in server
  write like `beta_users`. Needs a gate.
- 🧭 **Capture email on a wrong invite code (ADR-098 extension) — privacy call** — record the email (+ "bad code")
  of a **failed** registration so the owner can invite later. Doable the same way, **but** it stores emails of
  people who didn't have a valid code (possible typos/randoms) — decide if it's worth it, keep it minimal +
  owner-only, and note it in the privacy posture before building.
- 🩹 **Help — mention ☁ Save/Load in the "Save your team" step** — add that **☁ Save/Load across devices**
  (sidebar) exists and is likely the **better** option (vs download/upload). `7_Help.py` (step 7). *(Copy tweak.)*

## Requested features — 2026-08-07 intake (owner)

Five feature requests, triaged by feasibility (✅ buildable now · ◑ partial/plumbing now, sharpens at GW1 ·
⏳ GW1-gated · 🧭 needs a design/ADR):

- ✅ **DONE (Sprint 100, US-259/260, ADR-085)** — **AI Chat Assistant** — a 24/7 chatbot for FPL **rules**,
  squad questions, and tactical advice. Delivered: a curated **rules KB** (`src/fpl_rules.py`) answered by a
  grounded `rules` intent (**verified ✓**); a **labelled free-form** tail for open tactics (**ℹ not verified**,
  never a specific pick); grounded squad/player questions unchanged. The "scoped general-knowledge mode
  clearly labelled not-verified" this line called for. *Follow-ups:* a hosted LLM for the deploy (free-form
  needs a model — the cloud degrades to rules + grounded); ~~grow the KB~~ **grown 13 → 21 topics** (Sprint 110,
  US-282: flags · preseason transfers · one-chip-per-GW · bench points · wildcard timing · leagues · ranking ·
  team value) + the routing cues so each verifies ✓. Keep growing as questions arrive.
- ⏳ **Elite Manager Comparison** — how your squad compares to top-ranked managers + what the **Top 1,000**
  are doing (captain trends, transfer flow). *Needs:* the FPL leagues API + per-manager picks; **picks are
  public only from the GW1 deadline (2026-08-21)** → no data preseason. Build post-GW1.
- ✅ **DONE (Sprint 095, ADR-081)** — **Set Piece & Ownership Data** — who takes **penalties · corners ·
  free-kicks** for each team, plus **ownership combinations** to find high-value, low-ownership
  **differentials**. Ingested `corners_order` + `freekicks_order` (auto-migrated); `set_piece_flags`;
  a Players **"Set pieces"** view (Pen/Corners/FK order + Own%/Val/£m, filterable, differential caption) + a
  Pool **"Set"** flag. Display-only; `refresh`+`reseed` populated real data (38 first-choice takers).
  *(Follow-up: ~~a gated set-piece xP boost in `decision_xp` — a modelling change, not a lens.~~ **DONE** —
  Sprint 126, US-313/314, **ADR-096**: a tier-restricted `set_piece_bonus` in the rate (only where the baseline
  doesn't already price the duty → no double-counting), **wired-dormant** (`SET_PIECE_WEIGHT = 0`) + auditable
  (`set_piece_xp` + a grounded reason). Calibrate + backtest the weight at GW1.)*
- ◑ **DONE (v0) — Chip Strategy Guidance** (Sprint 096, US-251/252, ADR-082) — AI advice on when to use
  **Wildcard · Free Hit · Bench Boost · Triple Captain**. Delivered: `chip_advisor` (per-GW `by_gameweek`
  reductions + `best_legal_xi`) → a grounded `chips` `ask`/`chat` intent + a Squads **"Chips"** view. *Still
  deferred:* **DGW/BGW** detection (in-season — every GW has 10 fixtures preseason) + **mini-league position**
  (leagues API, GW1); a season-long scan; ~~a standalone CLI `chips` command~~ **DONE** (Sprint 128, US-316 —
  `python app.py chips --squad X`, reuses `render_chip_advice`).
- ✅ **DONE (Sprint 112, US-285/286, ADR-092)** — **Price Change Predictor** — an indicator flagging players
  about to **rise/fall** in value, to time transfers. Delivered: `analytics/price.py::price_pressure` =
  `net_transfers ÷ selected_by%` (ownership-normalised → comparable; the constant total-manager count cancels,
  so no new ingest), `price_prediction` (rise/fall/stable), `price_flag` (🔺/🔻, distinct from the retrospective
  💰/💸); a **Price** column on the Pool + a **My Squad** transfer-timing nudge, with an honest "live from GW1"
  caption. A directional **flag, not truth**; a **lens** (never `decision_xp` — an invariance test pins it);
  **0 preseason → live at GW1**. ~~*Still open:* an `ask` "who's about to rise?" intent~~ **DONE** (Sprint 128,
  US-317 — a `price` `ask`/`chat` intent → likely risers 🔺 / fallers 🔻; a "live at GW1" message preseason).
  *Still open at GW1:* calibrate the thresholds on real net transfers; an absolute "% to the next change" (needs
  `total_players` + a since-last-change counter); a **CLI price column** on `table`/`xg` (the ask intent covers
  the query).

## Enhancements

- ~~**Differential archetype**~~ — **DONE** (Sprint 043, **ADR-044**). Ingested `selected_by` and added a
  `min_differentials` constraint (≤5% owned — pinned so it bites); `squad --full --differential N` +
  NL "… with N differentials". Completes the archetype trio (low-cost / premium / differential).

- ~~**Bench order**~~ — **DONE** (Sprint 091, US-241/242, **ADR-078**). A pure `bench_order(bench, scores)`
  (outfield by xP → 1st/2nd/3rd + the bench GK, keeper-only), shown on **My Squad** as a "🔁 Bench order
  (auto-subs)" line with the FPL-rule explainer. A recommendation (order by value), not a per-blank
  simulator. *Still open:* let the user *set* the order / annotate the pitch cards / simulate specific blanks.
- ~~**Availability flags in the ranking views**~~ — **DONE (web)** (Sprint 085, US-228/229, **ADR-074**). A
  shared `availability_flag(player)` (🚑 injured · 🚫 suspended · ⛔ unavailable · ❓ doubtful; blank =
  available) + a **Fit** column on the **Players Pool** and all **four stat boards**; display-only, reuses
  ingested `status` (no analytics change). ~~*Still open:* the **CLI** ranking views (`table`/`xg`) + a chance%
  on the doubtful flag.~~ **DONE** — the CLI `table`/`xg` already carry a **Fit** column (`fit_flag`, ✅ =
  available, US-276) and the doubtful flag already shows the **chance%** (`❓ 75%`, US-236). (Confirmed at
  Sprint 120 planning.)
- ~~**DefCon opposition magnifier**~~ (owner idea, 2026-08-27) — **BUILT wired-dormant** (Sprint 129, US-318/319,
  **ADR-097** refined). Scale a player's DefCon by the **fixture's defensive context** (strong opponent → more
  DefCon; weak → less) via an **FDR clean-sheet proxy** — **no betting odds**. **Refined to the delta approach:**
  the baseline already includes DefCon points, so the magnifier **re-weights that share** (`defcon_pts_per_match ·
  (magnifier − 1)`), **0 at neutral → no double-count**. `analytics/defcon_xp.py` + a per-GW delta in `player_xp`
  behind `DEFCON_MAGNIFIER_WEIGHT = 0` (invariance-pinned) + `defcon_xp` + a "🛡 DefCon fixture edge" reason.
  *Deferred to GW1:* set the weight + tune `DEFCON_P_SCALE`/band + **backtest** on real returns; the
  **transferred-player** team-share adjustment; a separate clean-sheet-xP magnifier (opposite direction).
- **In-app email** (owner question, 2026-08-27) — **answered, no build.** The in-app Feedback form **already**
  emails you when `FPL_FEEDBACK_WEBHOOK` points at a **relay** (FormSubmit/Web3Forms, US-308) — that *is* in-app
  email (Send → your inbox, no mail client). Direct **SMTP** send isn't free (**Proton has no free SMTP** → paid
  Bridge). Owner action: set the relay (BETA.md §1B).
- **Ceiling / "differential" captaincy** — `captain` (Sprint 027, ADR-029) ranks by *mean* xP,
  which favours nailed-on premiums. A ceiling/variance view would surface high-upside punts — but
  it needs variance/form data we don't have yet. Revisit once in-season data accrues.
- **Multi-move transfer *planner*** — ◑ *partly done.* A **coordinated greedy plan** shipped (Sprint 033,
  **ADR-035**: `transfer --count N`, shared bank, no repeats) and it now ranks by **XI improvement**
  (Sprint 046, ADR-046). Still open: the **−4-hit vs roll / banking** maths and chip-aware sequencing —
  a bigger optimisation (wants the real bank + xMins) → Roadmap *Later*.
- ~~**Differentials / value `ask` intent**~~ — **DONE** (Sprint 070, US-198/199, **ADR-061**). A
  **differential** lens on the shortlist (`ask "best differential <pos> under £Xm"`, ≤5% owned, +Own%) + a
  single-player **`worth`** verdict (`ask "is X worth the money?"` → xP/£m · rank among position peers · vs
  the position median · a tiered verdict). Grounded; the plain shortlist stays byte-identical. *(Value
  (xP/£m) already existed on the shortlist, ADR-042; this added the ownership lens + the single-player
  judgment.)* The differential filter sharpens at GW1 as ownership concentrates.
- ~~**Pronoun-aware chat**~~ — **DONE** (Sprint 094, US-247/248, **ADR-080**). `_resolve_pronoun` rewrites a
  pronoun → the last turn's sole subject ("is **he** worth it?" → the last player); the web Ask now threads
  `Context` (`converse`) so pronouns + follow-ups work in the browser too. ~~*Still open:* persist the chat
  context across runs.~~ **DONE** (Sprint 110, US-281, **ADR-091**) — a local, TTL'd `chat_context` store; the
  CLI `ask`/`chat` remember the last turn across separate runs; the multi-user web stays session-only
  (read-only). *(Web cross-session persistence would need client storage → deferred.)*
- ~~**Team-level squad-fixtures view**~~ — **DONE**. The ADR-049 team lens shipped in **`ask`/`chat`** first
  (ADR-067: a "by team" `fixtures` mode via `render_squad_team_fixtures`); **Sprint 120, US-302** brings it to the
  **web ticker** — a **"My squad"** scope restricting the rows to your squad's **teams** with a **player-count**
  column. *(Companion: US-301's "🎯 Target by fixtures" — the best players to buy from the easiest-run teams,
  `analytics/targets.py`.)*

### Web UI ideas (from the Sprint 054 review — owner's notes)

- ~~**Home tab + full landing**~~ — **DONE** (Sprint 059). The Streamlit landing is **Home** and lists
  every page.
- ~~**Team badges + player photos**~~ — **DONE** (Sprint 059). `team.code` ingested → badges; player
  photos via `code`; shown across Players / Fixtures / the squad tabs (shared `badges` helper +
  `st.column_config.ImageColumn`).
- ~~**Deploy & share**~~ — **DONE** (Sprint 053, **ADR-053**). Deployed on **Streamlit Community Cloud**,
  public + read-only; a committed `data/seed.db` + `seed_squads.json` seed it; Ollama absent → degrades to
  decision + facts. Runbook: `docs/DEPLOY.md`. *(A custom domain via CNAME remains an optional extra.)*

- ~~**Crowd & Sentiment Signals (Phase 6) — Tier 1 & 2**~~ — **DONE** (Sprints 060–068). A *lens, not a
  rewrite of xP* (a test asserts `decision_xp` is untouched). **Tier 1** (ADR-057): ingested
  `transfers_in/out_event` · `cost_change_*` · `form` · `ict_index` (+ components) · `value_form`; crowd
  **flags** on Players/Build/Analyse/My Squad/Captain/Transfer; a **"trends"** `ask` intent + a **Trending**
  page. **Tier 2** (ADR-058/059): an FPL **news lens**, **manager-ID import**, and **Community Signals**
  (Reddit RSS buzz). **Tier 2b — media feeds** (Sprint 115, ADR-093): a **📰 Headlines** lens on News
  (Fantasy Football Scout + BBC Football public RSS; a YouTube slot) + a Reddit **weekly-top** discussions list
  on Trending — all public/no-auth, best-effort, display-only. *Deferred (ADR-093):* Reddit `.json`/HTML
  scraping/Transfermarkt; **betting/odds** and NLP over headlines (odds = a possible **Tier-3 modelling** input,
  not a lens). **Tier 3** (backtest crowd-follow vs xP-only) remains open → Roadmap *Later*. Momentum/form
  boards light up at **GW1 (2026-08-21)**.

- ~~**Cloud squads — server-side persistence (Path 2)**~~ — **DONE** (Sprint 124, US-309/310, **ADR-094**).
  **Cross-device** save/load: `web_streamlit/cloud_store.py` (handle-keyed **Supabase** save/load/delete,
  best-effort, secret-gated `FPL_STORE_URL`/`FPL_STORE_KEY`) + a My-Squad **☁ Save/Load across devices** expander
  (no login — the handle is the key) + `docs/CLOUD_SQUADS.md`. The **first server-side write** — the read-only
  invariant was revised (one opt-in, tested, secret-gated write); off by default. Native `st.login()` = the
  deferred "product" upgrade (the adapter interface fits it). ~£0 (Supabase free tier).

### Done (kept for the trail)

- ~~Include / exclude players~~ — **DONE** (Sprint 008, ADR-009).
- ~~`xp`/`squad` objective toggle~~ — **DONE** (Sprint 010, ADR-011).
- ~~Full 15-man squad~~ — **DONE** (Sprint 011, `squad --full`, ADR-012).
- ~~Declared bench~~ — **DONE** (Sprint 012, `squad --bench`, ADR-013).
- ~~Flexible formations~~ — **DONE** (Sprint 013, `squad --formation` + flexible default,
  ADR-014). Ranges (DEF 3–5, MID 2–5, FWD 1–3); the bench-implied shape shown in `--full`.
- ~~Validate a declared bench yields a legal XI~~ — **DONE** (Sprint 021, `legal_xi_issues`,
  ADR-022). Warns (not blocks) when a full 4-man bench leaves an illegal XI; reuses `XI_FLEX`.
- ~~Saved / persistent squad~~ — **DONE** (Sprint 023, `squad --save`/`--load`, ADR-024).
  User state in `data/squads.json` (gitignored), separate from the FPL cache; reload re-prices +
  flags injuries + notes departures.
- ~~`xp` per-gameweek breakdown~~ — **DONE** (Sprint 030, ADR-032). A `by_gameweek` breakdown on
  `player_xp` (a faithful decomposition of the total); shown in `analyse` and `xp --by-gameweek`,
  plus `analyse --sort xp`. (From Tony's Sprint 006 reflection.)

## Expected minutes (xMins) — the owner's Sprint-35 request

*Predicting playing time is often harder than predicting performance.* Rotation/minutes is the single
biggest source of FPL variance, and "assumes they play" is the recurring caveat in
`captain`/`transfer`/`analyse`. **Value: very high.** Assessed in Sprint 036 (US-108); recommended in
**two steps** so most of the value lands early, the heavy modelling waits for data.

- ~~**xMins v0 — lightweight, FPL-native, no ML *(near-term, Phase 3)*.**~~ **DONE** (Sprint 037,
  **ADR-038**). `availability_weight = chance_factor × recency-weighted minutes share` (**minutes-only**
  — the planning probe proved `starts` is unreliable pre-2022/23, correcting the original "minutes/starts
  ratio" sketch). Weights xP by expected minutes **default-on** at the decision edge
  (captain/transfer/analyse/`ask`), shown as **expected minutes** with a **`--no-xmins`** opt-out; the
  raw `xp` view stays pure. Backfill broadened 29% → 87%. *Honest limits (→ Phase 5):* role change +
  coverage. It's an estimate from chance% + history, **not** the full probabilistic model.
- **Full probabilistic xMins — the ML model *(later, dedicated phase — Roadmap Phase 5)*.** A trained
  model producing per-fixture expected-minutes *probabilities* from schedule density (hours between
  kickoffs), European-match congestion, historical manager rotation profiles, and substitution
  tendencies. **Needs:** in-season per-GW minutes to train (post-GW1, ties to Data Hardening), external
  European-fixture data (not in the FPL API), and a genuine ML effort. Gated on data → a later phase.

**Placement:** v0 as a near-term Phase 3 enhancement (immediately improves every recommendation); the
ML model as a later Phase 5 item (post-GW1). It's the highest-value deferred item — worth doing
properly, lightweight first. *(This supersedes the terse "Richer xP: … expected minutes" line under
Deferred below.)*

## Validated, deferred

- **Player-card "advanced" stats via Understat/FBref** — the player card (Sprint 139) ships with our FPL data; the
  extra FFH-style stats **Key Passes** + **Shots in the Box** aren't in the FPL API but *are* reachable from a free
  **Understat/FBref** fetch (per-shot coords → "in box"; KP direct). This is the `soccerdata`/Understat integration
  evaluated + deferred in **ADR-016** (heavy: player-matching, scraping fragility, a bigger dep). Revisit as its own
  sprint + a data-source decision if the card wants them. **Big Chances / Big Chances Created are Opta-proprietary
  (paid) — not planned.**
- ~~**A "not you? / log out" link**~~ — **DONE** (Sprint 133, US-327/328, extends ADR-099). A sidebar "Log out"
  (gated on `gate_active()`, off on the open deploy) clears the "remember me" cookie + the session and re-shows the
  gate — deferred clear (mirrors the write) + a `_beta_forgotten` re-admit guard. A **confirm dialog** on Log out
  is a deferred follow-up (only if a mis-click becomes an issue).
- **A signed/opaque "remember me" token** instead of the raw email/code cookie — deferred from Sprint 132 as
  over-engineering for a hobby beta (re-validating the raw value against `beta_users` / the code already gives the
  "pruned tester / rotated code is rejected" property). Revisit only if the raw value in the cookie becomes a
  concern (would need server-side token↔identity mapping). Native `st.login()` (verified identity + native cookie
  persistence) is the bigger hard-auth upgrade above it.

- **soccerdata / npXG** — evaluated in Sprint 015 ([ADR-016](06_Decisions/ADR-016-soccerdata-evaluation.md)).
  Matching works (~95% FPL↔Understat) and npXG is real, **but** the value is narrow
  (penalties score points in FPL, so penalty-inclusive xG is the relevant signal) and the
  cost is high (14 → 72 packages incl. a selenium/pandas stack, scraping fragility, a
  season-alignment trap). **Deferred.** Revisit only if a decision-driving need appears
  that FPL can't meet — and prefer a *lightweight* direct Understat fetch over the full
  library. Evidence: `spikes/015-soccerdata/`.

## Tech debt

- ~~**Migrate to the PuLP 4.0 API**~~ — **DONE (partial, deliberate)** (Sprint 076, US-211, **ADR-066**).
  Variables migrated to `problem.add_variable(...)`. **`PULP_CBC_CMD` kept** — `COIN_CMD` needs an
  *external* CBC (`pip install pulp[cbc]`) and fails ("cannot execute cbc") here + on the read-only Cloud;
  the bundled solver stays. The blanket `DeprecationWarning` ignore → a **targeted** PULP_CBC_CMD filter
  (other deprecations now surface). Revisit COIN_CMD only if we adopt `pulp[cbc]` / PuLP 4.0 lands.
- ~~**Shared *squad* renderer**~~ — **DONE (safe parts) + closed** (Sprint 076, US-212, ADR-066).
  `render_squad` / `render_loaded_squad` now share the **header** (`_header`) + the **"Bench:" heading**
  (`_BENCH_HEADING`). Folding into `ui/_table.py`'s `render_rows` is **not pursued** — its flat
  single-space join can't reproduce the squad views byte-for-byte (mid-table "Bench:" heading, `**`/`*`
  markers glued without the join space, and divergent price cells: an unpadded `£X.Xm` in `loaded` vs a
  width-6 pad in `render_squad`). The dividers + row bodies stay per-renderer by design.
- ~~Shared table renderer for the ranking views~~ — **DONE** (Sprint 024, `ui/_table.py`
  `Col` + `render_rows`, ADR-025). Five near-duplicate renderers → one; output byte-identical.

## Deferred (data-dependent — need season-start data)

- Richer xP: recent `form` + expected minutes (xMins — now assessed in its own section above).
- Attack/Defence FDR split (needs `strength_attack_*` / `strength_defence_*`).
- ~~**Per-GW history ingestion**~~ — **DONE (wired, dormant)** (Sprint 069, US-196, **ADR-060**). A
  `player_history` table filled by the *existing* `element-summary` backfill (the one call already carries
  `history`); empty preseason → live at GW1. ~~Still open: a `history <player>` view.~~ **DONE** (Sprint 117,
  US-295/296) — `analytics/history.player_history` + `ui/history` + a CLI **`history <player>`** command + a
  grounded **`history` ask/chat intent** (past seasons real now, per-GW at GW1; verified ✓). ~~*Follow-ups: a
  per-season price column; a web History view.*~~ **DONE** (Sprint 118, US-297/298) — a **£start→end · Δ£**
  column across CLI/Ask + a **web "History" view** on Players (season `st.dataframe` + a per-GW line chart).
  ~~*Still open: a rolling-form sparkline; a coloured web Δ£; cross-player comparison.*~~ **coloured Δ£** (🟢/🔴)
  + **cross-player comparison** (a 2nd player overlaid — `align_seasons` + a season table & line chart) **DONE**
  (Sprint 125, US-311/312). *Still open: a rolling-form **sparkline** overlay (per-GW → GW1-gated).*
- ~~**In-season form blend into xP**~~ — **DONE (wired, dormant)** (Sprint 069, US-197, ADR-060). A
  rolling-**pp90** form term in the one `decision_xp` recipe behind `FORM_WEIGHT = 0`. Still open at GW1:
  set the weight + **calibrate** the weight/window on real form.
- **Data Hardening — the GW1 flip + calibration** — prep is done (per-GW ingest + form blend, wired dormant,
  Sprint 069). At **GW1 (2026-08-21):** `history --backfill` (now also per-GW) + raise `FORM_WEIGHT` +
  calibrate; then the crowd/form-vs-xP **backtest** (Tier 3). The full 567-player backfill can ride any time.
