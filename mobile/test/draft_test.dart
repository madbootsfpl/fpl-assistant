/// A saved draft knows when it has stopped being true (ADR-225).
///
/// ⭐⭐ **This is the file that stops the app lying.** A plan restored after the world moved on is shown as
/// *your team*, and a manager acts on it — the one failure here with real consequences, since the action it
/// invites costs a transfer.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/draft.dart';

Draft draftOf({
  int managerId = 2885974,
  int gameweek = 6,
  List<int> base = const [1, 2, 3, 4, 5],
  List<int>? players,
}) =>
    Draft(
      managerId: managerId,
      gameweek: gameweek,
      basePlayerIds: base,
      playerIds: players ?? const [1, 2, 3, 4, 99],
      benchIds: const [99],
      savedAt: DateTime(2026, 9, 22),
    );

void main() {
  group('staleness', () {
    test('a plan for the same manager, week and squad still applies', () {
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: 6, fplPlayerIds: [1, 2, 3, 4, 5]),
        DraftStaleness.fresh,
      );
    });

    test('a squad that changed underneath it is the move already made', () {
      // ⭐⭐ The case this whole design exists for: plan on Friday, make the transfer for real on Saturday,
      // reopen on Sunday. A snapshot would show Friday's plan as your team.
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: 6, fplPlayerIds: [1, 2, 3, 4, 99]),
        DraftStaleness.squadChanged,
      );
    });

    test('a plan for a gameweek already played is meaningless', () {
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: 7, fplPlayerIds: [1, 2, 3, 4, 5]),
        DraftStaleness.gameweekPassed,
      );
    });

    test('another manager\'s plan is not yours', () {
      expect(
        draftOf().checkAgainst(managerId: 123, gameweek: 6, fplPlayerIds: [1, 2, 3, 4, 5]),
        DraftStaleness.otherManager,
      );
    });

    test('reordering the bench is not a squad change', () {
      // ⚠️ FPL returns picks in its own order, and that order moves when a manager reorders the bench.
      // Treating order as identity would throw away a perfectly good plan for no reason.
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: 6, fplPlayerIds: [5, 3, 1, 4, 2]),
        DraftStaleness.fresh,
      );
    });

    test('an unknown gameweek does not invalidate a plan', () {
      // ⭐ Absent is not "different". Refusing to restore because a field was missing would punish the
      // manager for the server's silence.
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: null, fplPlayerIds: [1, 2, 3, 4, 5]),
        DraftStaleness.fresh,
      );
    });

    test('a squad of the same size with a different player is caught', () {
      // ⚠️ Length alone is not identity — fifteen players are always fifteen players.
      expect(
        draftOf().checkAgainst(managerId: 2885974, gameweek: 6, fplPlayerIds: [1, 2, 3, 4, 77]),
        DraftStaleness.squadChanged,
      );
    });
  });

  group('swaps', () {
    test('are derived from the two squads, not stored', () {
      // ⭐ Two lists and a subtraction cannot disagree with each other; a stored list of swaps could drift
      // from the squad it claims to describe.
      expect(draftOf().swaps, equals([(5, 99)]));
    });

    test('an unchanged draft has none', () {
      expect(draftOf(players: const [1, 2, 3, 4, 5]).isEmpty, isTrue);
    });

    test('survive a round trip through storage', () {
      final restored = Draft.fromJson(draftOf().toJson());
      expect(restored.swaps, equals(draftOf().swaps));
      expect(restored.basePlayerIds, equals(draftOf().basePlayerIds));
      expect(restored.gameweek, equals(6));
    });
  });
}
