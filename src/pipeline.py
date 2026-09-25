"""The autonomous data pipeline — fetch, validate, publish or refuse (ADR-211, Phase 2c).

Until now data reached users because a person ran `reseed` and committed a 956 KB binary. This module is what
replaces that person: a scheduled job decides whether a refresh is due, runs it, **checks what FPL sent before
any of it is stored**, and records the outcome — including a refusal — where both clients can see it.

⭐ **Three things a human did implicitly, now written down:**

* **Judgement about *when*.** A person refreshes before a deadline because they know one is coming. The
  cadence below derives that from the fixtures instead, so nothing has to be scheduled by hand — see
  `refresh_due`.
* **Judgement about *whether*.** A person notices when a fetch looks wrong and does not commit it. Server-side
  nobody is watching, and the blast radius is every user at once — see `validate`.
* **Saying what happened.** A person knows they ran it. `data_status` is how an unattended pipeline says so,
  ⭐ *including when it failed* — recording only successes would make a dead pipeline indistinguishable from
  a quiet one.
"""

from datetime import UTC, datetime, timedelta

from src import ingest
from src.analytics.deadline import next_deadline
from src.analytics.team_dna import team_dna_all
from src.analytics.xp import decision_xp
from src.api.client import FplApiError
from src.ingest import PayloadRejected
from src.storage import Storage

# ── Cadence ───────────────────────────────────────────────────────────────────────────────────────────────
#
# ⭐ **The schedule is Python, not cron, because the thing it depends on moves every week.** GitHub Actions
# cannot know when Saturday's deadline is; the fixtures do. So the workflow ticks every 15 minutes and this
# decides whether there is anything worth doing — which also means the policy is *testable*, and a cheap
# early exit costs a few seconds rather than an FPL request.
LIVE_WINDOW = timedelta(hours=2, minutes=30)     # a match is "in play" for about this long after kick-off
PRE_DEADLINE_WINDOW = timedelta(hours=1)         # ADR-211: four attempts in the last hour, not one precise one

INTERVAL_LIVE = timedelta(minutes=10)            # scores and provisional points move
INTERVAL_PRE_DEADLINE = timedelta(minutes=15)    # team news and price changes cluster; ADR-210's counters reset
INTERVAL_NORMAL = timedelta(hours=1)
INTERVAL_QUIET = timedelta(hours=6)              # overnight: prices settle, little else moves
QUIET_HOURS = range(1, 6)                        # 01:00-05:59 UTC


def _parse(when):
    """An ISO string (or datetime) → an aware UTC datetime, or None."""
    if when is None:
        return None
    if isinstance(when, datetime):
        return when if when.tzinfo else when.replace(tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(str(when).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _a_match_is_in_play(fixtures, now) -> bool:
    """Has a fixture kicked off within the live window without being marked finished?"""
    for f in fixtures or []:
        try:
            kicked, finished = _parse(f["kickoff_time"]), f["finished"]
        except (KeyError, IndexError, TypeError):
            continue
        if kicked and not finished and kicked <= now <= kicked + LIVE_WINDOW:
            return True
    return False


def cadence(fixtures, now) -> tuple[timedelta, str]:
    """How often a refresh should run *right now*, and why — ordered most urgent first."""
    if _a_match_is_in_play(fixtures, now):
        return INTERVAL_LIVE, "a gameweek is in play"
    upcoming = next_deadline(fixtures or [], now)
    if upcoming and now >= upcoming[1] - PRE_DEADLINE_WINDOW:
        # ⭐ ADR-210's transfer counters reset at this deadline, and the reading before it cannot be recovered
        # afterwards. Four chances in the last hour is the redundancy that makes cron's drift survivable.
        return INTERVAL_PRE_DEADLINE, f"GW{upcoming[0]} deadline is within the hour"
    if now.hour in QUIET_HOURS:
        return INTERVAL_QUIET, "overnight"
    return INTERVAL_NORMAL, "ordinary hours"


def refresh_due(fixtures, now=None, last_attempt=None) -> tuple[bool, str]:
    """Is a refresh due, and why (or why not)?

    ⚠️ **No fixtures means a first run, which is always due** — an empty database must be able to bootstrap
    itself, and a cadence derived from fixtures cannot be derived when there are none.
    """
    now = now or datetime.now(UTC)
    if not fixtures:
        return True, "no fixtures stored yet — bootstrapping"
    interval, why = cadence(fixtures, now)
    previous = _parse(last_attempt)
    if previous is None:
        return True, f"no previous attempt recorded ({why})"
    waited = now - previous
    if waited >= interval:
        return True, f"{why} — {interval} since the last attempt"
    return False, f"{why} — next due in {interval - waited}"


# ── Publishing the analytics (ADR-213) ────────────────────────────────────────────────────────────────────

XP_BOARD_HORIZON = 8        # the UI slider's maximum; one board answers every horizon 1..8

class BoardRejected(Exception):
    """A computed xP board failed its sanity checks, so nothing was published."""


def validate_board(board, players) -> None:
    """Check a board **before it replaces the last good one**.

    ⭐ ADR-211's rule, applied to a second thing: *once storing is publishing, a check that runs afterwards is
    not a check* — the previous board is already gone by then.

    ⚠️ **A bad xP board is more dangerous than a stale one**, and that is why this exists at all. Stale data
    announces itself through `data_status`; a board where every goalkeeper scores 40 announces nothing. It
    would simply be wrong, confidently, on every screen.

    ⚠️ These bounds are **declared, not measured** — the same honest caveat ADR-211 put on its payload
    checks. They are a smoke alarm, not a thermostat: wide enough that a real January fixture pile-up passes,
    because a check that blocks good data is worse than one that admits slightly odd data.
    """
    if not board:
        raise BoardRejected("empty board")
    if len(board) < len(players) * 0.9:
        raise BoardRejected(f"only {len(board)} rows for {len(players)} players")
    broken = [r["id"] for r in board if "by_gameweek_exact" not in r][:3]
    if broken:
        raise BoardRejected(f"rows with no breakdown field at all, e.g. {broken}")

    # ⚠️ **An EMPTY breakdown is not a broken one**, and an earlier draft of this function conflated them.
    # A player with no fixtures in the window legitimately has `{}` — end of season, or a club whose next
    # game is beyond the horizon. The first version rejected that, which would have refused a perfectly good
    # board; it was caught by an existing pipeline test, on a 650-player fixture with no upcoming games.
    # ⭐ *A check that blocks good data is worse than one that admits slightly odd data* (ADR-211).
    if not any(r.get("by_gameweek_exact") for r in board):
        return                                       # no window at all — nothing to sanity-check

    # ⭐ *The failure that produces a plausible-looking answer is the one worth a check.* A broken history
    # load does not raise — it scores nobody, and every screen renders happily.
    if not any(sum(r["by_gameweek_exact"].values()) > 0 for r in board):
        raise BoardRejected("every player scores zero")
    hottest = max(sum(r["by_gameweek_exact"].values()) for r in board)
    if hottest > 200:
        raise BoardRejected(f"implausible top score {hottest:.0f} over {XP_BOARD_HORIZON} gameweeks")


def publish_board(store: Storage, *, computed_at: str) -> dict:
    """Compute and publish the board-wide xP table. Returns `{"rows": n}` or raises `BoardRejected`.

    ⭐⭐ **Calls the same `decision_xp` the CLI, the web app and `ask` call.** Not a copy, not a
    pipeline-shaped variant — ADR-181 was written because an optional argument on a shared helper quietly
    priced a different player at one call site, and this is the same helper serving a new consumer.
    """
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    board = decision_xp(players, upcoming, store.get_history_by_code(),
                        horizon=XP_BOARD_HORIZON,
                        gw_history_by_code=store.get_gw_history_by_code())
    validate_board(board, players)
    first_event = min((gw for r in board for gw in r["by_gameweek_exact"]), default=None)
    if first_event is None:
        # ⭐ **No upcoming fixtures is a fact about the season, not a failure.** Refusing here would fail an
        # otherwise-healthy tick every day of the summer; publishing a board of zeros would be worse still,
        # because it reads as "nobody scores" rather than "there is nothing to score in". So: skip, say so,
        # and leave the last real board in place for anyone still looking at it.
        return {"rows": 0, "first_event": None, "skipped": "no upcoming fixtures"}
    rows = store.publish_xp_board(board, first_event=first_event, computed_at=computed_at)
    return {"rows": rows, "first_event": first_event}


def validate_team_dna(profiles, players) -> None:
    """Sanity-check a Team DNA board before it replaces the last good one.

    ⚠️ **A missing club is the failure worth catching**, because the symptom on a phone is *"my team is not
    there"* rather than an error.

    ⭐ **Checked against the teams the PLAYERS belong to**, which took two wrong answers to get right.
    Hardcoding 20 rejected an existing fixture that legitimately has one team; counting the `teams` table
    rejected it too, because `team_dna_all` builds its pool from players, not from that table. *A check must
    be expressed against the same population the thing under test derives from* — otherwise it is measuring a
    different question and will be wrong on the edges.
    """
    pool = {p["team"] for p in players if p["team"]}
    if len(profiles) != len(pool):
        raise BoardRejected(f"{len(profiles)} team profiles for {len(pool)} teams in the player pool")
    flat = [a for t in profiles.values() for a in t.axes]
    if not flat:
        raise BoardRejected("no axes on any team")
    pct = [getattr(a, "percentile", None) for a in flat]
    if any(p is None or not 0 <= p <= 100 for p in pct):
        raise BoardRejected("a percentile outside 0-100")
    # ⭐ **Percentiles that are ALL identical mean the ranking never ran** — the pool collapsed and every club
    # came back with the no-peers default. It raises nothing upstream; it just grades everyone the same.
    # ⚠️ Only meaningful with something to rank against: one club in the pool has no peers, and identical
    # percentiles are then the correct answer rather than a symptom.
    if len(pool) > 1 and len(set(pct)) == 1:
        raise BoardRejected(f"every percentile is {pct[0]} — the ranking did not run")


def publish_team_dna(store: Storage, *, computed_at: str) -> dict:
    """Compute and publish the Team DNA board. ⭐ Calls the same `team_dna_all` the web app calls."""
    profiles = team_dna_all(store.get_players(), store.get_upcoming_fixtures(),
                            gw_history=store.get_gw_history_by_code())
    if not profiles:
        return {"rows": 0, "skipped": "no team profiles"}
    validate_team_dna(profiles, store.get_players())
    return {"rows": store.publish_team_dna_board(profiles, computed_at=computed_at)}


# ── The run ───────────────────────────────────────────────────────────────────────────────────────────────

def run(store: Storage, *, now=None, force: bool = False, client=None, elo_client=None) -> dict:
    """One pipeline tick: decide, fetch, validate, publish or refuse — and record what happened.

    Returns a dict describing the outcome (`ran`, `ok`, `reason`, `counts`), so the CLI can print it and a
    test can assert on it. ⭐ **Never raises for a rejected payload or a failed fetch** — an unattended job
    that dies on a bad afternoon tells nobody anything; one that records a refusal can be looked at later.
    """
    now = now or datetime.now(UTC)
    stamp = now.isoformat(timespec="seconds")
    status = store.data_status()
    last_attempt = status["attempted_at"] if status else None

    due, why = refresh_due(store.get_all_fixtures(), now, last_attempt)
    if not due and not force:
        return {"ran": False, "ok": None, "reason": why, "counts": None}

    try:
        counts = ingest.refresh(store, client=client, elo_client=elo_client, now=stamp)
    except PayloadRejected as rejected:
        # ⭐ The refusal is the feature. Nothing was written, the last good data still serves every client,
        # and the reason is recorded where the app can show it rather than dying in a log nobody reads.
        store.set_data_status(attempted_at=stamp, ok=False, note=f"rejected: {rejected}")
        return {"ran": True, "ok": False, "reason": str(rejected), "counts": None}
    except FplApiError as exc:
        store.set_data_status(attempted_at=stamp, ok=False, note=f"fetch failed: {exc}")
        return {"ran": True, "ok": False, "reason": f"fetch failed: {exc}", "counts": None}

    # ⭐ **The analytics run AFTER the data is stored and BEFORE the run is called good.** The board is
    # derived from what was just written, so it cannot be computed earlier; and a refresh that published
    # players but not their xP would leave the two tables describing different moments (ADR-213).
    upcoming = next_deadline(store.get_all_fixtures(), now)
    try:
        published = publish_board(store, computed_at=stamp)
        team_dna = publish_team_dna(store, computed_at=stamp)
    except BoardRejected as bad:
        # ⭐⭐ **`refreshed_at` still moves, and that is not a slip.** By this point `ingest.refresh` has
        # already written the players — the raw data genuinely did refresh, and the sidebar reads exactly
        # this field to say so. Withholding it would make the app report **stale data that is actually
        # fresh**: a false alarm, and one nobody could diagnose from the screen.
        #
        # ⭐ *Each artefact reports its own freshness.* `refreshed_at` is about the FPL data; the board's age
        # is `xp_board.computed_at`, which stays where it was because the refused board never replaced it.
        # `ok=False` plus the note is what says something went wrong, without lying about which thing.
        store.set_data_status(refreshed_at=stamp, attempted_at=stamp,
                              event=upcoming[0] if upcoming else None,
                              ok=False, note=f"board rejected: {bad}")
        return {"ran": True, "ok": False, "reason": f"board rejected: {bad}",
                "counts": counts, "board": None, "team_dna": None}

    store.set_data_status(refreshed_at=stamp, attempted_at=stamp,
                          event=upcoming[0] if upcoming else None, ok=True, note=None)
    # ⚠️ **The board count is its own key, not folded into `counts`.** `ingest.refresh` returns a 4-tuple
    # that `describe()` unpacks positionally — appending to it would break the line a person actually reads.
    return {"ran": True, "ok": True, "reason": why, "counts": counts,
            "board": published, "team_dna": team_dna}


def describe(outcome: dict) -> str:
    """One line for the CLI and the Actions log — the thing a person reads when they check on it."""
    if not outcome["ran"]:
        return f"Nothing to do — {outcome['reason']}."
    if outcome["ok"]:
        players, teams, fixtures, elo = outcome["counts"]
        # ⭐ **The board gets its own clause.** Every other thing this tick publishes is named here, and the
        # one that is silent is the one nobody notices has stopped — the lesson ADR-211 landed on for
        # headlines (*stale headlines do not look stale*). A skipped board says so rather than vanishing.
        board = outcome.get("board") or {}
        if board.get("skipped"):
            xp = f", xP board skipped ({board['skipped']})"
        else:
            xp = f", xP board {board.get('rows', 0)} players from GW{board.get('first_event')}"
        dna = outcome.get("team_dna") or {}
        tdna = (f", Team DNA skipped ({dna['skipped']})" if dna.get("skipped")
                else f", Team DNA {dna.get('rows', 0)} teams")
        return (f"Published {players} players, {teams} teams, {fixtures} fixtures, {elo} Elo{xp}{tdna} "
                f"({outcome['reason']}).")
    return f"REFUSED — {outcome['reason']}. The last good data still stands."


# ── The per-gameweek history backfill ─────────────────────────────────────────────────────────────────────
#
# A different job on a different clock: ~659 throttled requests (≈3–5 minutes) once per gameweek, after the
# results post — against the core refresh's 3.6 seconds every few minutes. Its own workflow, its own stamp.

def _completed_rounds(fixtures) -> set:
    """Gameweeks whose fixtures have **all** finished — the rounds whose history is worth fetching."""
    played, pending = set(), set()
    for f in fixtures or []:
        try:
            event, finished = f["event"], f["finished"]
        except (KeyError, IndexError, TypeError):
            continue
        if event is None:
            continue
        (played if finished else pending).add(event)
    return played - pending


#: ⭐⭐⭐ **What shape of per-gameweek history the current code writes.** Bump this whenever a column is
#: **added** to `player_history` and the new column needs values for weeks already stored.
#:
#: ⚠️⚠️⚠️ **This exists because a migration is not a backfill, and nothing noticed the difference.**
#: ADR-298 added `yellow_cards` and `red_cards`. The migration ran, the columns appeared, every test
#: passed — and production served **zero bookings for every player in every gameweek**, because the rows
#: were written before the columns existed and the backfill gate asks *"is a completed gameweek
#: missing?"*, which they were not. The bug surfaced as a tester saying *"don't see red or yellow
#: cards"*, on a screen whose whole job was to show them.
#:
#: ⭐ *A row that exists is not a row that is current*, and a gate that only counts rows cannot tell the
#: two apart. The version number can.
#:
#: 2 — `yellow_cards` / `red_cards` (ADR-298).
HISTORY_SCHEMA = 2


def backfill_due(fixtures, gw_history_by_code) -> tuple[bool, str, set]:
    """Which completed gameweeks have no stored history yet — `(due, why, rounds)`.

    ⭐⭐ **"We have this gameweek" is asked with the analytics' own definition, not a second one.**
    `minutes.completed_gameweeks` is what `in_season_share`, the backtest and ADR-203's availability log all
    use: a round counts as held only when its rows carry a **scoreline**, never on row presence and never on
    `minutes == 0` — because FPL writes a player's per-gameweek row when the fixture is merely *scheduled*
    (ADR-125/129).

    ⚠️ Had the pipeline invented its own test — "are there rows for round N?" — it would have found the
    scheduled-but-unplayed rows, concluded the work was done, and left the analytics with a gameweek they
    cannot see. ⭐ *The pipeline's "done" has to be the consumer's "have".*
    """
    from src.analytics.minutes import completed_gameweeks

    finished = _completed_rounds(fixtures)
    held = completed_gameweeks(gw_history_by_code)
    missing = finished - held
    if not missing:
        return False, f"history held for every completed gameweek ({sorted(held) or 'none played'})", set()
    return True, f"no stored history for GW{sorted(missing)}", missing


def rewalk_due(stored_schema, gw_history_by_code) -> tuple[bool, str, set]:
    """Were the rows we hold written **before** the columns we now read existed? — `(due, why, rounds)`.

    ⚠️⚠️⚠️ **A different question from `backfill_due`, and merging the two was a mistake I made and
    caught here.** *"Is a gameweek missing?"* is what a **reader** needs — it drives the app's stale-data
    banner, which exists to say *"the numbers on this screen are from yesterday."* *"Were these rows
    written at an older schema?"* is what the **pipeline** needs, and it is not a reader-facing fault at
    all: every number on the screen is correct, one secondary column is simply empty.

    ⭐ Asking both through one function put `behind: true` and `missing_gameweeks: [1,2,3,4,5]` into every
    `my-team` response — ⚠️ *nine testers told their data was broken when it was not, which would have
    been a worse bug than the blank column it was reporting.*
    """
    from src.analytics.minutes import completed_gameweeks

    held = completed_gameweeks(gw_history_by_code)
    if (stored_schema or 0) >= HISTORY_SCHEMA:
        return False, f"history is at schema v{HISTORY_SCHEMA}", set()
    # ⚠️⚠️ **Nothing held is nothing to rewrite**, and without this an empty database asks for 659
    # throttled requests to refresh rows that do not exist. ⭐ *This check is about rows that arrived
    # before the question changed; where there are no rows there is no such thing.* A fresh database gets
    # its history through the missing-gameweek path above and is stamped on the way out.
    if not held:
        return False, "no stored history to bring forward", set()
    # ⭐ Every completed round, not just the newest: the empty values are in the **old** rows, which is
    # precisely the set any freshness check would skip.
    return (True,
            f"history was written at schema v{stored_schema or 0}, code writes v{HISTORY_SCHEMA} — "
            f"the columns added since have no values for GW{sorted(held)}",
            set(held))


def run_backfill(store: Storage, *, now=None, force: bool = False, client=None, sleep=None) -> dict:
    """Fetch per-gameweek history when a completed gameweek is missing it (ADR-211 2d).

    ⚠️ **Expensive and deliberately rare.** One request per player, throttled — so this is gated on a
    gameweek actually being missing rather than run on a clock. It is idempotent and resumable already
    (upsert on code+round), so a partial run simply completes next time.

    Never raises: like `run`, an unattended job that dies tells nobody anything.
    """
    now = now or datetime.now(UTC)
    stamp = now.isoformat(timespec="seconds")
    status = store.data_status()
    stored_schema = None
    if status is not None:
        # ⚠️ `sqlite3.Row` and a psycopg row both index by name, but neither has `.get` — and a database
        # that predates the column has no key at all. ⭐ *A freshness check that throws is a pipeline that
        # stops refreshing*, which is worse than the staleness it was added to catch.
        try:
            stored_schema = status["backfilled_schema"]
        except (KeyError, IndexError):
            stored_schema = None
    history = store.get_gw_history_by_code()
    due, why, rounds = backfill_due(store.get_all_fixtures(), history)
    if not due:
        # ⭐ Only when nothing is outright missing: a gameweek with no rows is the bigger hole and the
        # more useful message.
        due, why, rounds = rewalk_due(stored_schema, history)
    if not due and not force:
        return {"ran": False, "ok": None, "reason": why, "rounds": []}

    try:
        kwargs = {"client": client} if client is not None else {}
        if sleep is not None:
            kwargs["sleep"] = sleep
        players, seasons, gameweeks, failures = ingest.backfill_history(store, **kwargs)
    except FplApiError as exc:
        store.set_data_status(backfilled_at=stamp)
        return {"ran": True, "ok": False, "reason": f"backfill failed: {exc}", "rounds": sorted(rounds)}

    # ⭐ Stamped only on a **clean** run. A backfill that failed part-way must not claim the new shape, or
    # the gate goes quiet with half the values still missing — ⚠️ *the exact silence this whole mechanism
    # was added to break.*
    store.set_data_status(backfilled_at=stamp, backfilled_event=max(rounds) if rounds else None,
                          backfilled_schema=HISTORY_SCHEMA if failures == 0 else None)
    return {"ran": True, "ok": failures == 0, "reason": why, "rounds": sorted(rounds),
            "counts": (players, seasons, gameweeks, failures)}


def describe_backfill(outcome: dict) -> str:
    """One line for the CLI and the Actions log."""
    if not outcome["ran"]:
        return f"Nothing to do — {outcome['reason']}."
    if outcome.get("counts") is None:
        return f"FAILED — {outcome['reason']}."
    players, _seasons, gameweeks, failures = outcome["counts"]
    tail = f" ⚠ {failures} player(s) failed and will be retried" if failures else ""
    return (f"Backfilled GW{outcome['rounds']}: {gameweeks} gameweek rows from {players} players{tail}.")
