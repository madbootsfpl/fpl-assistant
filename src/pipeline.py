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

    upcoming = next_deadline(store.get_all_fixtures(), now)
    store.set_data_status(refreshed_at=stamp, attempted_at=stamp,
                          event=upcoming[0] if upcoming else None, ok=True, note=None)
    return {"ran": True, "ok": True, "reason": why, "counts": counts}


def describe(outcome: dict) -> str:
    """One line for the CLI and the Actions log — the thing a person reads when they check on it."""
    if not outcome["ran"]:
        return f"Nothing to do — {outcome['reason']}."
    if outcome["ok"]:
        players, teams, fixtures, elo = outcome["counts"]
        return (f"Published {players} players, {teams} teams, {fixtures} fixtures, {elo} Elo "
                f"({outcome['reason']}).")
    return f"REFUSED — {outcome['reason']}. The last good data still stands."
