// Squad Lab: modes, build styles, editing, and what "apply" actually means (ADR-272).
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/draft.dart';
import 'package:madboots/lab_view.dart';

PlayerSummary p(
  int id,
  String name, {
  String pos = 'MID',
  double price = 5.0,
}) => PlayerSummary(
  id: id,
  name: name,
  team: 'ARS',
  position: pos,
  price: price,
  xp: 4,
  status: 'a',
  chance: null,
  minutesWeight: 1,
  leaving: null,
  byGameweek: const {},
);

BuiltPlayer built(int id, {String pos = 'MID', bool bench = false}) =>
    BuiltPlayer(
      player: p(id, 'P$id', pos: pos),
      bench: bench,
      forced: false,
    );

BuildAnswer squadOf(List<BuiltPlayer> squad) => BuildAnswer(
  horizon: 5,
  budget: 100,
  status: 'Optimal',
  selected: squad,
  totalCost: 99,
  projectedXp: 400,
  xiXp: 320,
);

/// A legal-shaped fifteen: 2 GK, 5 DEF, 5 MID, 3 FWD, four of them benched.
BuildAnswer legalFifteen() {
  final squad = <BuiltPlayer>[];
  var id = 1;
  for (final (pos, n) in const [
    ('GK', 2),
    ('DEF', 5),
    ('MID', 5),
    ('FWD', 3),
  ]) {
    for (var i = 0; i < n; i++) {
      squad.add(built(id++, pos: pos, bench: false));
    }
  }
  // bench one of each of the last four
  for (final i in [1, 6, 10, 14]) {
    squad[i] = BuiltPlayer(player: squad[i].player, bench: true, forced: false);
  }
  return squadOf(squad);
}

void main() {
  group('the modes differ in the thing that matters', () {
    // ⭐ A wildcard is played for a run; a free hit for one week — and asking the solver for a run
    // would give a different fifteen.
    test('free hit asks for one gameweek, the others for a run', () {
      expect(LabMode.freeHit.horizon, 1);
      expect(LabMode.wildcard.horizon, greaterThan(1));
      expect(LabMode.freshSeason.horizon, greaterThan(1));
    });

    test('only a new season starts from nothing owned', () {
      expect(LabMode.freshSeason.fromScratch, isTrue);
      expect(LabMode.wildcard.fromScratch, isFalse);
      expect(LabMode.freeHit.fromScratch, isFalse);
    });

    test('each mode says what it is for', () {
      for (final mode in LabMode.values) {
        expect(mode.label, isNotEmpty);
        expect(
          mode.note.length,
          greaterThan(20),
          reason: '${mode.label} has a label, not a note',
        );
      }
    });
  });

  group('build style', () {
    // ⚠️ Not a preference — two genuinely different squads.
    test('a strong XI spends less on the bench than a strong fifteen', () {
      expect(
        BuildStyle.strongXi.benchWeight,
        lessThan(BuildStyle.strongFifteen.benchWeight),
      );
    });

    test(
      'a strong fifteen values the bench fully, which is what Bench Boost asks',
      () {
        expect(BuildStyle.strongFifteen.benchWeight, 1.0);
      },
    );

    test('neither weight is out of the range the server accepts', () {
      for (final style in BuildStyle.values) {
        expect(style.benchWeight, inInclusiveRange(0, 1));
      }
    });
  });

  group('formationOf', () {
    test('reads the shape off the eleven, not the fifteen', () {
      expect(formationOf(legalFifteen()), '4-4-2');
    });

    test('an empty squad does not throw', () {
      expect(formationOf(squadOf(const [])), '0-0-0');
    });
  });

  group('squadDiff', () {
    test('names who leaves and who arrives', () {
      final diff = squadDiff(squadOf([built(1), built(3)]), [
        p(1, 'A'),
        p(2, 'B'),
      ]);
      expect(diff.out.map((x) => x.id), [2]);
      expect(diff.in_.map((x) => x.player.id), [3]);
    });

    // ⚠️ Two players can share a surname; a diff matching on text would pair the wrong two.
    test('it matches on id, not on name', () {
      final diff = squadDiff(
        squadOf([
          BuiltPlayer(player: p(2, 'Silva'), bench: false, forced: false),
        ]),
        [p(1, 'Silva'), p(2, 'Silva')],
      );
      expect(diff.out.map((x) => x.id), [1]);
      expect(diff.in_, isEmpty);
    });
  });

  group('applying a squad makes a plan, never a transfer', () {
    // ⭐⭐ The draft keeps the REAL fifteen as its base, which is how it later knows it is stale.
    test(
      'the base stays the real squad while the plan becomes the built one',
      () {
        final answer = legalFifteen();
        final draft = Draft(
          managerId: 7,
          gameweek: 6,
          basePlayerIds: const [90, 91, 92],
          playerIds: [for (final b in answer.selected) b.player.id],
          benchIds: [for (final b in answer.bench) b.player.id],
          savedAt: DateTime(2026, 9, 23),
          signalKeys: const {'news:1'},
          name: 'Wildcard plan',
        );

        expect(draft.basePlayerIds, const [90, 91, 92]);
        expect(draft.playerIds, hasLength(15));
        expect(draft.benchIds, hasLength(4));
        // ⚠️ Without this the plan cannot report what has changed since it was made (ADR-260).
        expect(draft.signalKeys, {'news:1'});
        expect(draft.name, 'Wildcard plan');
      },
    );

    test('a named plan survives a round trip through storage', () {
      final draft = Draft(
        managerId: 7,
        gameweek: 6,
        basePlayerIds: const [1],
        playerIds: const [2],
        benchIds: const [],
        savedAt: DateTime(2026, 9, 23),
        name: 'Free Hit plan',
      );
      expect(Draft.fromJson(draft.toJson()).name, 'Free Hit plan');
    });

    test('an unnamed plan is empty, never a fabricated label', () {
      final draft = Draft(
        managerId: 7,
        gameweek: 6,
        basePlayerIds: const [1],
        playerIds: const [2],
        benchIds: const [],
        savedAt: DateTime(2026, 9, 23),
      );
      expect(Draft.fromJson(draft.toJson()).name, isEmpty);
    });

    // ⚠️ An unsolved answer must never become a plan — fifteen blank rows on the pitch.
    test('an infeasible answer is not a squad to apply', () {
      expect(squadOf(const []).solved, isFalse);
      expect(legalFifteen().solved, isTrue);
    });
  });
}
