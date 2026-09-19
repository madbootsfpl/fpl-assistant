"""The autonomous pipeline: decide, fetch, validate, publish or refuse (ADR-211, Phase 2c).

This replaces a person. A person refreshed before a deadline because they knew one was coming, noticed when a
fetch looked wrong and did not commit it, and knew they had run it. Those three judgements are now `cadence`,
`validate` and `data_status` — and the middle one is the one with teeth, because ⭐ **locally the blast radius
of a bad payload is one laptop; server-side it is every user at once.**
"""

from datetime import UTC, datetime, timedelta

import pytest

from src import ingest, pipeline
from src.ingest import PayloadRejected, validate
from src.models import Fixture, Player, Team
from src.storage import Storage


def _team(i):
    return Team(id=i, name=f"Team {i}", short_name=f"T{i:02d}", strength_overall_home=3,
                strength_overall_away=3, code=i)


def _player(i, price=5.0):
    return Player(id=i, first_name="A", second_name=f"B{i}", web_name=f"P{i}", team_id=1,
                  position="MID", price=price, total_points=10)


def _fixture(i, event=5, kickoff="2026-09-18T19:00:00Z", finished=False):
    return Fixture(id=i, event=event, team_h=1, team_a=2, team_h_difficulty=3,
                   team_a_difficulty=3, finished=finished, kickoff_time=kickoff)


def _good_payload(n_players=650):
    return ([_player(i) for i in range(1, n_players + 1)],
            [_team(i) for i in range(1, 21)],
            [_fixture(i) for i in range(1, 11)])


# ── validate ──────────────────────────────────────────────────────────────────────────────────────────────

def test_a_good_payload_passes():
    players, teams, fixtures = _good_payload()
    assert validate(players, teams, fixtures, previous_players=655) == []


@pytest.mark.parametrize("mangle, expected", [
    (lambda p, t, f: ([], t, f),                          "players"),
    (lambda p, t, f: (p[:100], t, f),                     "players"),
    (lambda p, t, f: (p, t[:18], f),                      "teams"),
    (lambda p, t, f: (p, t, []),                          "fixtures"),
    (lambda p, t, f: ([_player(i, price=0.0) for i in range(1, 651)], t, f), "price"),
])
def test_each_shape_of_broken_payload_is_named(mangle, expected):
    """⭐ The reason is returned, not just a boolean — an unattended pipeline has to be able to say *what* was
    wrong, because nobody watched it happen."""
    reasons = validate(*mangle(*_good_payload()), previous_players=650)
    assert reasons and any(expected in r for r in reasons), reasons


def test_a_collapse_is_caught_only_when_there_is_a_baseline_to_compare_against():
    """⚠️ A first run has no previous count, and inventing a baseline would either block the bootstrap or make
    the check meaningless. `None` skips this one comparison and nothing else."""
    players, teams, fixtures = _good_payload(n_players=400)
    assert any("collapsed" in r for r in validate(players, teams, fixtures, previous_players=650))
    assert validate(players, teams, fixtures, previous_players=None) == []


def test_the_bounds_are_loose_on_purpose():
    """⭐ *A smoke alarm, not a thermostat.* A January window really does add and remove players, and a check
    that fired on one would block good data — which is worse than storing slightly odd data. So an ordinary
    window-sized change must pass."""
    players, teams, fixtures = _good_payload(n_players=620)
    assert validate(players, teams, fixtures, previous_players=700) == []


# ── the refusal, end to end ───────────────────────────────────────────────────────────────────────────────

class _FakeClient:
    """An FPL client returning whatever payload a test hands it."""

    def __init__(self, players, teams, fixtures):
        self._data = {"teams": [{"id": t.id, "name": t.name, "short_name": t.short_name, "code": t.code,
                                 "strength_overall_home": 3, "strength_overall_away": 3} for t in teams],
                      "elements": [{"id": p.id, "first_name": p.first_name, "second_name": p.second_name,
                                    "web_name": p.web_name, "team": p.team_id, "element_type": 3,
                                    "now_cost": int(p.price * 10), "total_points": p.total_points}
                                   for p in players]}
        self._fixtures = [{"id": f.id, "event": f.event, "team_h": f.team_h, "team_a": f.team_a,
                           "team_h_difficulty": f.team_h_difficulty, "team_a_difficulty": f.team_a_difficulty,
                           "finished": f.finished, "kickoff_time": f.kickoff_time} for f in fixtures]

    def get_bootstrap_static(self):
        return self._data

    def get_fixtures(self):
        return self._fixtures


def test_a_deliberately_broken_payload_is_REFUSED_and_nothing_is_written(tmp_path):
    """⭐⭐ **Phase 2c's exit criterion.** Not "validation returns a list" — that the write never happens.

    A good fetch is published first so there is something to lose, then FPL 'returns' three players. The last
    good data must still be there afterwards, unchanged, because ⭐ *a pipeline that cannot decline will
    eventually publish nonsense to everyone simultaneously.*
    """
    store = Storage(str(tmp_path / "p.db"))
    try:
        good = _good_payload()
        ingest.refresh(store, client=_FakeClient(*good), elo_client=None, now="2026-09-18T10:00:00+00:00")
        assert store.count_players() == 650

        broken = ([_player(i) for i in range(1, 4)], good[1], good[2])
        with pytest.raises(PayloadRejected) as rejected:
            ingest.refresh(store, client=_FakeClient(*broken), elo_client=None,
                           now="2026-09-18T11:00:00+00:00")

        assert "3 players" in str(rejected.value)
        assert store.count_players() == 650, "the last good data must still stand"
    finally:
        store.close()


def test_a_refusal_records_the_attempt_WITHOUT_moving_the_published_stamp(tmp_path):
    """⭐ The distinction `data_status` exists for: a dead pipeline and a quiet one must not look alike.
    `attempted_at` moves on the refusal; `refreshed_at` does not."""
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    try:
        good = _good_payload()
        ok = pipeline.run(store, now=datetime(2026, 9, 18, 10, tzinfo=UTC),
                          client=_FakeClient(*good), elo_client=None, force=True)
        assert ok["ok"] is True
        published = store.data_status()["refreshed_at"]

        broken = ([_player(i) for i in range(1, 4)], good[1], good[2])
        out = pipeline.run(store, now=datetime(2026, 9, 18, 11, tzinfo=UTC),
                           client=_FakeClient(*broken), elo_client=None, force=True)

        assert out["ran"] and out["ok"] is False, "a refusal is a run that happened and declined"
        row = store.data_status()
        assert row["refreshed_at"] == published, "the published stamp must NOT move on a refusal"
        assert row["attempted_at"] != published, "but the attempt must be recorded"
        assert not row["ok"] and "rejected" in row["note"]
    finally:
        store.close()


def test_run_never_raises_on_a_bad_payload(tmp_path):
    """⭐ An unattended job that dies on a bad afternoon tells nobody anything; one that records a refusal can
    be looked at on Monday. The CLI therefore exits 0 and the scheduler stays quiet."""
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    try:
        broken = ([_player(i) for i in range(1, 4)], [_team(i) for i in range(1, 21)], [_fixture(1)])
        out = pipeline.run(store, now=datetime(2026, 9, 18, 11, tzinfo=UTC),
                           client=_FakeClient(*broken), elo_client=None, force=True)
        assert out["ok"] is False
        assert "REFUSED" in pipeline.describe(out)
    finally:
        store.close()


# ── cadence ───────────────────────────────────────────────────────────────────────────────────────────────

def _rows(fixtures):
    return [{"event": f.event, "kickoff_time": f.kickoff_time, "finished": f.finished} for f in fixtures]


def test_a_match_in_play_gets_the_shortest_interval():
    now = datetime(2026, 9, 18, 20, 0, tzinfo=UTC)          # 1h after a 19:00 kick-off
    interval, why = pipeline.cadence(_rows([_fixture(1, kickoff="2026-09-18T19:00:00Z")]), now)
    assert interval == pipeline.INTERVAL_LIVE and "in play" in why


def test_the_hour_before_a_deadline_is_its_own_interval():
    """⭐ Because ADR-210's transfer counters reset at that deadline and the reading before it cannot be
    recovered afterwards — four chances in the last hour is what makes cron's drift survivable."""
    now = datetime(2026, 9, 18, 17, 0, tzinfo=UTC)          # kickoff 19:00 → deadline 17:30
    interval, why = pipeline.cadence(_rows([_fixture(1, kickoff="2026-09-18T19:00:00Z")]), now)
    assert interval == pipeline.INTERVAL_PRE_DEADLINE and "deadline" in why


def test_overnight_is_quiet_and_daytime_is_not():
    fixtures = _rows([_fixture(1, kickoff="2026-10-10T11:30:00Z")])
    assert pipeline.cadence(fixtures, datetime(2026, 9, 20, 3, tzinfo=UTC))[0] == pipeline.INTERVAL_QUIET
    assert pipeline.cadence(fixtures, datetime(2026, 9, 20, 14, tzinfo=UTC))[0] == pipeline.INTERVAL_NORMAL


def test_an_empty_database_is_always_due_because_it_cannot_derive_a_cadence():
    due, why = pipeline.refresh_due([], datetime(2026, 9, 18, 3, tzinfo=UTC), last_attempt=None)
    assert due and "bootstrap" in why


def test_a_refresh_inside_the_interval_is_declined_without_touching_fpl():
    """The early exit is the point: a tick that has nothing to do should cost seconds, not an FPL request."""
    now = datetime(2026, 9, 20, 14, tzinfo=UTC)
    fixtures = _rows([_fixture(1, kickoff="2026-10-10T11:30:00Z")])
    assert not pipeline.refresh_due(fixtures, now, (now - timedelta(minutes=5)).isoformat())[0]
    assert pipeline.refresh_due(fixtures, now, (now - timedelta(hours=2)).isoformat())[0]


def test_an_unparseable_last_attempt_is_treated_as_no_attempt(tmp_path):
    """⚠️ A corrupt stamp must not wedge the pipeline shut forever — the safe direction here is to run."""
    fixtures = _rows([_fixture(1, kickoff="2026-10-10T11:30:00Z")])
    due, _ = pipeline.refresh_due(fixtures, datetime(2026, 9, 20, 14, tzinfo=UTC), last_attempt="not a date")
    assert due


# ── the scheduled job itself ──────────────────────────────────────────────────────────────────────────────

def test_the_workflow_runs_a_command_the_cli_actually_accepts():
    """⚠️ Written after shipping `--no-headlines` in the workflow for a flag that does not exist — the YAML
    was valid, the command was not, and nothing would have failed until the first scheduled tick.

    ⭐ *A workflow file is code that no test runs by default*, so this parses the command out of the YAML and
    puts it through the real argument parser."""
    import shlex
    from pathlib import Path

    import yaml

    from src.cli import build_parser

    workflow = yaml.safe_load((Path(__file__).resolve().parents[1]
                               / ".github/workflows/data.yml").read_text())
    steps = workflow["jobs"]["refresh"]["steps"]
    command = next(s["run"] for s in steps if s.get("name") == "Tick")
    # Strip the GitHub expression that injects --force; both branches are exercised below.
    line = command.strip().replace("${{ inputs.force && '--force' || '' }}", "").strip()
    args = shlex.split(line)[2:]                      # drop "python app.py"
    for variant in (args, args + ["--force"]):
        parsed = build_parser().parse_args(variant)
        assert parsed.handler.__name__ == "cmd_pipeline"


def test_headlines_are_absent_from_the_scheduled_path_by_construction():
    """⭐ The ADR-211 gate kept headline extraction manual because it needs a local model and the runner has
    none. That is worth pinning as a property rather than a flag: `pipeline.run` simply never reaches it, so
    there is nothing to remember to pass."""
    import inspect

    assert "enrich_headlines" not in inspect.getsource(pipeline)
    assert "enrich_headlines" not in inspect.getsource(ingest.refresh)


def test_a_successful_refresh_CLEARS_the_previous_failure_note(tmp_path):
    """⚠️ Found by writing the backfill, not by a failing test: making `note` COALESCE — so the backfill could
    write its own stamps without clobbering the refresh's verdict — quietly stopped a healthy run from
    clearing a stale failure reason. The app would have gone on showing yesterday's refusal.

    ⭐ *A field that is cleared by writing None cannot be merged with COALESCE.* The note follows the verdict:
    a write carrying `ok` owns it, a write without one leaves it alone.
    """
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    try:
        good = _good_payload()
        broken = ([_player(i) for i in range(1, 4)], good[1], good[2])
        pipeline.run(store, now=datetime(2026, 9, 18, 10, tzinfo=UTC),
                     client=_FakeClient(*broken), elo_client=None, force=True)
        assert store.data_status()["note"], "the refusal recorded a reason"

        pipeline.run(store, now=datetime(2026, 9, 18, 11, tzinfo=UTC),
                     client=_FakeClient(*good), elo_client=None, force=True)
        row = store.data_status()
        assert row["ok"] and row["note"] is None, "a healthy run must clear the stale reason"
    finally:
        store.close()


def test_a_backfill_stamp_does_not_disturb_the_refresh_verdict(tmp_path):
    """The other half of the same rule: the backfill is a different job on a different clock, so writing its
    stamp must not make a healthy refresh look broken — or a broken one look healthy."""
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    try:
        # ⚠️ **A live refusal, not a clean slate.** The first version of this test set `note=None` before
        # backfilling, so a mutation that let the backfill clobber the note with None was invisible — the
        # value it destroyed was already None. ⭐ *A guard only tests the case its fixture can reach.*
        store.set_data_status(refreshed_at="2026-09-18T10:00:00Z", attempted_at="2026-09-18T11:00:00Z",
                              ok=False, note="rejected: player count collapsed")
        store.set_data_status(backfilled_at="2026-09-18T12:00:00Z", backfilled_event=5)
        row = store.data_status()
        assert row["ok"] == 0 and row["note"] == "rejected: player count collapsed", \
            "the backfill must not erase the core refresh's verdict or its reason"
        assert row["refreshed_at"] == "2026-09-18T10:00:00Z"
        assert row["backfilled_at"] == "2026-09-18T12:00:00Z" and row["backfilled_event"] == 5
    finally:
        store.close()


# ── the per-gameweek backfill ─────────────────────────────────────────────────────────────────────────────

def _gw_row(round_no, *, scored=True):
    """A per-GW history row as `get_gw_history_by_code` returns it — a **row**, not a `PlayerGameweek`.

    ⚠️ Written with the dataclass first, which `completed_gameweeks` cannot index (`TypeError`), because the
    real path never sees one. ⭐ *A fixture that models less than reality will confirm a broken mechanism* —
    here it would have failed loudly, but the same slip the other way round is how a guard passes on a shape
    production never produces.
    """
    return {"element_code": 1, "round": round_no, "minutes": 90 if scored else 0,
            "total_points": 5 if scored else 0, "fixture": round_no * 10,
            "kickoff_time": f"2026-09-{round_no:02d}T14:00:00Z",
            "team_h_score": 1 if scored else None, "team_a_score": 0 if scored else None}


def test_a_completed_gameweek_with_no_history_is_due():
    fixtures = [{"event": 1, "finished": True}, {"event": 2, "finished": True}]
    due, why, rounds = pipeline.backfill_due(fixtures, {})
    assert due and rounds == {1, 2} and "GW[1, 2]" in why


def test_a_gameweek_still_in_progress_is_not_due():
    """⭐ *All* of a gameweek's fixtures must have finished. A Saturday 3pm round with a Monday night game
    still to come is not a gameweek whose history is worth fetching."""
    fixtures = [{"event": 5, "finished": True}, {"event": 5, "finished": False}]
    due, _, rounds = pipeline.backfill_due(fixtures, {})
    assert not due and rounds == set()


def test_done_is_asked_with_the_ANALYTICS_definition_not_a_second_one(tmp_path):
    """⭐⭐ The trap this avoids. FPL writes a player's per-gameweek row when the fixture is merely
    **scheduled** (ADR-125/129), so a pipeline asking *"are there rows for round N?"* would find them,
    conclude the work was done, and leave the analytics with a gameweek they cannot see.

    `minutes.completed_gameweeks` — what `in_season_share`, the backtest and the availability log all use —
    counts a round only when its rows carry a **scoreline**. ⭐ *The pipeline's "done" has to be the
    consumer's "have".*
    """
    fixtures = [{"event": 3, "finished": True}]
    scheduled_only = {1: [_gw_row(3, scored=False)]}
    due, _, rounds = pipeline.backfill_due(fixtures, scheduled_only)
    assert due and rounds == {3}, "rows exist, but none carry a scoreline — the work is NOT done"

    played = {1: [_gw_row(3)]}
    assert pipeline.backfill_due(fixtures, played)[0] is False


def test_the_backfill_records_its_own_stamp_and_leaves_the_refresh_verdict_alone(tmp_path):
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    calls = {"n": 0}

    def fake_backfill(_store, **kwargs):
        calls["n"] += 1
        return (659, 0, 120, 0)

    try:
        store.set_data_status(refreshed_at="2026-09-18T10:00:00Z", attempted_at="2026-09-18T10:00:00Z",
                              ok=True, note=None)
        import src.pipeline as pipeline_module
        original = pipeline_module.ingest.backfill_history
        pipeline_module.ingest.backfill_history = fake_backfill
        try:
            out = pipeline.run_backfill(store, now=datetime(2026, 9, 18, 12, tzinfo=UTC), force=True)
        finally:
            pipeline_module.ingest.backfill_history = original

        assert calls["n"] == 1 and out["ran"] and out["ok"]
        row = store.data_status()
        assert row["backfilled_at"].startswith("2026-09-18T12")
        assert row["ok"] and row["refreshed_at"] == "2026-09-18T10:00:00Z", \
            "a backfill must not disturb the core refresh's verdict"
    finally:
        store.close()


def test_the_backfill_does_not_walk_659_players_when_nothing_is_missing(tmp_path):
    """⚠️ The gate is the whole point — this is ~659 throttled requests. A job that ran it on a clock rather
    than on need would hammer FPL hourly for nothing."""
    store = Storage(str(tmp_path / "p.db"), ensure_schema=True)
    called = {"n": 0}

    def fake_backfill(_store, **kwargs):
        called["n"] += 1
        return (659, 0, 0, 0)

    try:
        import src.pipeline as pipeline_module
        original = pipeline_module.ingest.backfill_history
        pipeline_module.ingest.backfill_history = fake_backfill
        try:
            out = pipeline.run_backfill(store, now=datetime(2026, 9, 18, 12, tzinfo=UTC))
        finally:
            pipeline_module.ingest.backfill_history = original
        assert not out["ran"] and called["n"] == 0
    finally:
        store.close()


def test_the_backfill_workflow_runs_a_command_the_cli_accepts():
    """The same guard as the refresh workflow, for the same reason: ⭐ *a workflow file is code no test runs
    by default*, and the last one shipped a flag that did not exist."""
    import shlex
    from pathlib import Path

    import yaml

    from src.cli import build_parser

    workflow = yaml.safe_load((Path(__file__).resolve().parents[1]
                               / ".github/workflows/backfill.yml").read_text())
    step = next(s for s in workflow["jobs"]["backfill"]["steps"]
                if s.get("name", "").startswith("Backfill"))
    line = step["run"].strip().replace("${{ inputs.force && '--force' || '' }}", "").strip()
    for variant in (shlex.split(line)[2:], shlex.split(line)[2:] + ["--force"]):
        parsed = build_parser().parse_args(variant)
        assert parsed.handler.__name__ == "cmd_pipeline" and parsed.backfill


# ── 2e: the one manual input ──────────────────────────────────────────────────────────────────────────────

def test_a_local_refresh_carries_headlines_into_whatever_database_it_is_pointed_at():
    """⭐ 2e's whole mechanism, and it is a property rather than a feature: `cmd_refresh` opens **one** store
    and hands that same store to `enrich_headlines`.

    So `FPL_DATABASE_URL=… app.py refresh` on a machine with Ollama writes players *and* headlines straight
    into Postgres — there is no separate push step to remember, and no second code path to keep in step.

    ⚠️ Pinned because it would be easy to 'tidy' the headline call onto its own `Storage()`, which would
    silently keep writing events to the local SQLite cache while the app read Postgres — and the symptom
    would be *no news*, which looks exactly like *no news*.
    """
    import inspect

    from src import cli
    source = inspect.getsource(cli.cmd_refresh)
    assert "enrich_headlines(store)" in source, "headlines must use the same store as the player data"
    assert source.count("Storage(") == 1, "a second store here would split the destination in two"


def test_the_scheduled_pipeline_still_cannot_reach_the_model_path():
    """The gate decided headlines stay manual (option b). That holds by construction — `pipeline.run` never
    calls `enrich_headlines` — so there is no flag to forget and no way for the runner, which has no model,
    to start failing on one."""
    import inspect

    assert "enrich_headlines" not in inspect.getsource(pipeline)


# ── 2f: the app must not describe a deploy route it no longer uses ────────────────────────────────────────

def test_the_sidebar_does_not_claim_a_redeploy_is_needed_while_reading_postgres(monkeypatch):
    """⚠️ **A sentence the app says about itself while behaving differently.** Before the cutover *"updates
    when the app is redeployed"* is true; after it the pipeline refreshes the database through the day and
    the same caption is simply false.

    ⭐ *Retiring a path means retiring what the product says about it* — the failure ADR-184 was written
    about, where a claim outlived its mechanism on six surfaces for a fortnight.
    """
    from src import config as config_module
    from src.web_streamlit import status as status_module

    captions = []

    class _Sidebar:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(status_module.st, "sidebar", _Sidebar())
    monkeypatch.setattr(status_module.st, "caption", lambda msg, **k: captions.append(msg))
    monkeypatch.setattr(status_module.st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(status_module.st, "button", lambda *a, **k: False)
    monkeypatch.setattr(status_module, "_player_count", lambda: 659)
    monkeypatch.setattr(status_module, "is_local", lambda: False)
    monkeypatch.setattr(status_module, "fallback_reason", lambda: None)
    monkeypatch.setattr(status_module, "_data_as_of", lambda: "2026-09-19")

    monkeypatch.setattr(config_module, "DATABASE_URL", None)
    status_module.render_data_status()
    assert any("redeployed" in c for c in captions), "before the cutover the snapshot line is correct"

    captions.clear()
    monkeypatch.setattr(config_module, "DATABASE_URL", "postgresql://u@h/db")
    status_module.render_data_status()
    assert not any("redeployed" in c for c in captions), "after it, that sentence is false"
    assert any("automatically" in c for c in captions)


def test_nothing_in_the_app_still_calls_reseed_the_way_to_update_the_deployed_app():
    """⭐ ADR-184's discipline: when a claim is retired, **grep for it and make the grep the test**.

    `reseed` keeps working and keeps its place — it maintains the fallback snapshot. What it stops being,
    once the pipeline is on, is *how data reaches users*. Any copy still saying otherwise would send the
    owner down a route that no longer does the thing.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in list((root / "src").rglob("*.py")) + [root / "docs/DEPLOY.md"]:
        if "__pycache__" in path.parts:
            continue
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            # ⚠️ **Do not require "reseed" on the same line.** The first version did, and missed the exact
            # regression it exists for: the `help=` string on `p_reseed` never contains the word — the
            # variable name does. ⭐ *Sweep for the CLAIM, not for a word you expect to sit beside it*
            # (ADR-184, and the second time in this ADR alone).
            if "updates the deployed app" in line.lower():
                offenders.append(f"{path.relative_to(root)}:{i}: {line.strip()}")
    assert not offenders, (
        "reseed maintains the fallback once the pipeline is on; it is not the deploy route:\n"
        + "\n".join(offenders))
