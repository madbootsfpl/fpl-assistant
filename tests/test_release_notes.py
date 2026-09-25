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

    # The empty case is reached through the filter — a release of only invisible work.
    keep = _subject_filter()
    assert not any(keep.match(s) for s in [
        "docs: update the readme",
        "chore: release 1.0.0+13",
        "test: cover the lab modes",
    ])

    # And whatever HEAD happens to be, every entry is real, trimmed text — never a blank bullet.
    for note in manifest()["notes"]:
        assert note and note.strip() == note


def test_a_human_can_override_them() -> None:
    notes = manifest({"MADBOOTS_NOTES": "Landscape pitch fixed\nFaster player search"})["notes"]

    assert notes == ["Landscape pitch fixed", "Faster player search"]


def test_an_override_is_capped_like_the_derived_ones() -> None:
    # ⚠️ The banner shows three. *A cap enforced in one of two places is a cap that moves.*
    assert len(manifest({"MADBOOTS_NOTES": "\n".join(f"line {i}" for i in range(9))})["notes"]) == 3


def _subject_filter() -> re.Pattern:
    """The regex the generator sifts commit subjects with — ⚠️ pulled out and **exercised**, because a
    substring check on the script matched `--grep=^chore: release`, which finds the range rather than
    letting chore commits through. ⭐ *A test that reads the code instead of running it will believe
    whatever the code says about itself.*"""
    pattern = re.search(r'm = re\.match\(\s*r"([^"]+)"', _generator())
    assert pattern, "the subject filter is no longer a literal regex"
    return re.compile(pattern[1].replace("\\\\", "\\"))


def test_only_changes_a_reader_could_notice() -> None:
    """⭐ `docs:`, `test:` and `chore:` changed nothing they can see.

    ⚠️ *A note about work nobody can observe teaches people to skip the notes.*
    """
    keep = _subject_filter()

    for subject in [
        "feat(ADR-293): in landscape the bench sits beside the pitch",
        "fix(ADR-291): a plan that contradicted itself",
        "feat: something without an ADR",
    ]:
        assert keep.match(subject), f"a user-visible change was dropped: {subject}"

    for subject in [
        "docs(ADR-295): the orientation docs were a phase behind",
        "chore: release 1.0.0+12",
        "test(ADR-294): the Lab's modes were built",
        "refactor: tidy the pitch",
    ]:
        assert not keep.match(subject), f"an invisible change reached the banner: {subject}"


def test_the_adr_number_does_not_reach_the_reader() -> None:
    """⚠️ `feat(ADR-293):` is how this project talks to itself. ⭐ *A tester reading "ADR-293" learns
    that the note was not written for them*, and stops reading the next one."""
    keep = _subject_filter()
    m = keep.match("feat(ADR-293): in landscape the bench sits beside the pitch")

    text = m.group(2) or m.group(4)
    assert text == "in landscape the bench sits beside the pitch"
    assert "ADR" not in text


def test_the_range_starts_at_the_last_release_not_a_guess() -> None:
    """⚠️ This project does not tag. ⭐ *A range that guesses would silently report the wrong week's
    work* — and silently is the problem, because the notes would still look plausible."""
    assert "--grep=^chore: release" in _generator()
