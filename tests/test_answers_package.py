"""The answers package keeps the properties its split depends on (ADR-324).

`src/service/answers.py` was one 2,368-line module; it is now a package of families. ⭐ The split is only
safe while two things hold, and both were broken at least once while making it — which is why they are
tests rather than notes.
"""

import pathlib
import types

import pytest

import src.service.answers as answers

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "service" / "answers"
FAMILIES = ("common", "squad", "mini_leagues", "profiles", "market", "language", "meta")


@pytest.mark.parametrize("family", FAMILIES)
def test_no_handler_shadows_its_own_module(family):
    """🔴 **The trap this package walked into.** `__init__` re-exports the handlers, so a submodule named
    after one of them loses: `from src.service.answers.player import player` rebinds `answers.player` from
    the *module* to the *function*, and `answers.player.team_dna_all` then raises AttributeError — which is
    how a monkeypatch target stops existing.

    ⭐⭐ *A name that resolves to two different objects depending on import order is a trap, not a
    convenience.* It cost two renames (`league` → `mini_leagues`, `player` → `profiles`) and is asserted so
    the next family added cannot quietly reintroduce it.
    """
    assert isinstance(getattr(answers, family, None), types.ModuleType), (
        f"`answers.{family}` is not the module — a re-exported function of the same name has shadowed it. "
        f"Rename the module (as `league`→`mini_leagues` and `player`→`profiles` were) so no handler "
        f"collides with it."
    )


def test_every_family_is_listed_here():
    """⚠️ A new module in the package must join `FAMILIES`, or the shadowing check silently skips it —
    ⭐ *a parametrised guard is only as wide as its list, and the list is the part that goes stale.*"""
    on_disk = {p.stem for p in PKG.glob("*.py")} - {"__init__"}
    assert on_disk == set(FAMILIES), (
        f"the package holds {sorted(on_disk)} but this test checks {sorted(FAMILIES)} — add the new family "
        "to FAMILIES above"
    )


def test_the_contract_layer_still_reaches_every_handler():
    """⭐ `src/service/__init__.py` is what `app.py` and Streamlit import (ADR-219). The split is meant to be
    invisible there, so every name it publishes must still resolve."""
    import src.service as service

    missing = [n for n in service.__all__ if not hasattr(service, n)]
    assert not missing, f"the contract layer publishes names it cannot resolve: {missing}"


def test_the_shared_helpers_are_reached_through_the_module():
    """⚠️⚠️ **Why `common` is imported as a module and not as names.** `_chip_status` is faked in three test
    suites and `_entry_history` in one; both are used by more than one family. Binding them into each
    family's globals would give them one patch point per importer — ⭐ *and a fake that reaches one caller
    but not the next is worse than no fake, because the test still passes for the wrong reason.*

    So the families call `common.x(...)`. Asserted by source, because the alternative is invisible: the code
    works either way until someone patches it.
    """
    for family in ("squad", "mini_leagues", "language", "market"):
        src = (PKG / f"{family}.py").read_text()
        if "common." not in src:
            continue
        assert "from src.service.answers import common" in src, (
            f"{family}.py calls common.* without importing the module"
        )
        for name in ("_chip_status", "_entry_history", "plain"):
            bad = "from src.service.answers.common import"
            assert not (bad in src and name in src.split(bad)[1].split("\n")[0]), (
                f"{family}.py imports `{name}` by name from common. Import the module instead — a shared "
                f"helper bound into this module's globals cannot be faked for every consumer at once."
            )
