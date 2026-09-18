"""The transfer-flow log (ADR-210) — recording a *now* field before the next refresh destroys it.

⭐ **This is ADR-203's table, for the one other quantity that was still expiring.** `transfers_in_event` /
`transfers_out_event` / `selected_by` live on the single mutable `players` row; FPL resets the counters at
every deadline and publishes no history for them. ADR-190 discovered the consequence the hard way: its
instruction to *"re-measure `EXODUS_PRESSURE` on ≥4 gameweeks"* had no data to run on, so what it actually
produced was a **second single-week sample**, from a different point in a different week, 51% apart.

The tests below are about the two things that make the log usable at all: it is keyed by the event the
counter climbs toward, and every row carries the **phase** of the cycle it was read at.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.ingest import _record_transfer_flow
from src.storage import Storage


@dataclass
class _P:
    code: int
    transfers_in_event: int = 0
    transfers_out_event: int = 0
    selected_by: float = 10.0


@dataclass
class _F:
    event: int | None
    kickoff_time: str | None


# GW5 kicks off 18 Sep 19:00Z, so its deadline is 17:30Z that day; GW6 a fortnight later.
FIXTURES = [_F(5, "2026-09-18T19:00:00Z"), _F(5, "2026-09-20T15:30:00Z"), _F(6, "2026-10-10T11:30:00Z")]


def _store():
    return Storage(":memory:")


def test_a_reading_is_filed_against_the_gameweek_its_counter_is_climbing_TOWARD():
    """⚠️ Not the gameweek being played. FPL's counters reset at each deadline, so the number sitting on the
    players row on 14 September is *GW5's* accumulation even though GW4 is the gameweek just played. Filing
    it under GW4 would not raise — it would quietly build a series that cannot be compared with itself."""
    db = _store()
    rows = _record_transfer_flow(db, [_P(1, transfers_out_event=50_000)], FIXTURES,
                                 "2026-09-14T09:00:00+00:00")
    assert rows == 1
    (row,) = db.transfer_flow()
    assert row["event"] == 5, "the next deadline's gameweek, not the one just played"
    assert row["transfers_out"] == 50_000
    db.close()


def test_every_row_carries_how_far_from_the_deadline_it_was_read():
    """⭐⭐ The column the whole table exists for. These counters are an **accumulation** — they start at zero
    after a deadline and climb all week — so a value without its phase is not a measurement of anything.

    That is precisely what went wrong: read ~1 day into the cycle the p10 was −3,901; read ~5 days in it was
    −14,992. Two honest readings of the same season, 51% apart, and nothing recorded said they were taken at
    different points on a ramp. ADR-190 could only conclude *"it varies"*."""
    db = _store()
    _record_transfer_flow(db, [_P(1)], FIXTURES, "2026-09-13T17:30:00+00:00")   # 5 days out
    (row,) = db.transfer_flow(5)
    assert row["hours_to_deadline"] == 120.0
    db.close()


def test_the_row_for_a_gameweek_settles_on_the_LAST_reading_before_its_deadline():
    """One row per player per event, upserted — so the stored value is the end-of-cycle total, the one point
    in the week that is comparable across weeks. Every earlier reading of the same event is superseded."""
    db = _store()
    for when, out in (("2026-09-13T17:30:00+00:00", 10_000),    # 5 days out
                      ("2026-09-16T17:30:00+00:00", 40_000),    # 2 days out
                      ("2026-09-18T15:30:00+00:00", 90_000)):   # 2 hours out
        _record_transfer_flow(db, [_P(1, transfers_out_event=out)], FIXTURES, when)
    rows = db.transfer_flow(5)
    assert len(rows) == 1, "one row per player per event, not one per refresh"
    assert rows[0]["transfers_out"] == 90_000 and rows[0]["hours_to_deadline"] == 2.0
    db.close()


def test_a_new_gameweek_starts_a_new_row_rather_than_overwriting_the_old_one():
    """The reset is the reason for the table. Once GW5's deadline passes, FPL zeroes the counters and they
    start climbing toward GW6 — and GW5's total must survive that, because nothing can recover it."""
    db = _store()
    _record_transfer_flow(db, [_P(1, transfers_out_event=90_000)], FIXTURES, "2026-09-18T15:30:00+00:00")
    _record_transfer_flow(db, [_P(1, transfers_out_event=2_000)], FIXTURES, "2026-09-21T09:00:00+00:00")
    by_event = {r["event"]: r["transfers_out"] for r in db.transfer_flow()}
    assert by_event == {5: 90_000, 6: 2_000}
    db.close()


def test_the_recorder_cannot_take_down_the_refresh_it_rides_on():
    """⭐ ADR-203's rule, and it is not decorative: `refresh` is the app's lifeline and this is a side-record.
    A player FPL sends without a `code` is skipped; a season with no next deadline writes nothing."""
    db = _store()
    assert _record_transfer_flow(db, [_P(None), _P(2)], FIXTURES, "2026-09-14T09:00:00+00:00") == 1
    assert _record_transfer_flow(db, [_P(3)], [], "2026-09-14T09:00:00+00:00") == 0, "no deadline → no key"
    assert _record_transfer_flow(db, [_P(3)], FIXTURES, "2027-06-01T09:00:00+00:00") == 0, "season over"
    db.close()


def test_a_naive_timestamp_is_read_as_utc_rather_than_crashing_the_refresh():
    """`next_deadline` requires an aware `now` and raises on a naive one. The refresh passes an aware stamp,
    but a caller (or a future test) passing a bare ISO string must not bring the lifeline down."""
    db = _store()
    assert _record_transfer_flow(db, [_P(1)], FIXTURES, "2026-09-14T09:00:00") == 1
    db.close()


def test_refresh_records_the_flow_on_real_fixture_dataclasses():
    """⚠️ The bug this test exists for: `next_deadline` indexes its rows (`f["event"]`) because every other
    caller hands it `sqlite3.Row`s, while `refresh` holds `Fixture` **dataclasses**, which are not
    subscriptable. Testing the helper with dicts alone would have passed while the real path raised.

    ⭐ *A fixture that cannot express the thing the code reads will confirm a broken mechanism* — so this one
    uses the same dataclass `refresh` actually builds."""
    from src.models import Fixture

    db = _store()
    real = [Fixture(id=1, event=5, team_h=1, team_a=2, team_h_difficulty=3, team_a_difficulty=3,
                    finished=False, kickoff_time="2026-09-18T19:00:00Z")]
    assert _record_transfer_flow(db, [_P(1)], real, datetime(2026, 9, 14, 9, tzinfo=UTC).isoformat()) == 1
    db.close()
