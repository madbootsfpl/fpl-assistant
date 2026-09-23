// Squad Lab (ADR-268) — the draft, and the diff that makes it useful.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/lab_view.dart';

BuildAnswer sample() => BuildAnswer.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/build.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

PlayerSummary p(int id, String name, {double price = 5.0}) => PlayerSummary(
  id: id,
  name: name,
  team: 'ARS',
  position: 'MID',
  price: price,
  xp: 4,
  status: 'a',
  chance: null,
  minutesWeight: 1,
  leaving: null,
  byGameweek: const {},
);

BuiltPlayer built(int id, {bool bench = false, bool forced = false}) =>
    BuiltPlayer(player: p(id, 'P$id'), bench: bench, forced: forced);

BuildAnswer drafted(List<BuiltPlayer> squad) => BuildAnswer(
  horizon: 5,
  budget: 100,
  status: 'Optimal',
  selected: squad,
  totalCost: 99,
  projectedXp: 400,
  xiXp: 320,
);

void main() {
  group('the sample the app actually asks for', () {
    test('designates an eleven and a bench', () {
      final a = sample();
      expect(a.selected, hasLength(15));
      expect(a.xi, hasLength(11));
      expect(a.bench, hasLength(4));
    });

    // ⭐⭐ The headline must be the eleven: a bench-aware draft scores LOWER on all fifteen while
    // fielding a BETTER side.
    test('the eleven is named separately from the fifteen', () {
      final a = sample();
      expect(a.xiXp, isNotNull);
      expect(a.xiXp, lessThan(a.projectedXp));
    });

    test('it comes in within budget', () {
      final a = sample();
      expect(a.totalCost, lessThanOrEqualTo(a.budget));
      expect(a.solved, isTrue);
    });
  });

  group('solved', () {
    // ⚠️⚠️ Rendering fifteen blank rows under a heading is how "your constraints cannot be met" gets
    // read as "there are no good players".
    test('an infeasible answer is not a squad', () {
      final stuck = BuildAnswer.fromJson(const {
        'horizon': 5,
        'budget': 100.0,
        'status': 'Infeasible',
        'selected': [],
        'total_cost': 0.0,
        'projected_xp': 0.0,
      });
      expect(stuck.solved, isFalse);
    });

    test('a short squad is not a squad either, whatever the status says', () {
      expect(drafted([built(1), built(2)]).solved, isFalse);
    });

    test('a full optimal fifteen is', () {
      expect(
        drafted([for (var i = 0; i < 15; i++) built(i, bench: i >= 11)]).solved,
        isTrue,
      );
    });
  });

  group('squadDiff', () {
    test('names who leaves and who arrives', () {
      final mine = [p(1, 'Keep'), p(2, 'Drop')];
      final answer = drafted([built(1), built(3)]);
      final diff = squadDiff(answer, mine);

      expect(diff.out.map((x) => x.id), [2]);
      expect(diff.in_.map((x) => x.player.id), [3]);
    });

    test('an unchanged squad has nobody on either side', () {
      final mine = [p(1, 'A'), p(2, 'B')];
      final diff = squadDiff(drafted([built(1), built(2)]), mine);
      expect(diff.out, isEmpty);
      expect(diff.in_, isEmpty);
    });

    // ⚠️ Two players can share a surname; a diff matching on text would pair the wrong two.
    test('it matches on id, not on name', () {
      final mine = [p(1, 'Silva'), p(2, 'Silva')];
      final answer = drafted([
        BuiltPlayer(player: p(2, 'Silva'), bench: false, forced: false),
      ]);
      final diff = squadDiff(answer, mine);

      expect(diff.out.map((x) => x.id), [
        1,
      ], reason: 'only the player actually dropped');
      expect(diff.in_, isEmpty, reason: 'the other Silva was already owned');
    });

    test('a kept player never appears as an arrival', () {
      final mine = [p(1, 'Kept'), p(2, 'Gone')];
      final diff = squadDiff(drafted([built(1, forced: true), built(9)]), mine);
      expect(diff.in_.map((x) => x.player.id), [9]);
      expect(diff.out.map((x) => x.id), [2]);
    });

    test('an empty draft leaves the whole squad out, rather than throwing', () {
      final diff = squadDiff(drafted(const []), [p(1, 'A')]);
      expect(diff.out, hasLength(1));
      expect(diff.in_, isEmpty);
    });
  });

  group('the mode', () {
    // ⭐ A wildcard is played for a run, not for one week — the horizon IS the mode.
    test('wildcard builds over a run', () {
      expect(LabMode.wildcard.horizon, greaterThan(1));
      expect(LabMode.wildcard.label, 'Wildcard');
    });
  });
}
