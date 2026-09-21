"""Every transfer search in `src/` must say which window it is ranking (ADR-209, enforced by ADR-220).

⚠️⚠️ **ADR-209 fixed the engine and reached only some of its callers.** `window` sizes the tie-break band
and defaults to five gameweeks; `horizon_xp` lets the longer view break a near-tie. Both are optional, so a
caller that omits them gets **no error and no warning** — the ranking returns and simply names a different
player. The Streamlit Transfer tab ran that way for a fortnight, at **horizon 1**, where the band is more
than twice the width it should be.

⭐⭐ **So the guard sweeps for the claim rather than checking the places I thought of** (ADR-184). Two
earlier guards in this project both checked the same two files and a retired claim survived on six surfaces
for fourteen days. A sweep finds the *next* call site too.

⚠️ **This is a source scan, and ADR-178 is right that a source scan asserts code was WRITTEN, not that it
RUNS.** That limit is accepted here because the claim being made *is* about the source: "no call site omits
this argument" is not a runtime property of any single execution. The behavioural half lives in
`tests/test_tiebreak_horizon.py` and `tests/test_service_endpoints.py`.
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
CALL = re.compile(r"\b(suggest_transfers|suggest_transfer_plan)\s*\(", re.M)

# ⭐ `transfer.py` is where they are defined and where the plan calls the single-swap search with the window
# it was itself given — the one place the argument is threaded rather than chosen.
DEFINING_MODULE = "transfer.py"


def _uncommented(text: str) -> str:
    """The file with `#` comments blanked out, line by line.

    ⚠️ **Needed, not fastidious.** `gameweek.py` explains a past decision with the words
    *"this used to call `suggest_transfers(limit=2)`"* — and the first version of this sweep reported that
    sentence as an unfixed call site. ⭐ *The paragraphs that warn about a pattern contain the pattern*
    (ADR-178), so a guard that greps must read code and not prose.
    """
    out = []
    for line in text.split("\n"):
        quote = None
        for i, ch in enumerate(line):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif ch == "#":
                line = line[:i] + " " * (len(line) - i)
                break
        out.append(line)
    return "\n".join(out)


def _balanced(text: str, start: int, *, stop_at_newline: bool = True) -> str:
    """From `start` to the point where every bracket opened has closed — one whole statement or call."""
    depth, i = 0, start
    while i < len(text):
        depth += text[i] in "([{"
        depth -= text[i] in ")]}"
        if depth <= 0 and (text[i] == "\n" if stop_at_newline else text[i] in ")]}"):
            return text[start:i + (0 if stop_at_newline else 1)]
        i += 1
    return text[start:]


def _resolve(text: str, args: str) -> str:
    """The call's arguments, with any `**name` splat replaced by where `name` was defined.

    ⭐ **Per call, and splats followed — the guard needs both.** Reading only the parentheses misses the
    service, the Transfer tab and `ask`, which each build `{"window": …, "horizon_xp": …}` once and pass it
    to two or three searches; that is good code. But widening the check to *the enclosing function* was too
    far: with three calls sharing one dict, deleting the splat from **one** of them left the dict still in
    scope and the guard still green. ⚠️ *I only found that by breaking the guard after improving it* — it
    had reported three clean call sites that were not.

    ⚠️ `name` is resolved anywhere in the file, because `ask` keeps its dict as a module constant while the
    others keep theirs local. A guard that follows only the indirection you happened to write is a guard
    against yourself.
    """
    for name in set(re.findall(r"\*\*(\w+)", args)):
        # ⚠️ `[ \t]*`, not `\s*` — `\s` matches newlines, so the match would start on the blank line above
        # and `_balanced` would stop at the first line end having read nothing.
        where = re.search(rf"^[ \t]*{re.escape(name)}\s*=", text, re.M)
        if where:
            args += "\n" + _balanced(text, where.start())
    return args


def _call_sites():
    """(path, line number, the call's own arguments, splats resolved) for every call in `src/`."""
    out = []
    for path in sorted(SRC.rglob("*.py")):
        text = _uncommented(path.read_text())
        for match in CALL.finditer(text):
            if text[:match.start()].rstrip().endswith("def"):
                continue
            args = _balanced(text, match.end(), stop_at_newline=False)
            out.append((path.relative_to(SRC.parent), text[:match.start()].count("\n") + 1,
                        _resolve(text, args)))
    return out


def _ids(value):
    """`path:line` rather than a whole function body — ⭐ a failure has to name its call site to be
    actionable, and pytest builds the id from the parameters it is given."""
    return str(value) if not (isinstance(value, str) and len(value) > 40) else "args"


def test_there_are_call_sites_to_check():
    """⭐ A sweep that finds nothing passes. ADR-178: *a test that skips is not a test that passes*, and a
    regex that silently stops matching is the same failure wearing a different hat."""
    assert len(_call_sites()) >= 6


@pytest.mark.parametrize("path, line, args", _call_sites(), ids=_ids)
def test_every_transfer_search_states_the_window_it_ranks(path, line, args):
    """⚠️ The default is five gameweeks. A caller ranking a one-gameweek map without saying so gets a band
    sized for a window it is not using — ADR-209 measured that as **silently deciding every one-gameweek
    recommendation**, because the median gap between best and second best was 0.20 against a band of 2.0."""
    if path.name == DEFINING_MODULE:
        pytest.skip("the definitions and the plan's internal call, which threads the window it was given")
    assert "window=" in args or '"window"' in args, (
        f"{path}:{line} ranks transfers without saying which window its xP map covers. Pass "
        f"`window=<horizon>` — omitting it silently applies a five-gameweek tie-break band."
    )


@pytest.mark.parametrize("path, line, args", _call_sites(), ids=_ids)
def test_every_transfer_search_offers_the_longer_view(path, line, args):
    """⭐⭐ The half that moves expected points. Two moves worth +1.2 apiece over one gameweek are a dead
    heat on the number being ranked; the owner's week had one worth −1.5 over five and the other +3.1, and
    the app **computed that number, printed it, and never let it choose** (ADR-191).

    ⚠️ `_horizon_gain` returns 0.0 when no wider map is supplied, so omitting `horizon_xp` does not fail —
    it makes the first tie-break key a constant and hands the decision to the next one.
    """
    if path.name == DEFINING_MODULE:
        pytest.skip("the definitions and the plan's internal call, which threads what it was given")
    assert "horizon_xp=" in args or '"horizon_xp"' in args, (
        f"{path}:{line} never offers the longer view a say. Pass `horizon_xp=<wider map>` (or an explicit "
        f"`horizon_xp=None` when the ranking window already IS the wider one)."
    )


def test_the_exemption_stays_exactly_as_big_as_it_is():
    """⚠️ **Two call sites are skipped above, and a skip is invisible in a green run** (ADR-178). If a third
    appeared in `transfer.py` — or if someone moved a caller there to quiet the guard — nothing would say
    so. ⭐ *An exemption that can grow silently is not an exemption, it is a hole.*
    """
    exempt = [(p, line) for p, line, _ in _call_sites() if p.name == DEFINING_MODULE]
    assert len(exempt) == 1, (
        f"{len(exempt)} call sites are exempt, not 1: {exempt}. The exemption covers `suggest_transfer_plan` "
        f"calling `suggest_transfers` with the window it was itself given — nothing else."
    )
