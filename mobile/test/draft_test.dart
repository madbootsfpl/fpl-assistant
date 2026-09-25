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
}) => Draft(
  managerId: managerId,
  gameweek: gameweek,
  basePlayerIds: base,
  playerIds: players ?? const [1, 2, 3, 4, 99],
  benchIds: const [99],
  savedAt: DateTime(2026, 9, 22),
);

void main() {
  _selfConsistency();
  group('staleness', () {
    test('a plan for the same manager, week and squad still applies', () {
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: 6,
          fplPlayerIds: [1, 2, 3, 4, 5],
        ),
        DraftStaleness.fresh,
      );
    });

    test('a squad that changed underneath it is the move already made', () {
      // ⭐⭐ The case this whole design exists for: plan on Friday, make the transfer for real on Saturday,
      // reopen on Sunday. A snapshot would show Friday's plan as your team.
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: 6,
          fplPlayerIds: [1, 2, 3, 4, 99],
        ),
        DraftStaleness.squadChanged,
      );
    });

    test('a plan for a gameweek already played is meaningless', () {
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: 7,
          fplPlayerIds: [1, 2, 3, 4, 5],
        ),
        DraftStaleness.gameweekPassed,
      );
    });

    test('another manager\'s plan is not yours', () {
      expect(
        draftOf().checkAgainst(
          managerId: 123,
          gameweek: 6,
          fplPlayerIds: [1, 2, 3, 4, 5],
        ),
        DraftStaleness.otherManager,
      );
    });

    test('reordering the bench is not a squad change', () {
      // ⚠️ FPL returns picks in its own order, and that order moves when a manager reorders the bench.
      // Treating order as identity would throw away a perfectly good plan for no reason.
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: 6,
          fplPlayerIds: [5, 3, 1, 4, 2],
        ),
        DraftStaleness.fresh,
      );
    });

    test('an unknown gameweek does not invalidate a plan', () {
      // ⭐ Absent is not "different". Refusing to restore because a field was missing would punish the
      // manager for the server's silence.
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: null,
          fplPlayerIds: [1, 2, 3, 4, 5],
        ),
        DraftStaleness.fresh,
      );
    });

    test('a squad of the same size with a different player is caught', () {
      // ⚠️ Length alone is not identity — fifteen players are always fifteen players.
      expect(
        draftOf().checkAgainst(
          managerId: 2885974,
          gameweek: 6,
          fplPlayerIds: [1, 2, 3, 4, 77],
        ),
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

/// A plan that contradicts itself (ADR-291).
///
/// ⚠️⚠️ **The owner's phone reached `draft bench ids not in the draft squad: [496]` and could not get
/// past it.** The server refused the request, the app showed the refusal, and the saved plan that caused
/// it was re-sent on every launch — ⭐ *a saved plan that cannot be sent and cannot be cleared is an app
/// that will not open.*
void _selfConsistency() {
  final at = DateTime(2026, 9, 25);
  const squad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 496];
  const bench = [12, 13, 14, 496];

  group('a second transfer', () {
    test('does not resurrect the player the first one sold', () {
      // ⭐⭐ The exact shape of the owner's bug: 496 is a bench keeper, transferred out first.
      final first = Draft.swap(
        existing: null,
        managerId: 1,
        gameweek: 6,
        basePlayerIds: squad,
        benchIds: bench,
        outId: 496,
        inId: 900,
        savedAt: at,
      );
      final second = Draft.swap(
        // ⚠️ The team's own bench, which is what the screen passes — *and the reason the bug existed*:
        // the XI came from the draft and the bench came from here.
        existing: first,
        managerId: 1,
        gameweek: 6,
        basePlayerIds: squad,
        benchIds: bench,
        outId: 5,
        inId: 901,
        savedAt: at,
      );

      expect(second.benchIds, isNot(contains(496)));
      expect(
        second.benchIds.toSet().difference(second.playerIds.toSet()),
        isEmpty,
      );
    });

    test('keeps every bench id inside its own squad, over four transfers', () {
      // ⭐ Not just the second. *A bug that needs two steps to appear is a bug that gets fixed for two
      // steps*, so this walks far enough to catch a fix that only repairs the first repeat.
      var draft = Draft.swap(
        existing: null,
        managerId: 1,
        gameweek: 6,
        basePlayerIds: squad,
        benchIds: bench,
        outId: 496,
        inId: 900,
        savedAt: at,
      );
      for (final (out, into) in const [(12, 901), (1, 902), (900, 903)]) {
        draft = Draft.swap(
          existing: draft,
          managerId: 1,
          gameweek: 6,
          basePlayerIds: squad,
          benchIds: bench,
          outId: out,
          inId: into,
          savedAt: at,
        );
        expect(
          draft.benchIds.toSet().difference(draft.playerIds.toSet()),
          isEmpty,
          reason: 'after selling $out the bench left the squad',
        );
      }
      expect(
        draft.benchIds.length,
        bench.length,
        reason: 'the bench changed size',
      );
    });
  });

  group('a draft that already contradicts itself', () {
    Draft broken() => Draft(
      managerId: 1,
      gameweek: 6,
      basePlayerIds: squad,
      playerIds: const [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 900],
      benchIds: bench, // ⚠️ still holds 496, which the squad no longer has
      savedAt: at,
    );

    test('is dropped rather than sent', () {
      // ⭐⭐ Checked even though the cause is fixed: *the fix stops new ones being written, and says
      // nothing about the one already on somebody's phone.*
      expect(
        broken().checkAgainst(managerId: 1, gameweek: 6, fplPlayerIds: squad),
        DraftStaleness.inconsistent,
      );
    });

    test('is dropped whoever it belongs to and whatever gameweek it is', () {
      // ⚠️ The other reasons ask whether it still applies; this asks whether it was ever sendable — so
      // it must win, or a stuck phone stays stuck until the gameweek turns.
      expect(
        broken().checkAgainst(
          managerId: 999,
          gameweek: 9,
          fplPlayerIds: const [1],
        ),
        DraftStaleness.inconsistent,
      );
    });

    test('a consistent plan is still fresh', () {
      final good = Draft.swap(
        existing: null,
        managerId: 1,
        gameweek: 6,
        basePlayerIds: squad,
        benchIds: bench,
        outId: 496,
        inId: 900,
        savedAt: at,
      );
      expect(
        good.checkAgainst(managerId: 1, gameweek: 6, fplPlayerIds: squad),
        DraftStaleness.fresh,
      );
    });
  });
}
