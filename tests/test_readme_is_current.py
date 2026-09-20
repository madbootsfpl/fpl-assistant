"""The README's claims about the project have to stay true.

⭐⭐ **A number a document states is a claim the project makes about itself, and nothing was checking these.**
The README spent weeks advertising *"121 ADRs · 1091 tests"* while the repo held 212 and 2,035 — and said
*"🚨 GW1 = 2026-08-21 (tomorrow)"* a month after GW1 was played. Neither is a bug; both make the front page
of the project misleading to the first person who reads it, which for a README is the whole job.

⚠️ **Tolerances, not exact matches.** The test count moves on most commits, and a guard that fails on every
commit gets deleted or `-x`'d rather than obeyed. These bands are wide enough to ignore normal growth and
narrow enough to catch the drift that actually happened (a doubling).
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()


def _claimed(pattern):
    m = re.search(pattern, README)
    assert m, f"the README no longer states this at all: {pattern}"
    return int(m.group(1).replace(",", ""))


def test_the_adr_count_is_right():
    actual = len(list((ROOT / "docs" / "06_Decisions").glob("ADR-*.md")))
    claimed = _claimed(r"\*\*([\d,]+) ADRs")
    assert abs(claimed - actual) <= 5, (
        f"README says {claimed} ADRs, the repo has {actual}. Update the line in README.md.")


def test_the_test_count_is_roughly_right():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"],
                         cwd=ROOT, capture_output=True, text=True, timeout=600).stdout
    m = re.search(r"(\d+) tests? collected", out)
    assert m, f"could not read a collection count from pytest:\n{out[-500:]}"
    actual, claimed = int(m.group(1)), _claimed(r"([\d,]+) tests · CI green")
    assert abs(claimed - actual) / actual < 0.15, (
        f"README claims {claimed:,} tests, pytest collects {actual:,} "
        f"({abs(claimed-actual)/actual:.0%} out). Update the line in README.md.")


def test_it_does_not_still_describe_the_season_as_unstarted():
    """The specific embarrassment: a front page that says the season starts tomorrow, a month in.

    ⭐ Phrased as *"no unplayed-GW1 language"* rather than a date check, because the failure was never the
    date being wrong — it was the **tense**. A doc can carry a correct date inside a claim that has expired.
    """
    for phrase in ("GW1 = 2026-08-21 (tomorrow)", "gated until GW1", "the season lights up"):
        assert phrase not in README, (
            f"README still talks as though GW1 has not happened: {phrase!r}")


def test_it_does_not_tell_you_reseed_is_part_of_deploying():
    """ADR-211 replaced the manual snapshot with a scheduled pipeline. `reseed` still exists — it rebuilds
    the SQLite fixture the tests run against — so the word is fine; presenting it as a *deploy step* is not.

    ⚠️ A grep for `reseed` alone would fail on the honest mention. What makes it wrong is the claim attached.
    """
    for line in README.splitlines():
        if "reseed" in line and "TESTS ONLY" not in line:
            assert "deploy" not in line.lower(), (
                f"README presents reseed as a deploy step, which ADR-211 removed:\n  {line.strip()}")
