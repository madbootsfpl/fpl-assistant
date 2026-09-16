"""Availability is recorded as it passes, because it cannot be recovered afterwards (ADR-203).

FPL serves `status` / `chance` / `news` as a **now** field: the bootstrap payload says whether a player is fit
*today* and keeps no history. Every refresh overwrote the previous answer, so the question *"was he flagged
when that gameweek kicked off?"* had no source at all — which is why ADR-202's baseline had to score the model
with today's injury news applied retrospectively to round 1, and said so as its one uncloseable leak.

The shape under test is a **change log with intervals**, and both halves matter: rows only on change (a row
per player per refresh is ~480k a season and says nothing more), but each row carrying `observed_at` **and**
`last_seen_at`, because ⭐ *a change log alone cannot tell "unchanged" from "not observed"* — three silent
weeks and three stable weeks would otherwise look identical.
"""

from types import SimpleNamespace

from src.storage import Storage


def _p(code, status="a", chance=None, news=""):
    return SimpleNamespace(code=code, status=status, chance=chance, news=news)


def _rows(conn):
    return [tuple(r) for r in conn.execute(
        "SELECT element_code, observed_at, last_seen_at, status, chance FROM player_availability "
        "ORDER BY element_code, observed_at")]


def test_an_unchanged_player_extends_one_row_instead_of_adding_another(tmp_path):
    """The volume argument, and the reason it is safe: nothing is lost by not writing a row."""
    db = Storage(str(tmp_path / "x.db"))
    try:
        db.save_availability([_p(1)], "2026-09-01T10:00:00+00:00")
        db.save_availability([_p(1)], "2026-09-02T10:00:00+00:00")
        db.save_availability([_p(1)], "2026-09-03T10:00:00+00:00")
        assert _rows(db.conn) == [
            (1, "2026-09-01T10:00:00+00:00", "2026-09-03T10:00:00+00:00", "a", None)
        ], "three refreshes with no change must be one row whose window grew"
    finally:
        db.close()


def test_a_change_opens_a_new_row_and_leaves_the_old_one_closed(tmp_path):
    db = Storage(str(tmp_path / "x.db"))
    try:
        db.save_availability([_p(1)], "2026-09-01T10:00:00+00:00")
        db.save_availability([_p(1, status="d", chance=75, news="Knock")], "2026-09-05T10:00:00+00:00")
        db.save_availability([_p(1, status="a")], "2026-09-12T10:00:00+00:00")
        assert _rows(db.conn) == [
            (1, "2026-09-01T10:00:00+00:00", "2026-09-01T10:00:00+00:00", "a", None),
            (1, "2026-09-05T10:00:00+00:00", "2026-09-05T10:00:00+00:00", "d", 75),
            (1, "2026-09-12T10:00:00+00:00", "2026-09-12T10:00:00+00:00", "a", None),
        ]
    finally:
        db.close()


def test_news_alone_is_a_change(tmp_path):
    """*"Knock — 75%"* becoming *"Knock — expected back 20 Sep"* is new information at the same status."""
    db = Storage(str(tmp_path / "x.db"))
    try:
        db.save_availability([_p(1, status="d", chance=75, news="Knock")], "2026-09-01T10:00:00+00:00")
        db.save_availability([_p(1, status="d", chance=75, news="Knock - back 20 Sep")],
                             "2026-09-02T10:00:00+00:00")
        assert len(_rows(db.conn)) == 2
    finally:
        db.close()


def test_reading_as_of_a_date_gives_what_was_known_then_not_what_is_known_now(tmp_path):
    """The whole point: a walk-forward read must not see a flag that had not been raised yet."""
    db = Storage(str(tmp_path / "x.db"))
    try:
        db.save_availability([_p(1), _p(2)], "2026-09-01T10:00:00+00:00")
        db.save_availability([_p(1, status="i", chance=0, news="Hamstring"), _p(2)],
                             "2026-09-10T10:00:00+00:00")

        before = db.availability_as_of("2026-09-05T00:00:00+00:00")
        assert before[1][0] == "a", "the injury was not known on the 5th and must not appear"

        after = db.availability_as_of("2026-09-15T00:00:00+00:00")
        assert after[1][0] == "i"
        assert after[2][0] == "a"
    finally:
        db.close()


def test_the_reader_reports_how_stale_the_value_is(tmp_path):
    """⭐ *A status last confirmed three weeks ago is not the same evidence as one confirmed this morning* —
    so the window is returned with the value, not hidden behind it."""
    db = Storage(str(tmp_path / "x.db"))
    try:
        db.save_availability([_p(1, status="d", chance=50)], "2026-09-01T10:00:00+00:00")
        db.save_availability([_p(1, status="d", chance=50)], "2026-09-02T10:00:00+00:00")
        status, chance, _news, observed_at, last_seen_at = db.availability_as_of("2026-09-30T00:00:00+00:00")[1]
        assert (status, chance) == ("d", 50)
        assert observed_at == "2026-09-01T10:00:00+00:00"
        assert last_seen_at == "2026-09-02T10:00:00+00:00", (
            "the caller must be able to see the value was last confirmed on the 2nd, not the 30th")
    finally:
        db.close()


def test_an_older_database_gains_the_table_without_a_reseed(tmp_path):
    db_path = tmp_path / "x.db"
    first = Storage(str(db_path))
    first.conn.execute("DROP TABLE player_availability")
    first.conn.commit()
    first.close()

    again = Storage(str(db_path))
    try:
        again.save_availability([_p(1)], "2026-09-01T10:00:00+00:00")
        assert len(_rows(again.conn)) == 1
    finally:
        again.close()
