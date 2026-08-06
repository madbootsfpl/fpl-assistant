"""Help — a step-by-step guide to building your team with the assistant (ADR-068).

Static content only (markdown + expanders): no analytics/data dependency, so it renders even before a
refresh, and no input controls. It complements Home (the short overview) with a deeper recipe.
"""

import streamlit as st

st.set_page_config(page_title="Help · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Help — build your team with the assistant")
st.caption("A step-by-step recipe. The **analytics decide**; a local AI only *narrates* — and every "
           "answer is checked against the data (a ✓/⚠ trust line). Your squad lives in **your session** — "
           "download it to keep it (nothing is saved on the server).")

st.markdown(
    "**Quick start:** open **Squads** → *Build* → **Use this squad** → tweak it in *My Squad* → check "
    "*Health*, *Transfer* and *Captain* → **Download** your `squad.json`. Prefer words? Do it all from **Ask**."
)

st.caption("Everything for your team lives on the **Squads** tab — switch **Build · My Squad · Health · "
           "Transfer · Captain** with the buttons at the top.")

with st.expander("1 · Build your squad  →  **Squads → Build**", expanded=True):
    st.markdown(
        "Pick a **budget** and shape the 15 with the options: **archetypes** (cheap / premium / "
        "differential), **include / exclude** specific players, a **declared bench**, the **objective** "
        "(xp / points / value / xgi), and a **build mode** (*Balanced*, *Weekly* = a cheap playing bench, "
        "*Bench Boost* = maximise all 15). Every ⓘ explains a control.\n\n"
        "When you like it: **Download** the `squad.json` (that file *is* your save) and/or **Use this "
        "squad →** to make it this session's active squad."
    )

with st.expander("2 · Make it yours  →  **Squads → My Squad**", expanded=True):
    st.markdown(
        "Your active squad as a **formation pitch**. Edit it: **rename**, **swap** any player "
        "(legality-checked), set the **bench** (pick 4). Every change updates your session and the "
        "**Download**. New team? Switch back to the **Build** view."
    )

with st.expander("3 · Check its health  →  **Squads → Health**"):
    st.markdown(
        "See your squad's **projected xP over the next 5 gameweeks**, the per-GW breakdown, and the "
        "**weak links** worth upgrading. This is the same engine the CLI uses — one honest xP number."
    )

with st.expander("4 · Improve it  →  **Squads → Transfer** and **Captain**"):
    st.markdown(
        "**Transfer** ranks the best single swaps by **XI improvement** (how much a change lifts your best "
        "legal XI) — set your **bank** with the slider, or ask for a **coordinated plan** of 2–3. "
        "**Apply** a swap to your session squad.\n\n"
        "**Captain** ranks who to (vice-)captain this gameweek by expected points, with the opponent + "
        "penalty duty, and a template-vs-differential steer. **Set as captain** to keep it."
    )

with st.expander("5 · Do your research  →  Players · Fixtures · Trending · News"):
    st.markdown(
        "- **Players** — the whole pool (filter by **team / position / player**, sort, page through all) "
        "**plus** the stat views: over/under-performance · Defensive Contribution · clean sheets · xG "
        "(season-to-date). Switch views with the buttons at the top.\n"
        "- **Fixtures** — a colour-coded **difficulty ticker** (pick 1–8 gameweeks).\n"
        "- **Trending** — what the crowd's doing (most-owned · transferred in/out · in-form) + "
        "**Community Signals** (what r/FantasyPL is talking about).\n"
        "- **News** — official injury / doubt / return news, most serious first."
    )

with st.expander("6 · Ask the assistant  →  the **Ask** tab (plain English)"):
    st.markdown(
        "Type a question — the analytics answer and the ✓/⚠ line shows it was checked against the data. "
        "Things to try (copy-paste):"
    )
    st.code(
        'build me a squad for £100m with 3 differentials\n'
        'best differential midfielders under £8m\n'
        'is Haaland worth the money?\n'
        'who should I captain from my-team?\n'
        'what transfer should I make for my-team?\n'
        'which of my-team\'s teams have the best fixtures?\n'
        'when does Arsenal play next?',
        language=None,
    )
    st.markdown(
        "A **build** answer offers **Use this squad →** so it drops into *My Squad* to tweak. Follow-ups "
        "work too: after a pick, ask *\"why?\"* or *\"and the second best?\"*."
    )

with st.expander("7 · Save your team  →  Download, upload, or import by manager-ID"):
    st.markdown(
        "Your squad is per-session (no accounts). **Download** the `squad.json` to keep it — re-**upload** "
        "it from the sidebar next time, or **import your real FPL team by manager-ID** (the sidebar; your "
        "team's numeric id from its URL — picks are public from the GW1 deadline). The same `squad.json` "
        "loads in the CLI too."
    )

st.divider()
st.markdown(
    "**Good to know.** The *Data as of …* caption on each tab shows how fresh the data is. It's "
    "**preseason** now — ownership works, but **transfer momentum, in-season form and live picks light up "
    "at GW1 (2026-08-21)**. Crowd signals are a **lens, not truth**: the analytics decide, the crowd is "
    "context. New here? The **Home** tab has the one-screen overview."
)
