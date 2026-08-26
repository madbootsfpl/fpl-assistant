"""Spike 206 — can we read EVENTS out of the headlines the app already fetches?

The question, from the owner: could ML/sentiment turn Signals into a score? Measurement said no — 112
headlines, ~6KB, titles only, no labels. But the text turned out to be **reported fact with named
journalists**, not opinion:

    [Romano] Hilal have now agreed all details of deal to sign Ollie Watkins, here we go!

That is the exact story behind ADR-146's unexplained Watkins exodus, sitting in a feed we already fetch and
were reducing to a mention count. So the job is **extraction**, not sentiment.

This spike measures a **rule-based baseline first** — because if rules are good enough, an LLM is
unjustifiable complexity in a project that prefers simple solutions (and declined a heavier data dep in
ADR-016). Only if rules fail badly is a model worth discussing.
"""

import json
import pathlib
import re

CORPUS = pathlib.Path(__file__).parent / "corpus.json"

# Cue phrases that mark a transfer/availability EVENT, grouped by what they mean. Deliberately narrow: a
# false positive here would attach a wrong cause to a player, which is worse than staying silent (ADR-146's
# rule — the note must never invent a reason).
_TRANSFER = ("here we go", "agreed", "agree", "signs", "sign ", "joins", "join ", "medical",
             "deal to sign", "on loan", "loan move", "bid accepted", "completed a move", "transfer to")
_INJURY = ("injury", "injured", "out for", "ruled out", "sidelined", "hamstring", "acl", "surgery",
           "knock", "doubt")
_RETURN = ("returns", "back in training", "fit again", "available again")
_SOURCES = ("romano", "ornstein", "sky sports", "the athletic", "bbc", "guardian", "telegraph")


def _players(store_players):
    """Longest names first, so 'Cole Palmer' wins over 'Palmer' where both exist."""
    rows = [(str(p["web_name"] or ""), p) for p in store_players]
    rows = [(n, p) for n, p in rows if len(n) >= 4]
    return sorted(rows, key=lambda t: -len(t[0]))


def extract(title: str, players) -> dict | None:
    """A structured event from one headline, or None. Precision over recall, on purpose."""
    low = title.lower()
    kind = ("transfer" if any(c in low for c in _TRANSFER) else
            "injury" if any(c in low for c in _INJURY) else
            "return" if any(c in low for c in _RETURN) else None)
    if kind is None:
        return None
    for name, row in players:
        if re.search(rf"\b{re.escape(name.lower())}\b", low):
            return {"player": name, "id": row["id"], "team": row["team"], "kind": kind,
                    "sourced": any(s in low for s in _SOURCES), "title": title}
    return None


if __name__ == "__main__":
    from src.storage import Storage

    store = Storage()
    players = _players(store.get_players())
    store.close()

    corpus = json.loads(CORPUS.read_text())
    hits = [e for t in corpus if (e := extract(t["title"], players))]

    print(f"{len(corpus)} headlines → {len(hits)} events extracted ({len(hits)/len(corpus):.0%})\n")
    for e in hits:
        flag = "📰" if e["sourced"] else "  "
        print(f'  {flag} {e["kind"]:<9} {e["player"]:<14} {e["team"]:<4}  {e["title"][:76]}')
