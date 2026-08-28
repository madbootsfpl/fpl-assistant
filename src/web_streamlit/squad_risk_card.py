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
    # ADR-146 — the crowd knows things the feed doesn't. Shown ABOVE the table, because it is the only signal
    # here the app cannot derive for itself, and a percentile column is the wrong place to put news.
    from src.analytics.crowd import exodus_note

    # ADR-151 — the headlines read at refresh time. Empty on a snapshot built without a language model, in
    # which case every note below reads exactly as it did before (ADR-146).
    _events = {}
    try:
        from src.storage import Storage
        _store = Storage()
        _events = _store.headline_events_by_id()
        _store.close()
    except Exception:                                    # noqa: BLE001 — a bonus, never load-bearing
        _events = {}
    for r in rows:
        if r.get("exodus"):
            note = exodus_note({"web_name": r["web_name"]}, r["exodus"], _events.get(r["id"]))
            if note:
                st.warning(f"📉 {note}")
    st.caption("**Attention** blends the chance a player misses the 60-minute appearance points with how hard "
               "their run is *relative to the league* — minutes weigh more, because a player who doesn't play "
               "scores nothing while a hard fixture only shortens the odds. **Driver** names whichever "
               "contributes more — or **Crowd**, when a player our data says is fine is being sold heavily "
               "anyway, which is the one thing here we can only learn from other managers.")
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
                                  "they are.",
                     "Under 60": "The chance they don't reach 60 minutes, and so miss the second "
                                 "appearance point.",
                     "From": "What that chance is based on: their own per-gameweek record, or how often "
                             "they started last season.",
                     "Fixtures": "How hard their club's next 5 are, as a percentile across the league.",
                     "Driver": "Which signal is the bigger contributor — or **Crowd** when managers are "
                               "selling them and nothing in the data explains why.",
                 }))
    if unassessed:
        st.caption(f"🌱 {unassessed} player(s) show **—**: new to the league, so there's no minutes record to "
                   "judge them on yet. Unknown, not risky — their attention comes from fixtures alone.")


FP_CSS = """
<style>
.fp-wk{display:grid;grid-template-columns:46px 1fr auto;align-items:center;gap:10px;margin:6px 0;}
.fp-gw{color:#aab6c6;font-size:.76rem;font-weight:800;font-variant-numeric:tabular-nums;}
.fp-bt{background:rgba(255,255,255,.06);border-radius:999px;height:9px;overflow:hidden;display:flex;}
.fp-bh{background:linear-gradient(90deg,#f0b429,#f98a8a);height:100%;}
.fp-bb{background:#f98a8a;height:100%;}
.fp-bd{background:#5eead4;height:100%;}
.fp-tag{font-size:.68rem;font-weight:800;letter-spacing:.04em;padding:1px 7px;border-radius:999px;
white-space:nowrap;}
.fp-tag.hard{background:rgba(240,180,41,.16);color:#f0b429;}
.fp-tag.blank{background:rgba(249,138,138,.16);color:#f98a8a;}
.fp-tag.double{background:rgba(94,234,212,.14);color:#5eead4;}
.fp-tag.ok{background:rgba(255,255,255,.05);color:#7c8899;}
.fp-hl{color:#cdd6e2;font-size:.84rem;line-height:1.5;margin-bottom:12px;}
.fp-hl strong{color:#f2f6fb;}
.fp-ft{color:#7c8899;font-size:.74rem;margin-top:12px;padding-top:10px;
border-top:1px solid rgba(255,255,255,.07);}
</style>
"""


def _md_bold(text):
    import re
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def forward_plan_html(plan, squad_size: int = 15) -> str:
    """The weeks ahead: one bar per gameweek showing how much of your squad is exposed, and a headline.

    The bar is **fixture exposure**, not projected points — six weeks of a real squad sat inside ±3% on xP
    while hard-fixture counts swung 2→7, so exposure is the signal worth the width (ADR-131). The xP range is
    stated in the footnote, and says so when it's flat rather than letting a 3% wobble look like a forecast.
    """
    weeks = plan.get("weeks") or []
    if not weeks:
        return ""
    rows = ""
    for w in weeks:
        n = max(1, squad_size)
        seg = ""
        for cls, names in (("bb", w["blank"]), ("bh", w["hard"]), ("bd", w["double"])):
            if names:
                seg += f'<div class="fp-{cls}" style="width:{min(100, 100 * len(names) / n):.0f}%"></div>'
        tag_cls, tag = ("ok", "even")
        if w["flag"] == "blank":
            tag_cls, tag = "blank", f"{len(w['blank'])} blank"
        elif w["flag"] == "double":
            tag_cls, tag = "double", f"{len(w['double'])} double"
        elif w["flag"] == "hard":
            tag_cls, tag = "hard", f"{len(w['hard'])} hard"
        elif w["hard"]:
            tag = f"{len(w['hard'])} hard"
        rows += (f'<div class="fp-wk"><div class="fp-gw">GW{w["event"]}</div>'
                 f'<div class="fp-bt">{seg}</div>'
                 f'<div class="fp-tag {tag_cls}">{tag}</div></div>')
    xp = plan.get("xp") or {}
    foot = ""
    if xp:
        flat = (" — barely moves across these weeks, which is normal: fixture difficulty shifts a squad's "
                "projection by a few percent, not a few players." if xp.get("flat") else "")
        foot = (f'<div class="fp-ft">Projected {xp["min"]}–{xp["max"]} xP per gameweek '
                f'(average {xp["avg"]}){flat}</div>')
    return (SR_CSS + FP_CSS + '<div class="sq-card"><div class="sq-ti">📅 The weeks ahead</div>'
            f'<div class="fp-hl" style="margin-top:10px">{_md_bold(plan.get("headline", ""))}</div>'
            f'{rows}{foot}</div>')


def render_forward_plan(plan, squad_size: int = 15) -> None:
    st.markdown(forward_plan_html(plan, squad_size), unsafe_allow_html=True)
