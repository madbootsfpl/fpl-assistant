"""What the app's terms mean — **one source, read by every surface** (ADR-249).

⭐⭐ **Written because the phone had no tooltips and the web's help text had nowhere to come from.** The
web carries `help="…"` strings inline at ~40 call sites; there was no dictionary to point a second client
at, so a phone tooltip would have meant **retyping every explanation in Dart**. ⚠️ *That is exactly the
drift that put BOOTS in white* — a rule retyped instead of derived.

⭐ Definitions, not instructions. Each entry says what a number **is** and, where it matters, what it is
**not** — because the honest half of an explanation is usually the limit. ⚠️ Nothing here may promise
accuracy: *confidence is a heuristic and a percentile is a rank*, and a glossary that blurred either would
undo the care taken everywhere else.

📌 The web's inline strings should migrate onto this module. Until they do, this is the single source for
**the app** and the second source for the web — recorded so the next reader knows which way the debt runs.
"""

#: term key → (short label, the explanation)
TERMS: dict[str, tuple[str, str]] = {
    "xp": (
        "Expected points (xP)",
        "What we project a player to score, over the window shown. It is a **projection from minutes, "
        "fixtures and underlying numbers** — not a prediction of what will happen, and not FPL's own "
        "figure.",
    ),
    "confidence": (
        "Confidence",
        "How **clear** this week's plan is, 1–99. It is driven by your captain and reduced by flagged "
        "players in your XI.\n\nIt is a documented heuristic, **not a probability**. Raising it does not "
        "make you more likely to be right — it means the week is less ambiguous.",
    ),
    "ceiling": (
        "Ceiling",
        "The highest this week's confidence could reach, which is your **captain's own number**. Lifting "
        "it means choosing a different captain, not a different week.",
    ),
    "edge": (
        "Edge",
        "What is going **for** you this week — a clear captain, an upgrade worth taking, points sitting "
        "on your bench.",
    ),
    "risk": (
        "Risk",
        "What could go wrong — doubtful players, and sell-offs the data cannot explain. Each says what "
        "**kind** of claim it is, because an injury FPL confirmed and a crowd movement are not the same "
        "evidence.",
    ),
    "lineup": (
        "Lineup",
        "Changes to **who starts**, from the fifteen you already own. Free and reversible — no transfer "
        "is spent and nothing is bought, so this is the cheapest gain on the screen and the first one "
        "worth taking.",
    ),
    "transfer": (
        "Transfer",
        "A move that **costs** something — a free transfer, or four points. The gain shown is what the "
        "move is worth over the window, so a small gain over one gameweek and the same gain over five "
        "are very different propositions.",
    ),
    "timing": (
        "Timing",
        "Whether to act **now or wait**. Prices move, news lands, and a player's chance of starting "
        "firms up as the deadline nears — so a move worth making is not always a move worth making yet.",
    ),
    "percentile": (
        "Percentile",
        "A **rank**, not a score: 74 means better than 74% of the others being compared. It lets things "
        "measured in different units sit on one scale.\n\n⚠️ A high percentile in a weak field is still a "
        "high percentile.",
    ),
    "free_transfers": (
        "Free transfers",
        "How many moves you can make without a points hit. **FPL does not publish this**, so the app has "
        "to ask you for it — and the week's plan recommends this many moves.",
    ),
    "exodus": (
        "Unexplained sell-off",
        "Far more managers sold this player this week than his status or news explains.\n\nIt reports "
        "that **the crowd knows something we do not**. It does not say what.",
    ),
    "price_direction": (
        "Price direction",
        "Which way his price is heading, from net transfers measured against the whole board.\n\n⚠️ It "
        "does **not** say *when*. A change tonight and a change next week look the same here.",
    ),
    "defcon": (
        "Defensive contributions",
        "Tackles, interceptions, clearances and blocks per 90 — the actions FPL now awards points for.",
    ),
    "xgi": (
        "xG involvement",
        "Expected goals plus expected assists: the chances a player creates **and** finishes, before luck "
        "is applied.",
    ),
    "minutes_weight": (
        "Minutes weight",
        "How reliably he starts, 0–1, from his recent minutes. It scales every projection: a brilliant "
        "player who plays sixty minutes is worth less than the same player playing ninety.",
    ),
    "grade": (
        "Club grade",
        "A → D, from the axes that decide FPL points for a club's players. It is a **rank against the "
        "other nineteen**, so a D in a strong league is not the same as a D in a weak one.",
    ),
    "bench_order": (
        "Bench order",
        "The order FPL will substitute from if a starter plays no minutes: first, second, third, then "
        "your reserve keeper, who can only replace a keeper.",
    ),
}


def term(key: str) -> tuple[str, str] | None:
    """One entry, or None. ⭐ Never raises — a missing tooltip should hide, not take a screen down."""
    return TERMS.get(key)
