# MADBOOTS — Tester Guide

Thanks for trying it out! This is a **read-only** Fantasy Premier League analytics assistant — it helps you
build a squad, pick a captain, plan transfers, and analyse your team, all grounded in the FPL data. Nothing
you do here affects your real FPL account; it's a sandbox for exploring the numbers.

**Live app:** https://fantasypl.streamlit.app

You don't need an account or a login. Use the **sidebar** to move between tabs.

---

## Try this (≈5 minutes)

Work down the list — each step builds on the last. If anything looks wrong, confusing, or ugly, jot it down
(see *How to report* below).

1. **Players** — filter by position and max price, sort by points or value. Do the **photos** and **team
   badges** load? Does the price-vs-points chart make sense?
2. **Fixtures** — which teams have the easiest run over the next 5? Check the table + the difficulty chart.
3. **Build** — set a **budget**, give your squad a **name**, and (optionally) nudge the *low-cost / premium
   / differential* sliders. You get the optimal 15 (with photos), an xP table, and an XI/bench breakout.
   - Click **⬇︎ Download squad.json** — that file **is your save**. Keep it.
   - Click **Use this squad →** — it becomes your **active squad** for the other tabs.
4. **My Squad** — see your 15 with a **✓ legal / cost** banner. Try:
   - **Rename** it.
   - **Swap a player** — pick one out, pick any same-position replacement; illegal swaps are refused.
   - **Set the bench** (pick 4).
   - **⬇︎ Download** again to save your edits.
5. **Captain** — see the recommended captain, then **Set as captain**. It shows a **(C)** on Analyse and
   travels in your download.
6. **Transfer** — move the **bank** slider to free up money; you'll get ranked swaps. Pick one and
   **Apply this transfer →** — your squad updates.
7. **Analyse** — your squad's health over the next 5 gameweeks (projected xP, weak links, availability).
8. **Ask** — ask in plain English: *"who has the best fixtures next 5?"*, *"best midfielders under £8m"*,
   *"build me a squad for £100m"*. Every answer is checked against the data (a ✓/⚠ trust line).

**Load a saved squad next time:** use the sidebar **Upload a squad.json** to bring back a file you
downloaded earlier.

---

## Known limits (so these aren't a surprise)

- **Your squad resets if you refresh the browser** — until you've **Downloaded** it. Download = your save;
  re-upload it next time. (There's no server-side account yet — that's deliberate for now.)
- **Manual swaps are same-position** (a GK for a GK, etc.) — that keeps the squad legal in one move.
- **The data is a snapshot.** The sidebar shows **"📅 Data as of \<date\>"**. On the live site the data
  only updates when the owner redeploys; the **🔄 Refresh** button only appears when running locally.
- **Ask** works without its optional local AI — on the live site it shows the decision + facts (no
  chatty narration). That's expected, not a bug.

---

## How to report feedback

Please tell us **anything** — a bug, something confusing, a wrong number, or just "this bit felt clunky."

**Where:** open a GitHub issue → **https://github.com/tesheridan/fpl-assistant/issues/new**

**What helps most:**
- **Which tab** you were on (Build, Transfer, …).
- **What you did** (the steps) and **what happened** vs what you expected.
- A **screenshot** if it's visual.
- Your **browser / device** (e.g. Chrome on iPhone) for display issues.

No issue is too small — rough notes are genuinely useful. Thank you! 🙏
