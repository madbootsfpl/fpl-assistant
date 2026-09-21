"""The exodus threshold is bound to the whole board **at every call site** (ADR-210).

⭐⭐ **ADR-184's rule: a guard against a claim must sweep for the claim, not check the places you thought of.**
A retired claim once survived 14 days on six surfaces because two separate guards both happened to check the
same two files. So this does not import the call sites — it *greps* for them, and the grep is the test.

There are two claims to keep true, and they fail in opposite directions:

1. **Nobody calls `crowd_exodus` directly.** It takes a required threshold now, so a direct call is not
   silently wrong — but it is a call site that has decided for itself where the cut falls, which is the
   fragmentation ADR-181 wrote up (*"one recipe is a claim about every call site, not about the function"*).
2. **`exodus_detector` is handed the whole board.** This one *is* silent: bind it to `owned` or to a filtered
   view and nothing raises — you simply get the worst tenth of fifteen players, or a manufactured exodus
   inside every filter. ⚠️ The percentile is a claim about the league.
"""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

# The whole-board variable at every current call site. Not a style rule: it is the assertion. A future call
# site that legitimately needs another name must come here and say so, which is the point — the population
# this is bound to is the one decision that cannot be checked by reading the line it appears on.
WHOLE_BOARD = {
    "players",
    # ⭐ The service layer's loader (ADR-219/220) reads `get_players()` unfiltered into `Loaded.players` and
    # hands the whole thing on. Registered here rather than renamed at the call site, because **coming here
    # to say so is the mechanism** — this guard caught the new endpoint on the day it was written, which is
    # the pattern working exactly as ADR-210 intended.
    "data.players",
}


def _src_files():
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_production_code_calls_crowd_exodus_directly():
    """Everything goes through `exodus_detector`, which binds the live threshold once (ADR-181/210)."""
    offenders = []
    for path in _src_files():
        if path.name == "crowd.py":
            continue                     # where `exodus_detector` itself lives
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            if re.search(r"\bcrowd_exodus\s*\(", line):
                offenders.append(f"{path.relative_to(SRC.parent.parent)}:{i}: {line.strip()}")
    assert not offenders, (
        "call `exodus_detector(players)` and use the closure it returns:\n" + "\n".join(offenders))


def test_every_detector_is_bound_to_the_whole_board_and_never_to_a_filtered_view():
    """⚠️ The silent failure. `exodus_detector(owned)` does not raise — it takes the worst tenth of a squad.
    `exodus_detector(apply_filter(players, sel))` does not raise either — it invents a worst tenth inside
    whatever the reader has filtered to, so narrowing the Signals page to one club would report an exodus at
    that club every week of the season."""
    bad = []
    found = 0
    for path in _src_files():
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            for arg in re.findall(r"\bexodus_detector\s*\(\s*([^)]*)\)", line):
                found += 1
                if arg.strip() not in WHOLE_BOARD:
                    bad.append(f"{path.relative_to(SRC.parent.parent)}:{i}: exodus_detector({arg.strip()})")
    assert found >= 5, f"expected the detector at every exodus surface, found {found} — did a call site vanish?"
    assert not bad, (
        "the exodus threshold is a percentile of the LEAGUE; these bind it to something smaller:\n"
        + "\n".join(bad))


def test_the_retired_constant_is_gone_from_the_whole_repo():
    """⭐ ADR-184 again: *when retiring a claim, grep for it and make the grep the test.* `EXODUS_PRESSURE`
    was a number measured in one hour of GW1 and applied to every hour of every week after it, so a stray
    import or a lingering comparison would re-teach exactly what the ADR removed.

    ⚠️ **It greps for the constant in USE, not for the word.** ADR-178's first anti-pattern is a word
    blacklist standing in for a claim: the name still appears — inside backticks — in the comments and ADRs
    that explain *why* it went, and deleting that prose would destroy the record rather than protect it.
    ⭐ *A history of a decision is not a repetition of it.*
    """
    import src.analytics.crowd as crowd_mod

    assert not hasattr(crowd_mod, "EXODUS_PRESSURE"), "the fixed threshold must not be importable"

    root = SRC.parent
    offenders = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or "venv" in path.parts or path.name == Path(__file__).name:
            continue
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            code = re.sub(r"`[^`]*`", "", line)          # drop backticked prose — that is the record
            if "EXODUS_PRESSURE" in code:
                offenders.append(f"{path.relative_to(root)}:{i}: {line.strip()}")
    assert not offenders, "the fixed threshold is retired (ADR-210):\n" + "\n".join(offenders)
