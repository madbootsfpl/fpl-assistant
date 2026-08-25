"""Tests for the value analytics — points-per-£m, ranking, and the value frontier (ADR-138).

The frontier tests carry the reasoning that a chart cannot: *why* "nobody cheaper scores more" beats
points-per-£m as a definition of value, and why the verdict sentence lives in analytics rather than in the
view. A tooltip is a claim about the data, and claims get tested.
"""

from src.analytics.value import frontier_verdict, points_per_million, rank_players, value_frontier


def test_points_per_million_basic():
    assert points_per_million(200, 8.0) == 25.0


def test_points_per_million_zero_price_is_undefined():
    assert points_per_million(100, 0) is None


def test_points_per_million_missing_price_is_undefined():
    assert points_per_million(100, None) is None


def test_rank_by_value_puts_best_value_first():
    rows = [
        {"web_name": "Expensive", "price": 15.0, "total_points": 150},  # 10.0 / £m
        {"web_name": "Cheap", "price": 5.0, "total_points": 100},       # 20.0 / £m
    ]
    ranked = rank_players(rows, sort_by="value")

    assert ranked[0]["web_name"] == "Cheap"
    assert ranked[0]["value"] == 20.0


def test_rank_by_value_sorts_undefined_last():
    rows = [
        {"web_name": "NoPrice", "price": 0, "total_points": 100},   # undefined
        {"web_name": "Normal", "price": 5.0, "total_points": 50},   # 10.0 / £m
    ]
    ranked = rank_players(rows, sort_by="value")

    assert ranked[0]["web_name"] == "Normal"
    assert ranked[-1]["value"] is None


def test_rank_by_points_puts_top_scorer_first():
    rows = [
        {"web_name": "Low", "price": 5.0, "total_points": 100},
        {"web_name": "High", "price": 15.0, "total_points": 150},
    ]
    ranked = rank_players(rows, sort_by="points")

    assert ranked[0]["web_name"] == "High"


# ---- the value frontier (ADR-138) ----------------------------------------------------



def _v(pid, name, price, pos="MID", team="ARS"):
    return {"id": pid, "web_name": name, "price": price, "position": pos, "team": team}


def test_the_frontier_is_nobody_cheaper_scores_more():
    """The definition, and why it isn't points-per-£m.

    A ratio flatters cheap players who score a little — a £4.0 player on 4 xP beats Haaland on xP/£m and is
    not a better pick. "Nobody cheaper scores more" has no such failure mode: it is a claim you can act on.
    """
    rows = [_v(1, "Cheap", 4.0), _v(2, "Mid", 6.0), _v(3, "Dear", 10.0), _v(4, "Waste", 8.0)]
    xp = {1: 5.0, 2: 12.0, 3: 20.0, 4: 9.0}          # Waste costs more than Mid and scores less
    by_name = {e["player"]["web_name"]: e for e in value_frontier(rows, xp)}

    assert [n for n, e in by_name.items() if e["frontier"]] == ["Cheap", "Mid", "Dear"]
    assert by_name["Waste"]["frontier"] is False, "someone cheaper scores more — that is the whole test"


def test_a_tie_at_one_price_admits_only_the_best_of_them():
    """Two players at the same price cannot both be "nobody cheaper scores more"."""
    rows = [_v(1, "A", 5.0), _v(2, "B", 5.0), _v(3, "C", 5.0)]
    on = {e["player"]["web_name"] for e in value_frontier(rows, {1: 10.0, 2: 10.0, 3: 4.0}) if e["frontier"]}
    assert len(on) == 1 and on <= {"A", "B"}


def test_the_peer_median_is_what_turns_a_dot_into_a_sentence():
    """"16.9 xP" means nothing until you know the median player at that price manages 5.0."""
    rows = [_v(i, f"P{i}", 4.5) for i in range(1, 6)]
    entries = {e["player"]["web_name"]: e for e in value_frontier(rows, {1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0, 5: 20.0})}
    assert entries["P5"]["peer_median"] == 3.0
    assert entries["P5"]["edge"] == 17.0
    assert entries["P1"]["edge"] == -2.0, "below-median players must read as below median, not as zero"


def test_prices_are_grouped_without_trusting_float_equality():
    """FPL prices land on 0.1 boundaries and float equality is not something to bet a peer group on."""
    rows = [_v(1, "A", 4.1 + 0.4), _v(2, "B", 4.5), _v(3, "C", 4.5)]      # 4.1+0.4 != 4.5 in binary float
    entries = value_frontier(rows, {1: 3.0, 2: 9.0, 3: 6.0})
    assert {e["peers"] for e in entries} == {3}, "all three are £4.5 players and must share a peer group"


def test_a_player_with_no_xp_entry_is_scored_zero_not_dropped():
    """A real squad option that happens to be worth nothing. Hiding him would flatter the pool."""
    entries = value_frontier([_v(1, "A", 5.0), _v(2, "Ghost", 5.0)], {1: 8.0})
    assert {e["player"]["web_name"] for e in entries} == {"A", "Ghost"}
    assert next(e for e in entries if e["player"]["web_name"] == "Ghost")["xp"] == 0.0


def test_players_without_a_price_cannot_be_positioned_so_are_left_out():
    assert value_frontier([{"id": 1, "web_name": "X", "price": None, "position": "MID"}], {1: 5.0}) == []
    assert value_frontier([], {}) == []


def test_the_verdict_is_a_finding_not_a_coordinate():
    """The MadBoots difference, and the only part of this chart a rival can't copy from a screenshot."""
    rows = [_v(i, f"P{i}", 4.5, pos="DEF") for i in range(1, 5)] + [_v(9, "Mitchell", 4.5, pos="DEF")]
    entry = next(e for e in value_frontier(rows, {1: 4.0, 2: 5.0, 3: 5.0, 4: 6.0, 9: 16.9})
                 if e["player"]["web_name"] == "Mitchell")
    verdict = frontier_verdict(entry, horizon=5)
    assert "16.9 xP over 5 GW" in verdict
    assert "+11.9 xP vs the median £4.5 player" in verdict
    assert "nobody cheaper scores more" in verdict


def test_the_only_player_at_a_price_is_not_told_he_is_average():
    """Haaland is the only £15.5 player, so "exactly the median for £15.5" is a fact about a group of one.
    True, and useless — the sort of sentence that makes a reader stop trusting the others."""
    entry = next(e for e in value_frontier([_v(1, "Haaland", 15.5, pos="FWD"), _v(2, "X", 5.0)], {1: 28.4, 2: 4.0})
                 if e["player"]["web_name"] == "Haaland")
    assert entry["peers"] == 1
    v = frontier_verdict(entry)
    assert "the only player at £15.5" in v and "median" not in v


def test_an_unproven_player_cannot_hold_the_frontier():
    """The owner's catch, as a test (ADR-138).

    A £4.0 backup keeper had 9.9 xP from 35 starts at a former club and sat on the frontier, while the keeper
    who actually played that gameweek scored 2.3. "Nobody cheaper scores more" is a claim about **who to
    buy**, and it must not be made on behalf of someone with evidence he does not start — the frontier's cheap
    end is exactly where the xMins model is weakest, because the in-season minutes share is deferred until
    there are enough gameweeks to trust it (ADR-125).
    """
    rows = [_v(1, "Backup", 4.0), _v(2, "Starter", 4.0), _v(3, "Dearer", 5.0)]
    xp = {1: 9.9, 2: 7.0, 3: 8.0}

    without = {e["player"]["web_name"] for e in value_frontier(rows, xp) if e["frontier"]}
    assert without == {"Backup"}, "unfiltered, the backup takes the frontier — the reported bug"

    entries = value_frontier(rows, xp, unproven={1})
    on = {e["player"]["web_name"] for e in entries if e["frontier"]}
    assert on == {"Starter", "Dearer"}, "he steps off, and stops blocking everyone dearer than him"

    backup = next(e for e in entries if e["player"]["web_name"] == "Backup")
    assert backup["unproven"] is True and backup["xp"] == 9.9, \
        "marked, not deleted and not silently discounted — the number isn't wrong, it's unsupported"


def test_an_unproven_player_is_still_a_price_peer():
    """He is still someone you could buy at that price. Leaving him in the peer median makes every edge
    slightly smaller — the conservative direction, which is the one to fall in."""
    rows = [_v(1, "Backup", 4.5), _v(2, "A", 4.5), _v(3, "B", 4.5)]
    entries = value_frontier(rows, {1: 10.0, 2: 4.0, 3: 6.0}, unproven={1})
    assert next(e for e in entries if e["player"]["web_name"] == "A")["peer_median"] == 6.0
    assert all(e["peers"] == 3 for e in entries)
