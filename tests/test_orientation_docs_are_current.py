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

import pytest

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
    # ⭐ A line that marks it done may quote the old claim to explain the drift, so those are exempt —
    # ⚠️⚠️ **but per CLAUSE, not per line, which is how this guard was defeated for a week.** The exemption
    # was `if "✅" in line`, and `PROJECT_STATUS`'s **Current Phase** field is a 742-character paragraph
    # carrying ✅ against *the pipeline* and *Supabase* — so the whole line was skipped, including the
    # `**Next:** the Flutter mobile app` at the end of it (found 2026-09-28, ADR-322).
    #
    # ⭐⭐ *An escape hatch scoped more widely than the claim it excuses exempts the thing it was written to
    # catch* — and it fails silently, because a guard that skips looks exactly like a guard that passed.
    exempt = ("✅", "~~", "*This", "said", "read ")
    for name in ORIENTING:
        for line in _text(name).splitlines():
            for match in unbuilt.finditer(line):
                # The clause around the match: the regex never spans a `.`, so the nearest full stops on
                # either side bound it the same way.
                start = line.rfind(".", 0, match.start()) + 1
                end = line.find(".", match.end())
                clause = line[start:end if end != -1 else len(line)]
                assert any(mark in clause for mark in exempt), (
                    f"{name} still calls the mobile app unbuilt:\n  …{clause.strip()[:160]}"
                )


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


# ---- a retired log stays retired (2026-09-28) -----------------------------------------------------

RETIRED_LOG = ROOT / "docs" / "00_Project" / "Feedback_Log.md"


def test_the_feedback_log_still_says_it_is_retired() -> None:
    """⭐⭐ **A log nobody writes to any more reads as "nothing was reported".**

    `Feedback_Log.md` stopped being written to after **2026-08-28** while feedback kept arriving — a whole
    month of September reports went into ADRs and never appeared here, so an audit of open work would have
    concluded testers had gone quiet in August. ⚠️ *Silence in a record is indistinguishable from silence
    in the world*, which is the failure a retirement notice exists to prevent.

    It was retired rather than backfilled because the ADR index already carries the quote, the
    measurement, the decision and the tests — ⭐ *two places recording the same thing is how one of them
    becomes wrong.*
    """
    head = RETIRED_LOG.read_text()[:2000]
    assert "RETIRED" in head, (
        "the feedback log no longer announces that it is retired — a reader will take its August silence "
        "as the last word on tester feedback"
    )
    assert "ADR-000-index" in head, "the retirement notice does not say where feedback is recorded instead"


def test_nobody_has_started_writing_to_it_again() -> None:
    """⚠️ Retiring a file is a decision that only holds while nothing appends to it. ⭐ *A row added under
    a RETIRED header is worse than the original problem*: it makes the file look alive again while still
    missing everything that went to the ADRs.

    Dates in the table are `| YYYY-MM-DD |`; none may fall on or after the retirement.
    """
    retired_on = datetime.date(2026, 9, 28)
    dates = [datetime.date.fromisoformat(d)
             for d in re.findall(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|", RETIRED_LOG.read_text(), re.M)]
    assert dates, "the historical rows are gone — retiring this file was meant to keep them"
    newest = max(dates)
    assert newest < retired_on, (
        f"a row dated {newest} was added to a log retired on {retired_on}. Feedback belongs in an ADR "
        f"(docs/06_Decisions/), not here."
    )


# ---- size, because the prose guards all passed while the file grew to 84.5 KB (ADR-326) ------------

#: What each orienting document may weigh, and what a single "current" field may. ⚠️⚠️ **Not a style rule.**
#: Every test above checks a claim against the repo, and every one of them passed while `PROJECT_STATUS.md`
#: reached **84,531 bytes** — 86% of it a 69-entry sprint log inside one line — because ⭐⭐⭐ *no individual
#: sentence in it was false. The failure was a document too long to re-read, which is a property of the whole
#: and invisible to any test of the parts.*
#:
#: ⭐ The numbers are ceilings with room, not targets: roughly 3x what the files hold today, so ordinary
#: editing never trips them and a log quietly accumulating does.
CEILINGS = {
    "docs/00_Project/PROJECT_STATUS.md": 20_000,
    "docs/06_Decisions/ADR-000-index.md": 250_000,
    "CLAUDE.md": 12_000,
    # ⚠️ A tighter multiple than the others, on purpose: a forward plan legitimately grows as work is
    # agreed, so it needs room — but **46% of it was delivered work** when ADR-326 looked, 56 items sitting in
    # sections meant to say what is next. ⭐ *History accumulating in a plan looks exactly like the plan
    # growing*, which is why this one is watched at all.
    "docs/04_Roadmap/Roadmap.md": 85_000,
}
FIELD_CEILING = 900


@pytest.mark.parametrize("name", sorted(CEILINGS))
def test_an_orienting_document_stays_readable(name) -> None:
    """⚠️ If this fails, the fix is to **move** content, not to raise the number. The index's reasoning belongs
    in the ADR; a status file's history belongs in `Status_Log_Archive.md` or a sprint doc."""
    size = (ROOT / name).stat().st_size
    assert size <= CEILINGS[name], (
        f"{name} is {size:,} bytes, over its {CEILINGS[name]:,} ceiling. Something is accumulating in a file "
        f"that is read before anything else. Move it out (ADR-326) rather than raising this."
    )


def test_no_current_field_has_become_an_essay() -> None:
    """⭐ The fields named *current* are the ones a reader scans first and the ones that rot fastest — ADR-294's
    stale clause sat at the end of a 742-character paragraph, unread.

    ⚠️ `Tests:` is exempt and deliberately so: it is a facts line, not a narrative, and it names the CI jobs.
    """
    status = (ROOT / "docs/00_Project/PROJECT_STATUS.md").read_text().splitlines()
    fields = ("Current Phase:", "Current Sprint:", "Current Story:", "Next Milestone:", "Current Version:")
    for line in status:
        if line.startswith(fields):
            assert len(line) <= FIELD_CEILING, (
                f"'{line.split(':')[0]}' is {len(line)} characters, over {FIELD_CEILING}. Put the reasoning in "
                f"the ADR it cites — a status line that restates its ADR is the copy that goes stale."
            )

