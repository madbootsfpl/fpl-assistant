"""The update banner can say what changed (ADR-296).

⭐⭐ **The `notes` field shipped empty in ADR-282 and stayed empty**, because nothing produced it. ⚠️ *A
release note nobody is prompted for is a release note nobody writes* — the same argument that moved the
publish step into the script (ADR-290). So they come from the commits, and a human can override them
when a release deserves words chosen on purpose.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_android.sh"


def _generator() -> str:
    body = re.search(
        r"python3 - \"\$name\" \"\$next\" \"\$code\" \"\$SITE/app/version\.json\" <<'PY'\n(.*?)\nPY",
        SCRIPT.read_text(),
        re.S,
    )
    assert body, "the release script no longer builds version.json in python"
    return body[1]


def manifest(env: dict | None = None) -> dict:
    out = Path(tempfile.mkdtemp()) / "version.json"
    subprocess.run(
        ["python3", "-c", _generator(), "1.0.0", "13", "2013", str(out)],
        cwd=ROOT, check=True, env={**__import__("os").environ, **(env or {})},
    )
    return json.loads(out.read_text())


def test_notes_are_a_list() -> None:
    """⚠️ It shipped as `""` and the app must keep reading that, but new manifests are structured —
    ⭐ *a client that has to split a string to lay it out will one day split it differently* (ADR-286)."""
    assert isinstance(manifest()["notes"], list)


def test_a_release_with_nothing_to_say_says_nothing() -> None:
    """⭐⭐ **Empty is a legal answer**, and the script must be able to give it.

    ⚠️⚠️ **This asserted `notes == []` and passed until the next `fix:` commit landed** — it had pinned
    *what HEAD happened to be*, not a behaviour, so it failed on a change that was entirely correct.
    ⭐ *A test that reads the repository's current state tests the day it was written.*

    ⚠️ *A script that insists on filling this field will produce "various fixes" forever, which is worse
    than silence because it looks like information* — so the empty case is exercised through the one
    input that can produce it deterministically.
    """
    # ⚠️ A blank override is **not** an override — it falls through to the commits, which is right and
    # which my first rewrite of this test also assumed away. ⭐ *The second wrong assumption about the
    # same function is the one that shows you were guessing rather than reading it.*
    assert manifest({"MADBOOTS_NOTES": "   \n\n  "})["notes"] == manifest()["notes"]

    # The empty case is reached through a release of only invisible work — now the ordinary case,
    # because a note is opt-in (ADR-328) rather than derived from a prefix.
    assert _notes_from([
        "chore: release build 30",
        "docs: update the readme",
        "test: cover the lab modes",
        "fix: something with no trailer on it",
    ]) == []

    # And whatever HEAD happens to be, every entry is real, trimmed text — never a blank bullet.
    for note in manifest()["notes"]:
        assert note and note.strip() == note


def test_a_human_can_override_them() -> None:
    notes = manifest({"MADBOOTS_NOTES": "Landscape pitch fixed\nFaster player search"})["notes"]

    assert notes == ["Landscape pitch fixed", "Faster player search"]


def test_an_override_is_capped_like_the_derived_ones() -> None:
    # ⚠️ The banner shows three. *A cap enforced in one of two places is a cap that moves.*
    assert len(manifest({"MADBOOTS_NOTES": "\n".join(f"line {i}" for i in range(9))})["notes"]) == 3


def _notes_from(commits: list[str], env: dict | None = None) -> list[str]:
    """Run the real generator over a throwaway repo — ⭐ *a test that reads the code instead of running
    it will believe whatever the code says about itself*, which is how the old subject filter kept
    passing while it shipped three notes nobody could act on."""
    import os

    repo = Path(tempfile.mkdtemp())

    def git(*a: str) -> None:
        subprocess.run(["git", "-C", str(repo), *a], capture_output=True, check=True)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    for message in commits:
        (repo / "f").write_text(message)
        git("add", "-A")
        git("commit", "-q", "-m", message)

    out = repo / "version.json"
    subprocess.run(
        ["python3", "-c", _generator(), "1.0.0", "13", "2013", str(out)],
        cwd=repo, check=True, env={**os.environ, **(env or {})},
    )
    return json.loads(out.read_text())["notes"]


def test_a_note_is_opt_in_and_written_for_the_reader() -> None:
    """⭐⭐ **The trailer is the note** (ADR-328). Its author decides that a tester can see the change,
    and writes the sentence they will read — rather than a rule guessing from a commit prefix."""
    notes = _notes_from([
        "chore: release build 30",
        "fix: a free transfer for a gameweek FPL does not pay one for\n\n"
        "Release-note: The transfer count now matches FPL",
    ])
    assert notes == ["The transfer count now matches FPL"]


def test_a_fix_nobody_can_see_reaches_nobody() -> None:
    """🔴 **The bug this replaced.** Build 31 told nine testers about *"scope the staleness exemption to
    the clause it excuses"* — a docs test — and *"pin the deploy requirements"* — a requirements file.

    ⚠️⚠️ Both carried `fix:`, which is why the old rule let them through: *the prefix says what kind of
    change it is, never who can see it.* ⭐ The old filter's own comment promised "only what a reader of
    the app would notice", and the regex under it could not keep that promise.
    """
    notes = _notes_from([
        "chore: release build 30",
        "fix: scope the staleness exemption to the clause it excuses",
        "fix: pin the deploy requirements, including the file Render actually installs",
        "feat: something internal with no trailer",
        "docs: tidy the index",
    ])
    assert notes == [], f"an invisible change reached the banner: {notes}"


def test_the_adr_number_does_not_reach_the_reader() -> None:
    """⚠️ `fix(ADR-293):` is how this project talks to itself. ⭐ *A tester reading "ADR-293" learns the
    note was not written for them*, and stops reading the next one. The trailer carries no prefix at all,
    so the number cannot leak through it."""
    notes = _notes_from([
        "chore: release build 30",
        "fix(ADR-293): in landscape the bench sits beside the pitch\n\n"
        "Release-note: The bench sits beside the pitch in landscape",
    ])
    assert notes == ["The bench sits beside the pitch in landscape"]
    assert not any("ADR" in n for n in notes)


def test_the_anchor_accepts_both_spellings_of_a_release_commit() -> None:
    """🔴 **The convention slipped and nothing noticed** (ADR-328). Build 31's release commit reads
    `release: 1.0.0+31`, not `chore: release`, so the next run would have anchored on build 30 and
    re-reported a week-old list. ⭐ *An anchor that matches one spelling of a convention is an anchor
    that moves the first time someone types it differently.*"""
    notes = _notes_from([
        "chore: release build 30",
        "fix: old\n\nRelease-note: From before the last release",
        "release: 1.0.0+31 — the transfer fixes reach the testers",
        "fix: new\n\nRelease-note: From after the last release",
    ])
    assert notes == ["From after the last release"], (
        "the range did not restart at the `release:`-spelled commit"
    )


def test_the_range_starts_at_the_last_release_not_a_guess() -> None:
    """⚠️ This project does not tag. ⭐ *A range that guesses would silently report the wrong week's
    work* — and silently is the problem, because the notes would still look plausible."""
    assert "--grep=^chore: release" in _generator()
