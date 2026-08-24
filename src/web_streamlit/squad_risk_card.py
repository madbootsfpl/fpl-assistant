"""My Squad ▸ Health: the ⚠️ Risk Monitor table and the 🧬 Squad DNA card (ADR-130).

Display-only over `analytics.squad_risk`. Health already said how good a squad was; these say **what needs
attention this week** and **how the 15 look together**.
"""

import streamlit as st

from src.web_streamlit.formats import column_config

SR_CSS = """
<style>
.sq-card{background:linear-gradient(180deg,#111821,#0c121a);border:1px solid rgba(255,255,255,.09);
border-radius:14px;padding:16px 18px;margin:10px 0 4px;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.sq-hd{display:flex;align-items:baseline;gap:12px;margin-bottom:12px;}
.sq-gr{font-weight:800;font-size:2rem;line-height:1;color:#5eead4;}
.sq-ti{font-weight:800;font-size:.72rem;letter-spacing:.08em;color:#aab6c6;text-transform:uppercase;}
.sq-sc{color:#7c8899;font-size:.74rem;font-weight:600;}
.sq-bar{display:grid;grid-template-columns:78px 1fr 42px;align-items:center;gap:10px;margin:7px 0;}
.sq-bl{color:#aab6c6;font-size:.76rem;font-weight:700;}
.sq-bt{background:rgba(255,255,255,.06);border-radius:999px;height:8px;overflow:hidden;}
.sq-bf{height:100%;border-radius:999px;background:linear-gradient(90deg,#7c5cff,#5eead4);}
.sq-bv{color:#f2f6fb;font-size:.76rem;font-weight:700;text-align:right;
font-variant-numeric:tabular-nums;}
.sq-ed{margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.07);}
.sq-e{color:#cdd6e2;font-size:.8rem;margin:4px 0;}
</style>
"""


def squad_dna_html(dna) -> str:
    """The squad's grade, four bars and its grounded edge lines. An unmeasurable bar is left out rather than
    drawn at zero — an absent average is not a score of nothing (the rule this project keeps re-learning)."""
    bars = ""
    for label, pct in (dna.get("bars") or {}).items():
        if pct is None:
            continue
        bars += (f'<div class="sq-bar"><div class="sq-bl">{label}</div>'
                 f'<div class="sq-bt"><div class="sq-bf" style="width:{max(2, pct)}%"></div></div>'
                 f'<div class="sq-bv">{pct}</div></div>')
    edges = "".join(f'<div class="sq-e">• {e}</div>' for e in (dna.get("edges") or []))
    edge_block = f'<div class="sq-ed">{edges}</div>' if edges else ""
    return (SR_CSS + '<div class="sq-card"><div class="sq-hd">'
            f'<div class="sq-gr">{dna.get("grade", "—")}</div>'
            f'<div><div class="sq-ti">🧬 Squad DNA</div>'
            f'<div class="sq-sc">average percentile {dna.get("score", 0)} · vs the whole pool</div></div>'
            f'</div>{bars}{edge_block}</div>')


def render_squad_dna(dna) -> None:
    st.markdown(squad_dna_html(dna), unsafe_allow_html=True)


def _pct(v):
    return "—" if v is None else f"{v:.0%}"


def render_risk_monitor(rows, badges=None) -> None:
    """The triage table — most in need of attention first, not best first."""
    st.markdown("**⚠️ Risk Monitor** — who needs attention, most first")
    if not rows:
        st.info("No players to assess yet.")
        return
    unassessed = sum(1 for r in rows if r["minutes_basis"] is None)
    st.caption("**Attention** blends the chance a player misses the 60-minute appearance points with how hard "
               "his run is *relative to the league* — minutes weigh more, because a player who doesn't play "
               "scores nothing while a hard fixture only shortens the odds. **Driver** names whichever "
               "contributes more.")
    table = [{
        "badge": (badges or {}).get(r["team"], ""), "Player": r["web_name"], "Team": r["team"],
        "Pos": r["position"], "Attention": round(r["attention"] * 100),
        "Under 60": _pct(r["minutes_risk"]), "From": r["minutes_basis"] or "—",
        "Fixtures": _pct(r["fixture_risk"]), "Driver": r["driver"],
    } for r in rows]
    labels = ["badge", "Player", "Team", "Pos", "Attention", "Under 60", "From", "Fixtures", "Driver"]
    st.dataframe(table, hide_index=True, width="stretch", height=min(520, 40 + 36 * len(table)),
                 column_config=column_config(labels, help={
                     "Attention": "How much this player might cost you — higher needs a look. Not how good "
                                  "he is.",
                     "Under 60": "The chance he doesn't reach 60 minutes, and so misses the second "
                                 "appearance point.",
                     "From": "What that chance is based on: his own per-gameweek record, or how often he "
                             "started last season.",
                     "Fixtures": "How hard his club's next 5 are, as a percentile across the league.",
                     "Driver": "Which of the two is the bigger contributor.",
                 }))
    if unassessed:
        st.caption(f"🌱 {unassessed} player(s) show **—**: new to the league, so there's no minutes record to "
                   "judge them on yet. Unknown, not risky — their attention comes from fixtures alone.")
