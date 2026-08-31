"""The ADR index must not silently fall behind (ADR-171, Sprint 231).

It had stopped at **ADR-122 while 171 ADRs existed** — 49 missing — and nothing said so, because a stale
document does not fail. It was found by accident, three sprints later, while filing an unrelated ADR.

This project has now paid the same lesson three times in one week: CI never exercised the narrated path
(ADR-168), two AppTests asserted against the wrong tab after a rename (ADR-171), and this. **The species is
coverage that leaves without anything going red** — so the index gets a test, exactly like the code does.
"""

import re
from pathlib import Path

import pytest

DECISIONS = Path(__file__).resolve().parents[1] / "docs" / "06_Decisions"
INDEX = DECISIONS / "ADR-000-index.md"

_ROW = re.compile(r"^\| \[(\d+)\]\((.+?)\) \| (.*) \| (.*) \|$", re.M)


def _rows():
    return [(int(n), link, title, status) for n, link, title, status in _ROW.findall(INDEX.read_text())]


def _adr_files():
    """{number: filename} for every ADR except the index itself."""
    out = {}
    for f in DECISIONS.glob("ADR-*.md"):
        m = re.match(r"ADR-(\d+)-(.+)\.md$", f.name)
        if m and int(m.group(1)) != 0:
            out[int(m.group(1))] = f.name
    return out


def test_every_adr_has_an_index_row():
    missing = sorted(set(_adr_files()) - {n for n, *_ in _rows()})
    assert not missing, (
        f"{len(missing)} ADR(s) are not in the index: {missing}. Add a row to "
        f"docs/06_Decisions/ADR-000-index.md — an index that stops being maintained stops being an index."
    )


def test_the_index_has_no_rows_for_adrs_that_do_not_exist():
    files = _adr_files()
    orphans = sorted(n for n, *_ in _rows() if n not in files)
    assert not orphans, f"index rows with no matching file: {orphans}"


@pytest.mark.parametrize("field", ["link", "title", "status"])
def test_every_row_is_complete(field):
    bad = [n for n, link, title, status in _rows()
           if not {"link": link, "title": title, "status": status}[field].strip()]
    assert not bad, f"rows with an empty {field}: {bad}"


def test_every_link_resolves():
    dead = [(n, link) for n, link, _, _ in _rows() if not (DECISIONS / link.removeprefix("./")).exists()]
    assert not dead, f"dead links in the index: {dead}"


def test_the_index_is_ordered_and_unique():
    """Ascending, because it drifted into `…069 068 067 089 122…070 066` by being appended to at random."""
    nums = [n for n, *_ in _rows()]
    assert nums == sorted(nums), "the index must stay in ascending ADR order"
    assert len(nums) == len(set(nums)), "an ADR is listed twice"
