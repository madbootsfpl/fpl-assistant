"""Tests for the Admin tester roster + load panel (ADR-120).

The roster answers *"who is actually testing?"* without touching the anonymity invariant (ADR-100): it is a
**separate join** over the owner's own allow-list, not a field on an analytics event. That separation is the
thing most worth pinning — it is why `roster.py` exists as its own module rather than living in `analytics.py`.
"""

from datetime import datetime, timedelta, timezone

from src.web_streamlit import roster
from src.web_streamlit.analytics import load_summary

NOW = datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)


def _ago(**kw):
    return (NOW - timedelta(**kw)).isoformat()


# ---- the roster ---------------------------------------------------------------------

def test_a_tester_is_classified_by_when_they_last_persisted():
    assert roster.classify(_ago(days=1), NOW) == "active"
    assert roster.classify(_ago(days=12), NOW) == "dormant"
    assert roster.classify(_ago(days=90), NOW) == "lapsed"


def test_never_signed_in_is_its_own_state_not_the_far_end_of_dormant():
    """A tester who never arrived is a different problem — an unsent invite, a broken link — from one who
    signed in and drifted away."""
    assert roster.classify(None, NOW) == "never"
    assert roster.classify("", NOW) == "never"


def test_an_unparseable_timestamp_reads_as_never_rather_than_crashing():
    assert roster.classify("not-a-date", NOW) == "never"


def test_the_roster_sorts_the_quiet_ones_into_view():
    """The list exists to spot who has gone quiet; a column of blanks at the top would bury that."""
    upd = {"k_a": _ago(days=1), "k_b": _ago(days=12), "k_c": _ago(days=99)}
    rows = roster.build(["a@x.ie", "b@x.ie", "c@x.ie", "d@x.ie"], upd, key_for=lambda e: "k_" + e[0], now=NOW)
    assert [r["status"] for r in rows] == ["active", "dormant", "lapsed", "never"]
    assert rows[-1]["email"] == "d@x.ie" and rows[-1]["days"] is None


def test_the_roster_never_needs_supabase_or_streamlit():
    """`key_for` is injected, so identity derivation stays in auth and this stays a pure function."""
    rows = roster.build(["only@x.ie"], {}, key_for=lambda e: "unused", now=NOW)
    assert rows == [{"email": "only@x.ie", "last_active": None, "last_seen": None, "last_saved": None,
                     "status": "never", "days": None}]


def test_totals_count_every_state():
    upd = {"k_a": _ago(days=1), "k_b": _ago(days=1)}
    rows = roster.build(["a@x.ie", "b@x.ie", "c@x.ie"], upd, key_for=lambda e: "k_" + e[0], now=NOW)
    assert roster.totals(rows) == {"active": 2, "dormant": 0, "lapsed": 0, "never": 1, "registered": 3}


def test_an_empty_allow_list_is_safe():
    assert roster.build([], {}, key_for=str) == [] and roster.totals([])["registered"] == 0


# ---- load & concurrency --------------------------------------------------------------

def _ev(sid, mins_ago, op=None, ms=None):
    row = {"session_id": sid, "ts": (NOW - timedelta(minutes=mins_ago)).isoformat()}
    if op:
        row.update(event="perf", duration_ms=ms, meta={"op": op})
    return row


def test_active_now_counts_distinct_sessions_in_the_window():
    rows = [_ev("a", 1), _ev("a", 2), _ev("b", 3), _ev("c", 30)]
    assert load_summary(rows, NOW)["active_now"] == 2      # `a` twice is still one session; `c` is outside


def test_peak_concurrent_finds_the_busiest_window_not_the_current_one():
    """The number to watch is the deadline spike, which by definition isn't happening when you look."""
    rows = [_ev(s, 40) for s in "abcde"] + [_ev("z", 1)]
    out = load_summary(rows, NOW)
    assert out["active_now"] == 1 and out["peak_concurrent"] == 5


def test_p95_takes_the_worst_of_the_timed_operations():
    rows = [_ev("a", 1, "analysis", 900), _ev("b", 1, "data_load", 4000)]
    assert load_summary(rows, NOW)["p95_ms"] >= 4000


def test_health_escalates_on_either_concurrency_or_latency():
    assert load_summary([_ev("a", 1)], NOW)["health"] == "green"
    assert load_summary([_ev(s, 1) for s in "abcdef"], NOW)["health"] == "amber"
    assert load_summary([_ev("a", 1, "analysis", 9000)], NOW)["health"] == "red"


def test_no_events_is_green_and_empty_rather_than_an_error():
    out = load_summary([], NOW)
    assert out == {"active_now": 0, "peak_concurrent": 0, "p95_ms": None, "health": "green", "window_min": 10}


def test_rows_without_timestamps_are_ignored():
    assert load_summary([{"session_id": "a"}, {"ts": "2026-08-24T18:00:00Z"}], NOW)["active_now"] == 0


# ---- signing in is not the same as saving a squad (ADR-142) --------------------------

def test_status_follows_the_SIGN_IN_not_the_squad_save():
    """The reported bug. "Active" used to mean *saved a squad in the last 7 days* — which is not "used the
    app", and read as if it were. Most people sign in and browse; they never press save. On the live beta that
    reported **18 of 25 testers as ⚪ never** while at least two were using it daily.
    """
    rows = roster.build(["tony@x.ie"], {}, key_for=lambda e: "k",
                        seen_by_email={"tony@x.ie": _ago(days=1)}, now=NOW)
    assert rows[0]["status"] == "active", "signed in yesterday — active, with no squad ever saved"
    assert rows[0]["last_saved"] is None


def test_the_two_signals_are_kept_apart_rather_than_merged():
    """"Last used" and "last saved" answer different questions — who is *visiting* versus who is actively
    managing a team. Collapsing them is what caused the bug, so both stay on the row."""
    rows = roster.build(["a@x.ie"], {"k": _ago(days=20)}, key_for=lambda e: "k",
                        seen_by_email={"a@x.ie": _ago(days=2)}, now=NOW)
    assert rows[0]["last_seen"] == _ago(days=2)
    assert rows[0]["last_saved"] == _ago(days=20)
    assert rows[0]["status"] == "active", "judged on the visit, not the stale save"


def test_without_sign_in_data_it_degrades_to_the_old_behaviour():
    """`last_seen` needs a column added by hand, so until that happens the map is empty. The panel must fall
    back to what it did before — not report every tester as never-seen, which would be a worse lie than the
    one being fixed."""
    rows = roster.build(["a@x.ie"], {"k": _ago(days=1)}, key_for=lambda e: "k",
                        seen_by_email={}, now=NOW)
    assert rows[0]["status"] == "active" and rows[0]["last_saved"] == _ago(days=1)
    assert rows[0]["last_seen"] is None


def test_a_tester_who_only_ever_saved_still_counts():
    """A save is evidence of a visit even when the sign-in stamp predates the column existing."""
    rows = roster.build(["a@x.ie"], {"k": _ago(days=3)}, key_for=lambda e: "k",
                        seen_by_email={"b@x.ie": _ago(days=1)}, now=NOW)
    assert rows[0]["status"] == "active"


# ---- the store side: best-effort, and silent when the column isn't there yet ----------

def test_a_missing_last_seen_column_is_silent_not_an_error(monkeypatch):
    """`last_seen` has to be added by hand, so until it exists every read and write 400s. A tester must never
    see an error because an admin panel wants a nicer number — and the reader must return `{}` so the panel
    can say "this isn't on yet" rather than reporting everyone as never-seen."""
    import requests

    from src.web_streamlit import user_store

    def boom(*a, **kw):
        raise requests.HTTPError("column beta_users.last_seen does not exist")

    monkeypatch.setattr(user_store, "_endpoint", lambda: ("https://x/beta_users", "k"))
    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(requests, "patch", boom)

    assert user_store.last_seen_by_email(["a@x.ie"]) == {}
    assert user_store.touch_last_seen("a@x.ie")     # must not raise — and must say what went wrong


def test_the_stamp_patches_the_row_as_it_is_actually_spelled(monkeypatch):
    """A PostgREST `eq.` filter is case-**sensitive**, and the allow-list is hand-maintained — it currently
    holds both `markcondron88@gmail.com` and `Markcondron88@gmail.com`. `eq.<cleaned>` silently matches **no
    row** for the capitalised one, which is exactly the trap `is_registered` documents and exactly what the
    first version of this walked into. So the stored spelling is read first and *that* is patched.
    """
    import requests

    from src.web_streamlit import user_store

    seen = {}

    class R:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return [{"email": "Markcondron88@gmail.com"}]

    def fake_patch(url, params=None, json=None, headers=None, timeout=None):
        seen.update(params=params, json=json)

        class P:
            status_code = 200

            def json(self_inner):
                return [{"email": "Markcondron88@gmail.com"}]
        return P()

    monkeypatch.setattr(user_store, "_endpoint", lambda: ("https://x/beta_users", "k"))
    monkeypatch.setattr(requests, "get", lambda *a, **kw: R())
    monkeypatch.setattr(requests, "patch", fake_patch)

    assert user_store.touch_last_seen(" MARKCONDRON88@gmail.com ") == "ok"
    assert seen["params"] == {"email": "eq.Markcondron88@gmail.com"}, \
        "must patch the row as stored, not as cleaned — otherwise it matches nothing"
    assert "last_seen" in seen["json"]


def test_a_refused_write_is_NAMED_rather_than_swallowed(monkeypatch):
    """The reason this returns a status at all. The first version was silent best-effort, so when every
    `last_seen` came back NULL there was no way to tell whether the write was never attempted, never matched,
    or **refused by a row-level-security policy** — which is the usual cause, because a table needs SELECT and
    INSERT policies for the gate to work and can easily have no UPDATE policy at all.
    """
    import requests

    from src.web_streamlit import user_store

    class R:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return [{"email": "a@x.ie"}]

    class Denied:
        status_code = 401
        text = '{"message":"permission denied for table beta_users"}'

    monkeypatch.setattr(user_store, "_endpoint", lambda: ("https://x/beta_users", "k"))
    monkeypatch.setattr(requests, "get", lambda *a, **kw: R())
    monkeypatch.setattr(requests, "patch", lambda *a, **kw: Denied())

    out = user_store.touch_last_seen("a@x.ie")
    assert "401" in out and "permission denied" in out


def test_a_tester_not_on_the_allow_list_says_so_instead_of_pretending(monkeypatch):
    import requests

    from src.web_streamlit import user_store

    class R:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return [{"email": "someone@else.ie"}]

    monkeypatch.setattr(user_store, "_endpoint", lambda: ("https://x/beta_users", "k"))
    monkeypatch.setattr(requests, "get", lambda *a, **kw: R())
    monkeypatch.setattr(requests, "patch",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not write")))
    assert "isn't on the allow-list" in user_store.touch_last_seen("a@x.ie")


def test_nothing_is_written_when_the_store_is_unconfigured(monkeypatch):
    import requests

    from src.web_streamlit import user_store

    monkeypatch.setattr(user_store, "_endpoint", lambda: (None, None))
    monkeypatch.setattr(requests, "patch", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("no call")))
    assert user_store.touch_last_seen("a@x.ie") == "store not configured"
    assert user_store.last_seen_by_email(["a@x.ie"]) == {}


def test_zero_rows_updated_is_reported_as_RLS_not_as_a_missing_column(monkeypatch):
    """The live diagnosis (2026-08-26). The stamp came back *"wrote nothing — no row matched"*, and the first
    message guessed at a missing column. Wrong, and misleadingly so: the GET immediately above had just found
    that exact row, so the filter matches for SELECT and not for UPDATE — which is the signature of
    **row-level security with no UPDATE policy**.

    The two failures need different fixes and look nothing alike:

    * missing `GRANT` → PostgREST rejects outright, 401/403
    * RLS with no UPDATE policy → **HTTP 200, zero rows, no error anywhere**

    The second is the quiet one, and quiet is what made the original bug take three attempts to pin down.
    """
    import requests

    from src.web_streamlit import user_store

    class Found:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return [{"email": "a@x.ie"}]

    class UpdatedNothing:
        status_code = 200

        def json(self):
            return []                                # 200 OK, and not one row touched

    monkeypatch.setattr(user_store, "_endpoint", lambda: ("https://x/beta_users", "k"))
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Found())
    monkeypatch.setattr(requests, "patch", lambda *a, **kw: UpdatedNothing())

    out = user_store.touch_last_seen("a@x.ie")
    assert "row-level security" in out and "UPDATE policy" in out
    assert "column" not in out, "the column exists — saying otherwise sent the operator hunting the wrong thing"
