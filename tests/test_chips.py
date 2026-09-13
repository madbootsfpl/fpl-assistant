"""Tests for the chip-strategy assembler (ADR-082).

`chip_advisor` is a pure reduction of the per-GW xP (`by_gameweek`) + the best legal XI — no I/O beyond the
in-memory solve. A crafted `by_gameweek` makes each chip's best GW deterministic, so the four heuristics are
pinned exactly. It must never change the analytics — it only *reads* the xP the caller computed.
"""

from src.analytics import chip_advisor
from src.ui.chips import render_chip_advice


def _squad():
    """A legal 15 (2 GK · 5 DEF · 5 MID · 3 FWD), spread over 6 clubs (≤3/club so an XI is selectable),
    cheap enough that any XI fits the budget."""
    pos = ["GK", "GK"] + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3
    return [{"id": i + 1, "web_name": f"P{i + 1}", "team": f"T{i % 6 + 1}", "position": p,
             "price": 5.0, "total_points": 0}
            for i, p in enumerate(pos)]


def _by_gameweek(owned):
    """Craft per-GW xP so each chip's best GW is unambiguous over GWs [1..4]:
    - GW1: player 8 spikes to 20 (everyone else 2) → the highest single-starter ceiling (Triple Captain).
    - GW2: everyone scores 10 → the biggest all-15 total (Bench Boost).
    - GW3: everyone scores 1 → the weakest single week (Free Hit).
    - GW4: everyone scores 3. Rolling 3-GW XI windows: [1,2,3] vs [2,3,4]; the latter is weaker (Wildcard).
    """
    b = {}
    for p in owned:
        pid = p["id"]
        b[pid] = {1: (20.0 if pid == 8 else 2.0), 2: 10.0, 3: 1.0, 4: 3.0}
    return b


def test_chip_advisor_picks_the_right_gameweek_for_each_chip():
    owned = _squad()
    gameweeks = [1, 2, 3, 4]
    advice = chip_advisor(owned, _by_gameweek(owned), gameweeks)

    tc = advice["triple_captain"]
    assert tc["gameweek"] == 1 and tc["player"]["id"] == 8 and tc["player_xp"] == 20.0

    bb = advice["bench_boost"]
    assert bb["gameweek"] == 2 and bb["squad_total"] == 150.0        # 15 × 10
    assert bb["bench_points"] == 40.0                                # 150 total − 110 best-XI

    fh = advice["free_hit"]
    assert fh["gameweek"] == 3 and fh["xi_total"] == 11.0            # 11 × 1

    wc = advice["wildcard"]
    assert wc["window"] == (2, 4) and wc["gameweeks"] == [2, 3, 4]   # the weaker rolling stretch
    assert wc["avg_xi"] == round((110 + 11 + 33) / 3, 1)


def test_chip_advisor_is_empty_safe():
    assert chip_advisor([], {}, [1, 2]) is None                     # no players
    assert chip_advisor(_squad(), {}, []) is None                   # no gameweeks


def test_wildcard_window_clamps_to_a_short_horizon():
    owned = _squad()
    # Only two GWs → the window can't be 3; it clamps to 2 and spans both.
    b = {p["id"]: {1: 5.0, 2: 1.0} for p in owned}
    wc = chip_advisor(owned, b, [1, 2])["wildcard"]
    assert wc["window"] == (1, 2) and wc["gameweeks"] == [1, 2]


def test_render_chip_advice_shows_every_chip_and_the_caption():
    owned = _squad()
    advice = chip_advisor(owned, _by_gameweek(owned), [1, 2, 3, 4])
    block = render_chip_advice(advice, "TST", horizon=4)
    for label in ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard"):
        assert label in block
    assert "GW1" in block and "GW2" in block                        # the recommended weeks
    assert "in-season" in block                                     # the honest what-sharpens-later note


def test_render_chip_advice_handles_no_advice():
    assert "no data" in render_chip_advice(None, "TST")


def test_render_chip_advice_appends_the_model_note_only_when_explained():
    # US-278: the shared Model note closes an explained answer — here, when per-chip confidences are shown.
    from src.analytics.explain import explain_chips
    owned = _squad()
    advice = chip_advisor(owned, _by_gameweek(owned), [1, 2, 3, 4])
    assert "Model note:" not in render_chip_advice(advice, "TST", horizon=4)          # no confidences
    explained = render_chip_advice(advice, "TST", horizon=4, confidences=explain_chips(advice))
    assert "Model note:" in explained


# ---- one chip per gameweek (ADR-143) -------------------------------------------------

def _flat(owned, gws, value=1.0):
    """Every player the same in every gameweek — a blank canvas to spike."""
    return {p["id"]: dict.fromkeys(gws, value) for p in owned}


def test_two_chips_are_never_advised_for_the_same_gameweek():
    """The bug this ADR exists for. Each chip was chosen independently, so nothing stopped two naming the same
    week — measured at **28% of squads** over an 8-GW horizon. The app was then advising a move FPL forbids,
    contradicting its own rules base ("You can play only one chip per gameweek", `fpl_rules`).

    Built so that GW2 is simultaneously the best Triple Captain week (one huge ceiling) and the best Bench
    Boost week (the bench also peaks) — the exact collision.
    """
    owned, gws = _squad(), [2, 3, 4]
    bg = _flat(owned, gws)
    bg[13] = {2: 20.0, 3: 2.0, 4: 2.0}          # one player with a huge GW2 → TC wants GW2
    for i in (1, 2, 14, 15):                     # …and others peak in GW2 too → BB wants GW2 as well
        bg[i] = {2: 9.0, 3: 1.0, 4: 1.0}

    a = chip_advisor(owned, bg, gws)
    picked = [a["triple_captain"]["gameweek"], a["bench_boost"]["gameweek"], a["free_hit"]["gameweek"]]
    assert len(set(picked)) == 3, f"three chips, three distinct gameweeks — got {picked}"


def test_the_chip_that_cares_LEAST_is_the_one_that_moves():
    """Deliberately not "maximise total xP across the chips". Triple Captain's value is extra captain points,
    Bench Boost's is bench points, Free Hit's is a bad week avoided — **three different currencies**, and
    adding them would look rigorous while meaning nothing. So the chip with the smaller `margin` moves: the
    one whose best week beats its second-best by least, i.e. the one that cares least where it lands.
    """
    owned, gws = _squad(), [2, 3, 4]
    bg = _flat(owned, gws)
    bg[13] = {2: 30.0, 3: 1.0, 4: 1.0}          # TC's GW2 is unmissable — a huge margin
    for i in (1, 2, 14, 15):                     # BB likes GW2 but GW3 is nearly as good — a small margin
        bg[i] = {2: 6.0, 3: 5.9, 4: 1.0}

    a = chip_advisor(owned, bg, gws)
    assert a["triple_captain"]["gameweek"] == 2, "the chip with the bigger margin keeps its week"
    assert a["bench_boost"]["gameweek"] != 2 and "moved_from" in a["bench_boost"]


def test_a_moved_chip_says_where_it_came_from_and_what_it_cost():
    """Shown rather than silently corrected: a manager who reasoned their way to that week deserves to know
    the app agreed and then had to move it. The cost is the honest part — on live data it is 0.0 xP at the
    median, so this is the app declining to advise something illegal, not the app finding points."""
    owned, gws = _squad(), [2, 3, 4]
    bg = _flat(owned, gws)
    bg[13] = {2: 30.0, 3: 1.0, 4: 1.0}
    for i in (1, 2, 14, 15):
        bg[i] = {2: 6.0, 3: 5.0, 4: 1.0}

    bb = chip_advisor(owned, bg, gws)["bench_boost"]
    assert bb["moved_from"] == 2
    assert bb["cost"] >= 0, "the give-up is stated, whatever it is"
    text = render_chip_advice(chip_advisor(owned, bg, gws), "S")
    assert "moved off GW2" in text and "one chip per gameweek" in text


def test_an_untouched_chip_carries_no_moved_note():
    """No collision, no noise — the block reads exactly as it did before for the ~72% of squads unaffected."""
    owned, gws = _squad(), [2, 3, 4]
    bg = _flat(owned, gws)
    bg[13] = {2: 20.0, 3: 1.0, 4: 1.0}          # TC → GW2
    for i in (1, 2, 14, 15):
        bg[i] = {2: 1.0, 3: 9.0, 4: 1.0}        # BB → GW3, no clash

    a = chip_advisor(owned, bg, gws)
    assert "moved_from" not in a["triple_captain"] and "moved_from" not in a["bench_boost"]
    assert "moved off" not in render_chip_advice(a, "S")


def test_fewer_gameweeks_than_chips_does_not_crash_or_invent_a_week():
    """A one-gameweek horizon can't seat three chips. It must degrade, not raise and not fabricate."""
    owned = _squad()
    bg = _flat(owned, [2], value=2.0)
    a = chip_advisor(owned, bg, [2])
    assert a is not None
    assert all(a[k]["gameweek"] == 2 for k in ("triple_captain", "bench_boost", "free_hit"))


def test_the_margins_are_compared_as_a_SHARE_not_raw(monkeypatch):
    """The subtler half of ADR-143, and a mistake made on the way to it.

    The first cut moved "the chip with the smaller `margin`" — comparing raw margins after arguing, one
    paragraph earlier, that the chips are in different currencies. Bench Boost's margin is a whole-squad
    total, so it is *always* the biggest number, and it is inflated by the very player who made Triple Captain
    want that week. Measured on a crafted squad: TC's margin read 24.1 and BB's 29.4 **off the same spike**,
    so the raw rule moved Triple Captain — exactly backwards.

    A share of each chip's own scale is comparable: "gives up 80% of what it came for" means the same thing
    for all three.
    """
    owned, gws = _squad(), [2, 3, 4]
    bg = _flat(owned, gws)
    bg[13] = {2: 30.0, 3: 1.0, 4: 1.0}          # one enormous GW2 — the whole reason to Triple Captain
    for i in (1, 2, 14, 15):
        bg[i] = {2: 6.0, 3: 5.9, 4: 1.0}        # a bench that barely prefers GW2 to GW3

    a = chip_advisor(owned, bg, gws)
    assert a["triple_captain"]["gameweek"] == 2, \
        "TC gives up ~80% of its value by moving; BB gives up almost nothing — TC must keep the week"
    assert a["bench_boost"]["gameweek"] != 2 and "moved_from" in a["bench_boost"]


# ---- ADR-185: the wildcard answers *whether*, not only *when* ----------------------------------

def _squad(n=15, xp=20.0, price=6.0):
    pos = ["GK"] * 2 + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3
    return [{"id": i, "web_name": f"P{i}", "position": pos[i % len(pos)], "team": f"T{i % 6}",
             "price": price, "status": "a", "chance": None, "total_points": 0} for i in range(n)]


def test_the_wildcard_reports_what_a_rebuild_is_worth():
    """ADR-185, owner-reported from a two-team A/B he was 40 points ahead in: the advisor said *"Wildcard
    GW5-7, your weakest stretch · Confidence 42/100 · Low"* while his squad overlapped an optimal build by
    **3 of 15** and carried **£14.1m that could not play**.

    `chips.py` chose the week by the lowest rolling window of best-XI xP — *when are your fixtures worst* and
    nothing else. **It never asked what a wildcard would gain.**

    > A recommendation that measures only *when* will present itself as an answer to *whether*.
    """
    from src.analytics.chips import chip_advisor, rebuild_value

    owned = _squad()
    market = owned + [{**p, "id": 100 + p["id"], "web_name": f"Better{p['id']}"} for p in owned]
    xp = {p["id"]: 10.0 for p in owned} | {100 + p["id"]: 30.0 for p in owned}

    reb = rebuild_value(owned, market, xp, budget=200.0)
    assert reb["gain"] > 0 and reb["overlap"] == 0, reb
    assert reb["current"] == 150.0 and reb["rebuilt"] == 450.0    # 15 × 10 vs 15 × 30

    # ⚠️ `idle_spend` computed from the data, not handed in. The renderer test passes a literal, so it never
    # exercised this — a mutation hard-coding it to 0.0 passed. Two forwards priced at 6.0 projecting nothing
    # is £12.0m tied up, which is the concrete half of the gap and the part a reader can check on their pitch.
    dead = [p for p in owned if p["position"] == "FWD"][:2]
    xp_dead = {**xp, **{p["id"]: 0.0 for p in dead}}
    assert rebuild_value(owned, market, xp_dead, budget=200.0)["idle_spend"] == 12.0
    assert rebuild_value(owned, market, xp, budget=200.0)["idle_spend"] == 0.0, \
        "a squad where everyone contributes has no idle money"

    by_gw = {p["id"]: {1: 1.0, 2: 1.0, 3: 1.0} for p in market}
    advice = chip_advisor(owned, by_gw, [1, 2, 3], rebuild=reb)
    wc = advice["wildcard"]
    assert wc["gain"] == reb["gain"] and wc["overlap"] == 0 and wc["squad_size"] == 15
    assert wc["window"], "it must still say WHEN — the fixture answer is not replaced, it is demoted"


def test_the_wildcard_reads_exactly_as_before_without_a_rebuild():
    """The compatibility contract. `rebuild=None` must leave every existing caller untouched — the
    enhancement degrades, the answer does not. A squad that cannot be priced (no `price` on the rows) takes
    this path rather than failing the whole chip answer."""
    from src.analytics.chips import chip_advisor

    owned = _squad()
    by_gw = {p["id"]: {1: 5.0, 2: 1.0, 3: 1.0} for p in owned}
    wc = chip_advisor(owned, by_gw, [1, 2, 3])["wildcard"]
    for key in ("gain", "overlap", "idle_spend"):
        assert key not in wc, f"{key} must be absent when no rebuild was priced"
    assert "window" in wc and "avg_xi" in wc


def test_the_wildcard_confidence_measures_the_gap_not_the_fixture_margin():
    """⚠️ **Two different questions were sharing one number.** `margin` is how clearly one *window* beats
    another — genuinely low when the weeks are close, which they usually are. But the decision is not *"which
    week"*, it is *"is a rebuild worth it"*, and on the owner's squad a **+99.6 xP** rebuild rendered as
    *Confidence 42/100 · Low* — least confident exactly when the case was overwhelming.
    """
    from src.analytics.explain import rebuild_confidence

    assert rebuild_confidence(99.6, 275.3) >= 90, "an overwhelming rebuild must read High"
    assert rebuild_confidence(5.0, 300.0) <= 50, "a healthy squad must read Low — the advice is *don't*"
    assert rebuild_confidence(0.0, 300.0) <= 45
    assert rebuild_confidence(None, None) >= 1, "empty-safe"
    # Monotonic: a bigger gap can never read as less confident.
    ladder = [rebuild_confidence(g, 300.0) for g in (0, 10, 25, 50, 100)]
    assert ladder == sorted(ladder), ladder

    # ⚠️ …and the WIRING, through `explain_chips`. Calling `rebuild_confidence` alone left the branch that
    # selects it untested: a mutation disabling it (falling back to the fixture margin) passed everything
    # above. **Testing a component is not testing that anything uses it.**
    from src.analytics.chips import chip_advisor
    from src.analytics.explain import explain_chips

    owned = _squad()
    by_gw = {p["id"]: {1: 5.0, 2: 4.9, 3: 4.8} for p in owned}      # near-flat weeks → a tiny fixture margin
    reb = {"current": 100.0, "rebuilt": 199.6, "gain": 99.6, "overlap": 3,
           "squad_size": 15, "idle_spend": 14.1}
    with_reb = explain_chips(chip_advisor(owned, by_gw, [1, 2, 3], rebuild=reb))["wildcard"]
    without = explain_chips(chip_advisor(owned, by_gw, [1, 2, 3]))["wildcard"]
    assert with_reb["confidence"] >= 90 and with_reb["band"] == "High", with_reb
    assert without["confidence"] < 60, ("with no rebuild it must fall back to the fixture margin, which on "
                                        f"near-flat weeks is Low: {without}")


def test_the_rebuild_gain_is_labelled_as_the_chips_value_not_a_squad_score():
    """⚠️ The rebuild is unconstrained by transfers — right for a chip that lifts that constraint, and an
    overstatement of anything else. The copy must say what a **wildcard** is worth, and must not imply the
    squad is reachable by other means."""
    from src.ui.chips import render_chip_advice

    owned = _squad()
    by_gw = {p["id"]: {1: 5.0, 2: 1.0, 3: 1.0} for p in owned}
    reb = {"current": 100.0, "rebuilt": 199.6, "gain": 99.6, "overlap": 3,
           "squad_size": 15, "idle_spend": 14.1}
    from src.analytics.chips import chip_advisor
    out = render_chip_advice(chip_advisor(owned, by_gw, [1, 2, 3], rebuild=reb), "S", horizon=3)
    assert "worth +99.6 xP" in out, out
    assert "you keep only 3 of 15" in out
    assert "£14.1m of your squad cannot play" in out
    assert "weakest stretch" in out, "the fixture window survives — it answers a real question, just not the first"
