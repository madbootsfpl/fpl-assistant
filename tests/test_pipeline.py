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
