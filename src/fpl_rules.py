"""A curated, authoritative FPL-rules knowledge base (Sprint 100, ADR-085).

The AI Chat Assistant answers **rules** questions from *these* facts — never the LLM's memory (which
hallucinates rules). The LLM only phrases the matched facts, and the answer is **verified** against them
(✓, ADR-037). Pure data + a keyword matcher; no I/O.

Facts are phrased for the **2025/26** season. If the FPL rules change, update this one file. Keep each `fact`
short, self-describing, and numeric where the number is the answer (so the verifier can trace it).
"""

from datetime import timedelta

# Each entry: a `topic` (a stable id), the `cues` that a question about it contains, and the authoritative
# `fact` string. `match_rules` returns every entry whose cue appears in the question, in list order.
RULES = [
    {
        "topic": "scoring",
        "cues": ("points for", "how many points", "scoring", "points scored", "points system",
                 "worth how many", "goal worth", "assist worth"),
        "fact": ("Scoring:\n"
                 "  • Appearance: 1 point up to 60 minutes, 2 points for 60+.\n"
                 "  • Goal: 6 (GK/DEF), 5 (MID), 4 (FWD); an assist is 3.\n"
                 "  • Cards: yellow −1, red −3; own goal −2; missed penalty −2."),
    },
    {
        "topic": "clean_sheets",
        "cues": ("clean sheet", "cleansheet", "goals conceded", "saves", "penalty save", "keeper points",
                 "goalkeeper points"),
        "fact": ("Clean sheets & keepers:\n"
                 "  • Clean sheet: 4 points (GK/DEF), 1 (MID), 0 (FWD) — only with 60+ minutes played.\n"
                 "  • Goalkeeper: 1 point per 3 saves; 5 points for a penalty save.\n"
                 "  • GK/DEF lose 1 point for every 2 goals their team concedes."),
    },
    {
        "topic": "bonus",
        "cues": ("bonus point", "bps", "bonus points system", "how is bonus", "how are bonus"),
        "fact": ("Bonus points: the three best performers in a match by the Bonus Points System (BPS) get 3, "
                 "2 and 1 extra point. BPS rewards goals, assists, saves, tackles and more, and penalises "
                 "cards, misses and goals conceded."),
    },
    {
        "topic": "defensive_contribution",
        "cues": ("defensive contribution", "defcon", "def con", "cbit", "tackles and interceptions",
                 "recoveries points"),
        "fact": ("Defensive Contribution (2024/25 onwards): a defender who reaches 10 clearances, blocks, "
                 "interceptions and tackles (CBIT) in a match earns 2 points; a midfielder or forward earns 2 "
                 "for reaching 12 of those actions plus ball recoveries."),
    },
    {
        "topic": "chips",
        "cues": ("chip", "wildcard", "free hit", "bench boost", "triple captain", "how do chips",
                 "how does the wildcard", "which chips"),
        "fact": ("Chips:\n"
                 "  • Wildcard = unlimited free transfers this gameweek, kept permanently.\n"
                 "  • Free Hit = unlimited transfers for one gameweek only, then your squad reverts.\n"
                 "  • Bench Boost = your bench's points count this gameweek.\n"
                 "  • Triple Captain = your captain scores 3× instead of 2×.\n"
                 "  Each chip is used once per half of the season (a fresh set unlocks around gameweek 20)."),
    },
    {
        "topic": "transfers",
        "cues": ("transfer", "free transfer", "how many transfers", "transfer hit", "points hit",
                 "-4", "minus 4", "roll transfer", "save transfer", "extra transfer"),
        "fact": ("Transfers: you get 1 free transfer each gameweek. Unused free transfers roll over, up to a "
                 "maximum of 5 saved. Each transfer beyond your free ones costs 4 points. A Wildcard or Free "
                 "Hit gives unlimited transfers that gameweek with no points hit."),
    },
    {
        "topic": "price_changes",
        "cues": ("price change", "price rise", "price fall", "value change", "sell-on", "sell on fee",
                 "player value", "price go up"),
        "fact": ("Prices: a player's price rises or falls in £0.1m steps based on how many managers are "
                 "transferring them in or out. When you sell a player for more than you paid, you keep 50% of "
                 "the profit (rounded down to £0.1m) — the rest is a sell-on fee."),
    },
    {
        "topic": "squad_rules",
        "cues": ("squad rules", "how many players", "budget", "£100", "100m", "max per club", "3 per club",
                 "three per club", "how much money", "starting budget"),
        "fact": ("Squad: 15 players — 2 goalkeepers, 5 defenders, 5 midfielders, 3 forwards — within a £100.0m "
                 "budget, and no more than 3 players from any one club."),
    },
    {
        "topic": "formation",
        "cues": ("formation", "how many defenders", "valid lineup", "valid formation", "how many can i play",
                 "starting eleven", "starting xi rules"),
        "fact": ("Formations: your starting XI is 11 players with exactly 1 goalkeeper, at least 3 defenders "
                 "and at least 1 forward — so valid shapes range from 3-4-3 to 5-4-1 (3–5 DEF, 2–5 MID, "
                 "1–3 FWD)."),
    },
    {
        "topic": "captain",
        "cues": ("captain", "vice", "armband", "double points", "who captains"),
        "fact": ("Captain: your captain scores double points. If your captain plays 0 minutes, your "
                 "vice-captain is doubled instead."),
    },
    {
        "topic": "autosubs",
        "cues": ("auto sub", "auto-sub", "autosub", "automatic sub", "bench order", "substitution",
                 "if a player doesn't play"),
        "fact": ("Auto-subs: if a starter plays 0 minutes, the highest-priority bench outfielder who keeps a "
                 "valid formation is automatically substituted in. Your bench goalkeeper only ever replaces "
                 "your starting goalkeeper."),
    },
    {
        "topic": "deadline",
        "cues": ("deadline", "when is the deadline", "cut off", "cut-off", "lock time", "when do teams lock"),
        "fact": ("Deadline: your team locks 90 minutes before the kickoff of the first match of the "
                 "gameweek. Transfers, captain and chips must be set before then."),
    },
    {
        "topic": "gameweeks",
        "cues": ("double gameweek", "blank gameweek", "dgw", "bgw", "how many gameweeks", "38 gameweek",
                 "season length"),
        "fact": ("Season: there are 38 gameweeks. Later in the season some are Double Gameweeks (a team plays "
                 "twice) or Blank Gameweeks (a team doesn't play) due to cup and rescheduling — these are when "
                 "chips like Bench Boost and Triple Captain are often most valuable."),
    },
    {
        "topic": "flags",
        "cues": ("flag", "yellow flag", "red flag", "chance of playing", "what does the flag", "is he a doubt",
                 "75%", "50%", "25%", "player status"),
        "fact": ("Player flags: a red flag means unavailable (injured/suspended/not expected to play — 0% "
                 "chance). A yellow/orange flag means a doubt, with the chance of playing shown as 75%, 50% or "
                 "25%. No flag = expected to be available. The player's news explains the reason."),
    },
    {
        "topic": "preseason_transfers",
        "cues": ("before the season", "before gameweek 1", "before the first deadline", "preseason transfers",
                 "unlimited transfers before", "rebuild before"),
        "fact": ("Before the season starts you can make unlimited free transfers and rebuild your squad as "
                 "often as you like, up to the Gameweek 1 deadline — no points cost. The 1-free-transfer rule "
                 "only begins once the season is under way."),
    },
    {
        "topic": "chip_limits",
        "cues": ("two chips", "more than one chip", "chips in one gameweek", "same gameweek chip", "stack chips",
                 "one chip per", "multiple chips"),
        "fact": ("You can play only one chip per gameweek. Each chip (Wildcard, Free Hit, Bench Boost, Triple "
                 "Captain) is used once per half of the season, with a fresh set unlocking around Gameweek 20."),
    },
    {
        "topic": "bench_points",
        "cues": ("bench points", "do bench players score", "does my bench score", "substitutes score",
                 "points on the bench", "bench count"),
        "fact": ("Only your starting XI scores each gameweek — your four bench players don't, unless you play "
                 "the Bench Boost chip (which counts all 15). A bench player can still come on via an auto-sub "
                 "if a starter plays 0 minutes."),
    },
    {
        "topic": "wildcard_timing",
        "cues": ("how many wildcards", "two wildcards", "second wildcard", "wildcard reset", "when can i "
                 "wildcard", "wildcard expire", "wildcard deadline"),
        "fact": ("Wildcards: you get two per season — one for the first half and one for the second (the second "
                 "unlocks around Gameweek 20). An unused first-half Wildcard is lost at the halfway point; "
                 "within its half a Wildcard has no time limit and makes every transfer that gameweek free."),
    },
    {
        "topic": "leagues",
        "cues": ("mini league", "mini-league", "classic league", "head to head", "head-to-head", "h2h",
                 "how do leagues", "league scoring", "join a league"),
        "fact": ("Leagues:\n"
                 "  • Classic: ranked by total points — join any time, scored from the gameweek you join.\n"
                 "  • Head-to-Head: two managers' gameweek scores compared — 3 points for a win, 1 a draw, "
                 "0 a loss."),
    },
    {
        "topic": "ranking",
        "cues": ("overall rank", "overall points", "gameweek rank", "how is rank", "rank calculated",
                 "world rank", "total points"),
        "fact": ("Ranking: your Overall Rank is your position among all managers by total points across the "
                 "season so far; your Gameweek Rank is just that week's score. Points are only deducted by −4 "
                 "transfer hits and the usual card/own-goal/missed-penalty deductions."),
    },
    {
        "topic": "team_value",
        "cues": ("team value", "selling price", "in the bank", "itb", "how much can i sell", "buy price",
                 "profit on a player", "squad value"),
        "fact": ("Team value = your squad's value plus money in the bank. When a player's price rises, your "
                 "selling price is the buy price plus half the rise (rounded down to £0.1m) — you don't keep "
                 "all the profit. A price fall comes off your selling price in full."),
    },
]

# The human list of what the assistant can explain — shown when a rules question matches no specific topic.
TOPIC_LABELS = ("scoring", "clean sheets & saves", "bonus points", "defensive contribution", "chips",
                "transfers & hits", "price changes", "squad rules", "formations", "captaincy", "auto-subs",
                "deadlines", "double/blank gameweeks", "player flags & availability", "pre-season transfers",
                "one chip per gameweek", "bench points", "wildcard timing", "mini-leagues",
                "overall vs gameweek rank", "team value & selling price")


# The one FPL rule the *code* has to act on, not just narrate: a gameweek locks 90 minutes before its first
# kickoff. Both the countdown (`analytics.deadline`, ADR-086) and the "which fixtures can I still act on?" filter
# (`Storage.get_upcoming_fixtures`, ADR-123) measure from it, so it lives here — in the rules module both can
# depend on — rather than being written down twice and drifting apart.
DEADLINE_LEAD = timedelta(minutes=90)


def match_rules(question: str, limit: int = 4) -> list:
    """The curated `(topic, fact)` pairs a rules question is about — every entry whose cue appears in the
    question, in KB order, capped at `limit`. Empty when nothing matches (the caller then goes free-form)."""
    q = (question or "").lower()
    hits = [(e["topic"], e["fact"]) for e in RULES if any(cue in q for cue in e["cues"])]
    return hits[:limit]


# --- transfer windows (ADR-154) ----------------------------------------------------------------------------
# A club can only sell a player while a window is open, so a "he is leaving" report outside one changes
# **nothing about this gameweek** — he plays on until January. Reacting to it would cost a real transfer for a
# move that cannot happen yet.
#
# Dates are the English windows and shift by a day or two each year, so they live here as data rather than
# buried in a condition. **Deliberately conservative at the edges:** the cost of the gate being a day early is
# that we stay quiet about a true story; the cost of it being a day late is advising a transfer nobody can
# make.
#
# ⚠️ Known incompleteness, worth stating rather than discovering: **other countries' windows do not match
# England's.** The Saudi Pro League has repeatedly stayed open for weeks after the Premier League shut — which
# is exactly the Watkins → Al-Hilal case this was built for. So this gate can suppress a *true* signal in
# early September. That is the right direction to be wrong in, and it is the reason this is a list of ranges
# that can gain a row rather than a single hard-coded pair.
TRANSFER_WINDOWS = (
    ("06-10", "09-01"),      # summer
    ("01-01", "02-02"),      # winter
)


def transfer_window_open(today) -> bool:
    """Is an English transfer window open on `today`? (ADR-154)

    Compared on month-day so the same table holds every season. A window that wraps the new year would need
    care; neither of these does.
    """
    stamp = f"{today.month:02d}-{today.day:02d}"
    return any(start <= stamp <= end for start, end in TRANSFER_WINDOWS)
