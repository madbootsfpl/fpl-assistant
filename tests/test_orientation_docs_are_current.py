"""The documents that orient a reader must not describe a past version of the project (ADR-295).

⭐⭐ **These four are the ones a person — or a session — reads first**, which makes them the worst placed
to be out of date. `CLAUDE.md` is loaded into every session and said *"Next: a Flutter mobile app"* for
three weeks after the app was on nine phones; `PROJECT_STATUS`'s **Current Story** claimed 118 ADRs at
295 and pointed at GW1 as a future marker five weeks after it was played.

⚠️ *A document that orients you is the one worst placed to be out of date* — every other stale file is
read by someone already holding the context to notice.

These check claims against the repo, never against prose. ⭐ *A doc test that reads like a style guide is
a doc test that gets suppressed.*
"""

from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIENTING = [
    "CLAUDE.md",
    "README.md",
    "docs/00_Project/PROJECT_STATUS.md",
    "docs/04_Roadmap/Roadmap.md",
]


def _text(name: str) -> str:
    return (ROOT / name).read_text()


def test_nothing_calls_the_mobile_app_unbuilt() -> None:
    """⚠️ The exact drift that happened, derived from the repo rather than remembered.

    ⭐ The app is built if `mobile/lib/main.dart` exists — so the claim and its refutation are in the same
    test, and nobody has to remember to come back and delete this.
    """
    if not (ROOT / "mobile" / "lib" / "main.dart").exists():
        return  # no app yet — "next: a mobile app" is then true

    unbuilt = re.compile(
        r"next[^.\n]{0,40}(a |the )?(flutter |)mobile app|"
        r"next[^.\n]{0,20}phase is mobile|"
        r"planned[^.\n]{0,30}mobile app",
        re.I,
    )
    for name in ORIENTING:
        for line in _text(name).splitlines():
            # ⭐ A line that marks it done may quote the old claim to explain the drift.
            if "✅" in line or "*This" in line or "said" in line:
                continue
            assert not unbuilt.search(line), f"{name} still calls the mobile app unbuilt:\n  {line[:150]}"


def test_the_live_fields_are_not_a_season_behind() -> None:
    """`Current Story` and `Next Milestone` are **live** fields, not a log.

    ⚠️ Each carried a claim from August into late September. ⭐ *A field named "current" is the one nobody
    re-reads, because its name promises it was.*
    """
    status = _text("docs/00_Project/PROJECT_STATUS.md").splitlines()
    actual = len(list((ROOT / "docs" / "06_Decisions").glob("ADR-*.md")))

    for field in ("Current Story:", "Next Milestone:"):
        line = next(x for x in status if x.startswith(field))
        for claim in re.findall(r"\*\*(\d{2,4}) ADRs\.?\*\*", line):
            assert abs(int(claim) - actual) <= 10, (
                f"{field} claims {claim} ADRs; the repo has {actual}"
            )


def test_a_dated_claim_that_has_expired_is_not_still_pending() -> None:
    """⭐ *A date is the only part of a plan that expires on its own* (ADR-212).

    A line that says something happens "on or after" a date in the past, and still reads as waiting, is a
    line nobody has revisited. ⚠️ Historical records are exempt — they are meant to be in the past.
    """
    today = datetime.date.today()
    for name in ORIENTING:
        for line in _text(name).splitlines():
            for m in re.finditer(r"on or after \*{0,2}(20\d\d-\d\d-\d\d)", line):
                when = datetime.date.fromisoformat(m[1])
                if when <= today:
                    assert "✅" in line or "~~" in line, (
                        f"{name}: '{m[1]}' has passed and the line still reads as pending:\n"
                        f"  {line[:160]}"
                    )


def test_the_held_ml_gate_keeps_its_date_and_its_rule() -> None:
    """📅 The Phase 1 gate (ADR-204) is re-decided after GW8, against a rule fixed **before** the data.

    ⚠️⚠️ *The whole value of a pre-registered threshold is that it was set without knowing which side the
    answer falls on*, so this pins that the date and the criteria are still stated — ⭐ a held decision
    whose terms quietly drift is a decision that was never held.
    """
    adr = next((ROOT / "docs" / "06_Decisions").glob("ADR-204-*.md")).read_text()

    assert "2026-10-26" in adr or "GW8" in adr
    assert "pre-registered" in adr
    assert "declined for the season" in adr, "the decline branch is gone — a gate with one exit is a plan"
    # ⭐ And it must still be reachable: the harness that produces the numbers has to exist.
    spike = ROOT / "spikes" / "204-board-wide-minutes"
    for script in ("blend.py", "blend_on_points.py", "hit_rate_error.py"):
        assert (spike / script).exists(), f"{script} is gone; the GW8 review cannot be run"


def test_the_orientation_docs_are_tracked() -> None:
    """⚠️ `site/index.html` lived outside the repo and a broken link sat on it unnoticed (ADR-289)."""
    tracked = set(
        subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    )
    for name in ORIENTING:
        assert name in tracked, f"{name} is not tracked"
