"""Resolving a player name in free text — the part that has to be right (ADR-152).

Counting how often a player is mentioned looks trivial and is not. Measured on the live squad list and a real
112-headline corpus, naive `web_name` matching is wrong three different ways:

* **Shared surnames.** 14 `web_name`s belong to more than one player — `Palmer` ×2, `Wilson` ×3,
  `Phillips` ×3. A bare "Palmer" credited *both* Cole Palmer (14.2% owned) **and** Alex Palmer, a backup
  goalkeeper, with the same mention.
* **A name inside another name.** **90** `web_name`s appear inside a *different* player's full name:
  `James` inside "James Maddison" and "James Trafford"; `Keane` **and** `Lewis` both inside "Keane
  Lewis-Potter"; `Hall` inside "Kiernan Dewsbury-Hall". The single headline *"James Maddison out for up to
  two weeks"* credited Reece James with a mention.
* **Names too short to be safe**, which the ≥4-character floor already guarded against.

The fix is **longest-match-first with span consumption**: full names are matched before bare surnames, and a
matched span is removed from play so a shorter pattern cannot match inside it. "Cole Palmer" claims those
eleven characters, so the "Palmer" pattern never sees them.

**Ambiguity resolves to silence, not to a guess** — the same discipline as ADR-146's exodus note. Where a bare
surname could be several players, it is credited only when one is a *clear* favourite; otherwise it is
dropped. Measured across the 14 collisions: 9 have a clear favourite, and in the other 5 nobody owns any of
the candidates, so nothing of value is lost.
"""

import re

MIN_NAME = 4          # shorter names collide with ordinary words; the buzz counter has always used this
CLEAR_OWNERSHIP = 1.0     # a favourite must be owned by at least this % …
CLEAR_RATIO = 3.0         # … and by this multiple of the next candidate. Both measured (ADR-152).


def _get(row, key, default=None):
    try:
        v = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if v is None else v


def _full_name(player) -> str:
    first, second = _get(player, "first_name", ""), _get(player, "second_name", "")
    return f"{first} {second}".strip()


def _favourite(candidates):
    """The one player a bare surname most likely means, or `None` when it is genuinely ambiguous.

    Ownership is the proxy: in r/FantasyPL "Palmer" means the midfielder 14.2% of managers own, not the
    goalkeeper. But it is only used when the favourite is **clear** — otherwise a mention is dropped, because
    crediting the wrong player is worse than counting nothing.
    """
    ranked = sorted(candidates, key=lambda p: -(float(_get(p, "selected_by", 0.0) or 0.0)))
    top = float(_get(ranked[0], "selected_by", 0.0) or 0.0)
    nxt = float(_get(ranked[1], "selected_by", 0.0) or 0.0) if len(ranked) > 1 else 0.0
    if top < CLEAR_OWNERSHIP:
        return None                                   # nobody owns any of them — the mention is not worth a guess
    if nxt > 0 and top / nxt < CLEAR_RATIO:
        return None
    return ranked[0]


def build_index(players) -> list:
    """`[(pattern, player, exact)]`, **longest first** — the order is the whole mechanism.

    `exact` marks a full-name pattern: unambiguous by construction. Bare `web_name` patterns carry the
    player only when one is a clear favourite; a hopelessly shared surname is left out entirely.
    """
    by_web = {}
    for p in players:
        web = str(_get(p, "web_name", "") or "")
        if len(web) >= MIN_NAME:
            by_web.setdefault(web.lower(), []).append(p)

    index = []
    for p in players:
        full = _full_name(p)
        if len(full) >= MIN_NAME and " " in full:
            index.append((full.lower(), p, True))
    for web, group in by_web.items():
        owner = group[0] if len(group) == 1 else _favourite(group)
        if owner is not None:
            index.append((web, owner, False))
    return sorted(index, key=lambda t: -len(t[0]))


def find_mentions(text: str, index) -> dict:
    """`{player_id: hits}` for one piece of text, matching longest-first and consuming what it matches.

    Consumption is what stops "James Maddison" also counting as a mention of Reece James: the longer pattern
    runs first and blanks those characters, so the shorter one never sees them.
    """
    if not text:
        return {}
    low = text.lower()
    taken = bytearray(len(low))          # 1 where a longer pattern has already claimed a character
    hits = {}
    for pattern, player, _exact in index:
        for m in re.finditer(rf"\b{re.escape(pattern)}\b", low):
            a, b = m.span()
            if any(taken[a:b]):
                continue                 # inside a name we have already credited
            taken[a:b] = b"\x01" * (b - a)
            pid = _get(player, "id")
            hits[pid] = hits.get(pid, 0) + 1
    return hits
