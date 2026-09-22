/// The Dart models parse the **real** committed responses (ADR-221).
///
/// ⭐⭐ **This is the half that makes hand-written models defensible.** `tests/test_api_contract.py` guards
/// the samples against the server drifting; this guards the models against the samples. Neither alone is
/// enough: the Python test would stay green while a Dart model read the wrong key, and a Dart test against
/// a hand-made fixture would stay green while the server changed underneath it.
///
/// ⚠️ **Fed from `../spikes/018-flutter-read-slice/api-samples/`, never from a fixture written here.** A test that builds its own input
/// is testing the test — ask *"if the server changed, would this fail?"* It would, because the samples are
/// regenerated from the live service and shape-checked in CI.
library;

import 'dart:convert';
import 'dart:io';

import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> sample(String name) {
  final file = File('../spikes/018-flutter-read-slice/api-samples/$name.json');
  if (!file.existsSync()) {
    throw StateError('missing ${file.absolute.path} — run regenerate_samples.py');
  }
  return jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
}

void main() {
  _myTeamTests();
  _unreachableTests();
  group('analysis', () {
    late SquadAnalysis answer;
    setUp(() => answer = SquadAnalysis.fromJson(sample('analysis')));

    test('parses a whole squad', () {
      expect(answer.xi, hasLength(11));
      expect(answer.bench, hasLength(4));
      expect(answer.projectedXp, greaterThan(0));
      expect(answer.gameweeks, hasLength(answer.horizon));
    });

    test('gameweek keys survive as integers, in order', () {
      // ⚠️ The wire carries them as strings. Sorted as text, "10" precedes "6" — so a prefix sum over the
      // next two gameweeks would answer for the wrong two.
      final weeks = answer.xi.first.byGameweek.keys.toList()..sort();
      expect(weeks, equals(answer.gameweeks));
      expect(weeks, equals(List<int>.from(weeks)..sort()));
    });

    test('an unrounded per-gameweek sum is available to the client', () {
      final player = answer.xi.first;
      final total = player.byGameweek.values.fold<double>(0, (a, b) => a + b);
      expect(total, closeTo(player.xp, 0.05));
    });

    test('a player carries availability as three separate facts', () {
      // ⭐ status, chance and `leaving` are not derivable from one another — ADR-206 priced every doubt at
      // zero by reading a flag as a verdict, and ADR-155 found FPL reporting an agreed transfer as `a`.
      final player = answer.xi.first;
      expect(player.status, isNotEmpty);
      expect(player.minutesWeight, inInclusiveRange(0, 1));
      expect(player.isLeaving, isFalse);
    });
  });

  group('transfers', () {
    late TransfersAnswer answer;
    setUp(() => answer = TransfersAnswer.fromJson(sample('transfers')));

    test('parses the ranked moves', () {
      expect(answer.moves, isNotEmpty);
      expect(answer.moves.first.incoming.name, isNotEmpty);
      expect(answer.moves.first.out.name, isNotEmpty);
    });

    test('says whether the gains add up', () {
      // ⭐ At count 1 these are alternatives; adding two of them double-counts the same bank.
      expect(answer.coordinated, equals(answer.count > 1));
    });

    test('names the wider window a near-tie was broken on', () {
      // ADR-209: at horizon 1 there must be a longer view; at 5 the ranking already is it.
      expect(answer.longerWindow, answer.horizon < 5 ? isNotNull : isNull);
    });
  });

  group('captain', () {
    late CaptainAnswer answer;
    setUp(() => answer = CaptainAnswer.fromJson(sample('captain')));

    test('ranks candidates for a single gameweek', () {
      expect(answer.gameweek, isNotNull);
      expect(answer.picks, isNotEmpty);
      final xps = answer.picks.map((p) => p.xp).toList();
      expect(xps, equals(List<double>.from(xps)..sort((a, b) => b.compareTo(a))));
    });

    test('a doubtful pick is flagged, not dropped', () {
      for (final pick in answer.picks) {
        expect(pick.doubtful, isA<bool>());
        expect(pick.player.status, isNotEmpty);
        expect(pick.xp, greaterThan(0));
      }
    });
  });

  group('route', () {
    late RouteAnswer answer;
    setUp(() => answer = RouteAnswer.fromJson(sample('route')));

    test('names the target and answers the question either way', () {
      expect(answer.target.name, isNotEmpty);
      // ⭐ A blocked route is information. Silence would not be.
      expect(answer.routes.isNotEmpty || answer.blocked.isNotEmpty, isTrue);
    });

    test('an unaffordable target reports how far short', () {
      if (!answer.isAffordable) {
        expect(answer.shortfall, isNotNull);
        expect(answer.shortfall, greaterThan(0));
      }
    });
  });

  group('build', () {
    late BuildAnswer answer;
    setUp(() => answer = BuildAnswer.fromJson(sample('build')));

    test('parses a legal fifteen within budget', () {
      expect(answer.isOptimal, isTrue);
      expect(answer.selected, hasLength(15));
      expect(answer.totalCost, lessThanOrEqualTo(answer.budget));
    });

    test('the squad has the FPL position split', () {
      final counts = <String, int>{};
      for (final p in answer.selected) {
        counts[p.position] = (counts[p.position] ?? 0) + 1;
      }
      expect(counts, equals({'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}));
    });

    test('the solver status is carried, not swallowed', () {
      // ⚠️ A client that ignored this renders an empty pitch with no reason when the answer is Infeasible.
      expect(answer.status, isNotEmpty);
    });
  });
}

// ---- my-team: the landing pitch ----------------------------------------------------------

void _myTeamTests() {
  group('my-team', () {
    late MyTeam team;
    setUp(() => team = MyTeam.fromJson(sample('my-team')));

    test('parses everything the pitch draws', () {
      expect(team.squadName, isNotEmpty);
      expect(team.gameweek, isNotNull);
      expect(team.deadlineLabel, isNotEmpty);
      expect(team.captainId, isNotNull);
      expect(team.analysis.xi, hasLength(11));
      expect(team.kits, isNotEmpty);
      expect(team.fixtures, isNotEmpty);
    });

    test('every XI player has a kit and a fixture', () {
      // ⚠️ The kit is keyed by club, so a player whose club is missing gets an empty string and a placeholder
      // shirt — never a crash on the screen a manager checks most.
      for (final p in team.analysis.xi) {
        expect(team.kitFor(p), isNotEmpty, reason: '${p.name} (${p.team}) has no kit');
        expect(team.fixtureFor(p), isNotNull, reason: '${p.name} has no fixture');
      }
    });

    test('a keeper gets the keeper kit', () {
      final keeper = team.analysis.xi.firstWhere((p) => p.position == 'GK');
      final outfield = team.analysis.xi.firstWhere((p) => p.position != 'GK');
      expect(team.kitFor(keeper), contains('_1'));
      expect(team.kitFor(keeper), isNot(equals(team.kitFor(outfield))));
    });

    test('the bench comes back in the order FPL will substitute', () {
      // ⭐ Not the order it arrived in: the first sub on is the one FPL brings on first.
      final ordered = team.orderedBench;
      expect(ordered, hasLength(team.analysis.bench.length));
      expect(ordered.map((p) => p.id).toSet(),
          equals(team.analysis.bench.map((p) => p.id).toSet()));
      final first = team.benchRoles['1st'];
      if (first != null) expect(ordered.first.id, equals(first));
    });

    test('the armbands are the manager\'s, not the engine\'s pick', () {
      // ⚠️ `analysis.topPick` is the recommendation; `captainId` is what is actually set. Rendering one as
      // the other tells a manager what they did wrong while pretending it is what they did.
      expect(team.captainId, isNot(equals(-1)));
      final ids = [...team.analysis.xi, ...team.analysis.bench].map((p) => p.id);
      expect(ids, contains(team.captainId));
    });
  });
}

// ---- a dead server reads like a dead server (ADR-233) ------------------------------------

void _unreachableTests() {
  group('unreachable service', () {
    test('a refused connection becomes an actionable message', () async {
      // ⭐ Port 1 is reserved and nothing listens on it — a real refused connection rather than a stub, so
      // this exercises the same path the owner hit.
      final client = ServiceClient(baseUrl: 'http://localhost:1');
      try {
        await client.analysis([1, 2, 3]);
        fail('a refused connection must not look like an answer');
      } on ApiException catch (e) {
        expect(e.unreachable, isTrue);
        expect(e.detail, contains('not answering'));
        // ⚠️ The address AND the command. "Cannot connect" without either tells a reader only that they
        // are stuck.
        expect(e.detail, contains('localhost:1'));
        expect(e.detail, contains('uvicorn'));
        // ⭐ And no errno text — the thing this replaced.
        expect(e.detail, isNot(contains('errno')));
      } finally {
        client.close();
      }
    });

    test('friendlyError unwraps it rather than printing the object', () {
      final e = ApiException(0, 'The service is not answering.');
      expect(friendlyError(e), 'The service is not answering.');
      expect(friendlyError(e), isNot(contains('ApiException')));
    });

    test('healthy() answers false instead of throwing', () async {
      // ⚠️ A health check that throws is a health check that takes the screen down with it.
      final client = ServiceClient(baseUrl: 'http://localhost:1');
      expect(await client.healthy(), isFalse);
      client.close();
    });
  });
}
