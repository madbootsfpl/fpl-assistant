"""Tests for the curated FPL-rules knowledge base (Sprint 100, ADR-085).

`match_rules` is a pure keyword matcher over authoritative facts — the assistant answers rules questions from
*these* facts, never the LLM's memory. Every fact must be a non-empty string.
"""

from src.fpl_rules import RULES, match_rules


def test_match_rules_finds_the_right_topic():
    def topics(q):
        return [t for t, _ in match_rules(q)]
    assert topics("how does bench boost work?") == ["chips"]
    assert topics("how do transfers work?") == ["transfers"]
    assert topics("when is the deadline?") == ["deadline"]
    assert "clean_sheets" in topics("how many points for a clean sheet?")   # (also 'scoring' — a fuller answer)
    assert "squad_rules" in topics("what is the budget and max per club?")


def test_match_rules_can_return_several_topics_capped():
    hits = match_rules("how do chips and transfers and price changes work?", limit=4)
    topics = [t for t, _ in hits]
    assert {"chips", "transfers", "price_changes"} <= set(topics)
    assert len(match_rules("how do chips and transfers and price changes work?", limit=2)) == 2   # cap honoured


def test_match_rules_empty_when_nothing_matches():
    assert match_rules("what's the meaning of life?") == []      # → the caller goes free-form (US-260)
    assert match_rules("") == []                                 # empty-safe


def test_match_rules_covers_the_new_topics():
    # US-282: the KB grew — each new topic answers its natural question.
    def topic(q):
        return [t for t, _ in match_rules(q)]
    assert "flags" in topic("what does the yellow flag mean?")
    assert "preseason_transfers" in topic("can I make unlimited transfers before gameweek 1?")
    assert "chip_limits" in topic("can I play two chips in one gameweek?")
    assert "bench_points" in topic("do bench players score points?")
    assert "wildcard_timing" in topic("how many wildcards do I get?")
    assert "leagues" in topic("how does a head-to-head league work?")
    assert "ranking" in topic("how is my overall rank calculated?")
    assert "team_value" in topic("what is my selling price?")


def test_rules_topics_are_unique():
    topics = [e["topic"] for e in RULES]
    assert len(topics) == len(set(topics))       # no duplicate topic ids


def test_render_rules_bullets_a_multi_item_fact():
    # US-283 (tester feedback): a list fact (chips) reads item-per-line; a single-concept fact is one bullet.
    from src.ui.rules import render_rules
    chips = render_rules(match_rules("how does bench boost work?"))
    assert chips.startswith("FPL rules") and "Chips:" in chips
    for chip in ("Wildcard", "Free Hit", "Bench Boost", "Triple Captain"):
        assert f"• {chip}" in chips                              # each chip on its own bullet line
    assert render_rules(match_rules("when is the deadline?")).count("•") == 1   # single fact → one bullet


def test_every_rule_has_a_nonempty_fact():
    assert RULES and all(e["topic"] and e["cues"] and e["fact"].strip() for e in RULES)
