"""Helpers more than one family of answers needs.

⭐ Here **because they are shared, not because they are small** (ADR-324). `plain` is read by the market
and language answers; `_chip_status` and `_entry_history` fetch from FPL for the squad, league and language
families alike. ⚠️ *A helper used by two modules that lives in one of them makes that one the other's
dependency for no reason.*
"""


from src.fpl_rules import (
    CHIP_NAMES,
    chips_available,
)


def plain(text: str) -> str:
    """Markdown emphasis removed — ⭐ **the API speaks text, not Streamlit** (ADR-274).

    ⚠️⚠️ The engine's notes were written for a page that renders markdown, and the phone printed them
    literally: *"`**12 players**` stand out on two or more of these boards"*, asterisks and all, at the
    top of the screen the owner had asked to be made prominent.

    ⭐ *A string formatted for one renderer is a string formatted for one renderer* — and the transport is
    where that gets undone, exactly as the *"boards below"* wording was (ADR-271), because the Streamlit
    page it was written for still renders it correctly.
    """
    # ⚠️ Bold before italic: `**x**` would otherwise be read as an italic `*` wrapping `*x*`.
    #
    # ⭐ `__bold__` too, because the docstring above promises *markdown emphasis* and underscores are
    # markdown emphasis — found by a test that fed some through rather than looking for some.
    #
    # 🔴 **A single `_` is deliberately left alone, and completing the symmetry here would be a bug.**
    # FPL's own stat identifiers reach the screen as text — `defensive_contribution`, `goals_scored`,
    # `clean_sheets` — and the played-week card prints them (ADR-299). Stripping single underscores would
    # render that line as *"defensivecontribution"*. ⚠️ *The rule is not "remove punctuation", it is
    # "remove emphasis", and a lone underscore between two letters is neither.*
    return text.replace("**", "").replace("*", "").replace("__", "")


def _entry_history(manager_id) -> dict:
    """A manager's season history, or `{}` — ⚠️ **never load-bearing** (ADR-234's rule, reused).

    ⭐ One fetch behind three answers now: which chips are gone, how many free transfers are held, and how
    far the overall rank moved. *A call worth making once is worth making once.*
    """
    if not manager_id:
        return {}
    try:
        from src.api.client import FplClient

        return FplClient().get_entry_history(manager_id) or {}
    except Exception:                                # noqa: BLE001 — every caller degrades
        return {}


def _chip_status(manager_id, gameweek) -> dict:
    """Which chips are still in hand for this half-season (ADR-234).

    ⚠️ **`available: None` means *we do not know*.** No manager id, or a failed fetch, must not read as
    *"you still have it"* — ⭐ *"we could not check" and "you have it" are different facts, and only one of
    them is safe to act on.*
    """
    unknown = {name: {"available": None, "played_in": None} for name in CHIP_NAMES}
    if not manager_id or gameweek is None:
        return unknown
    try:
        from src.api.client import FplClient

        history = FplClient().get_entry_history(manager_id)
        return chips_available(history.get("chips"), gameweek)
    except Exception:                                    # noqa: BLE001 — advice survives a failed lookup
        return unknown
