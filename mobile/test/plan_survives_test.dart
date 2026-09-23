/// A plan survives, and tells you what changed under it (ADR-260).
///
/// ⭐⭐⭐ **The owner's actual workflow**: *"people like to manipulate their teams, wait till near deadline
/// and then make the changes **if nothing else external has happened that might influence change**."*
///
/// The first half has worked since ADR-225. ⚠️ The second half is the one the app knew and never said —
/// *a plan you come back to is only safe to execute if you know what changed underneath it.*
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/draft.dart';
import 'package:shared_preferences/shared_preferences.dart';

Draft planned({
  Set<String> knew = const {},
  List<int> ids = const [1, 2, 3],
  List<int> bench = const [3],
}) => Draft(
  managerId: 7,
  gameweek: 6,
  basePlayerIds: const [1, 2, 3],
  playerIds: ids,
  benchIds: bench,
  savedAt: DateTime(2026, 9, 20, 10),
  captainId: 1,
  signalKeys: knew,
);

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('it survives', () {
    test('a plan comes back whole, days later', () async {
      // ⭐ The transfers, the bench order and the armband — the three things a manager actually changed.
      final store = DraftStore();
      await store.save(
        planned(knew: {'official:5:1'}, ids: const [1, 2, 9], bench: const [9]),
      );

      final back = (await store.load())!;
      expect(back.playerIds, const [1, 2, 9]);
      expect(back.benchIds, const [9]);
      expect(back.captainId, 1);
      expect(back.signalKeys, {'official:5:1'});
      expect(
        back.checkAgainst(managerId: 7, gameweek: 6, fplPlayerIds: const [1, 2, 3]),
        DraftStaleness.fresh,
      );
    });

    test('a plan for a gameweek that has been and gone is not offered', () {
      // ⚠️ The deadline passed; the plan is history. ⭐ *Silently showing it would be showing a team that
      // cannot be fielded.*
      expect(
        planned().checkAgainst(managerId: 7, gameweek: 7, fplPlayerIds: const [1, 2, 3]),
        DraftStaleness.gameweekPassed,
      );
    });
  });

  group('it says what changed underneath', () {
    test('nothing new is an empty answer, not a missing one', () {
      // ⭐⭐⭐ **The reassurance is the feature.** A manager who plans on Tuesday and executes on Saturday
      // wants exactly this before committing, and an app that only speaks when something *has* happened
      // leaves silence meaning two things — *nothing happened* and *nobody checked*.
      final plan = planned(knew: {'a:1', 'b:2'});
      expect(plan.since(const ['a:1', 'b:2']), isEmpty);
    });

    test('a signal that arrived after the plan is reported', () {
      final plan = planned(knew: {'a:1'});
      expect(plan.since(const ['a:1', 'exodus:9']), {'exodus:9'});
    });

    test('a signal that has since gone quiet is not reported as new', () {
      // ⚠️ It is a difference in one direction only: *what is here now that was not then.* A signal that
      // disappeared is not news about your plan.
      expect(planned(knew: {'a:1', 'b:2'}).since(const ['a:1']), isEmpty);
    });

    test('a plan saved before this existed treats everything as new', () {
      // ⚠️⚠️ **The safe direction, chosen deliberately.** An older plan has no record of what was known,
      // which reads as "nothing was known" — so every current signal looks new. ⭐ *Over-reporting a
      // change invites a second look; under-reporting one lets a plan be executed blind.*
      final old = Draft.fromJson({
        'manager_id': 7,
        'gameweek': 6,
        'base_player_ids': [1, 2, 3],
        'player_ids': [1, 2, 3],
        'bench_ids': [3],
        'saved_at': DateTime(2026, 9, 20).toIso8601String(),
      });
      expect(old.signalKeys, isEmpty);
      expect(old.since(const ['a:1', 'b:2']), {'a:1', 'b:2'});
    });
  });

  group('editing a plan does not silence it', () {
    test('a transfer carries what was known, rather than resetting it', () {
      // ⚠️⚠️ **The subtle failure this guards.** Re-reading the current signals here would mark
      // everything as seen at the moment of a transfer — ⭐ *and the warning the plan needs on its way
      // back would be silently emptied by the act of editing the plan.*
      final first = planned(knew: {'a:1'});
      final after = Draft.swap(
        existing: first,
        managerId: 7,
        gameweek: 6,
        basePlayerIds: const [1, 2, 3],
        benchIds: const [3],
        outId: 2,
        inId: 9,
        savedAt: DateTime(2026, 9, 21),
        signalKeys: const {'a:1', 'b:2', 'c:3'},
      );
      expect(after.signalKeys, {'a:1'}, reason: 'the transfer reset what the plan knew');
      expect(after.since(const ['a:1', 'b:2']), {'b:2'});
    });

    test('a substitution carries it too', () {
      final first = planned(knew: {'a:1'});
      final after = Draft.substitute(
        existing: first,
        managerId: 7,
        gameweek: 6,
        basePlayerIds: const [1, 2, 3],
        benchIds: const [3],
        a: 3,
        b: 1,
        savedAt: DateTime(2026, 9, 21),
        signalKeys: const {'a:1', 'b:2'},
      );
      expect(after.signalKeys, {'a:1'});
    });

    test('a first plan made by a transfer records what was known then', () {
      // ⭐ No existing plan, so the keys passed in ARE what was known — this is the one case where the
      // parameter is used rather than ignored.
      final fresh = Draft.swap(
        existing: null,
        managerId: 7,
        gameweek: 6,
        basePlayerIds: const [1, 2, 3],
        benchIds: const [3],
        outId: 2,
        inId: 9,
        savedAt: DateTime(2026, 9, 21),
        signalKeys: const {'a:1'},
      );
      expect(fresh.signalKeys, {'a:1'});
      expect(fresh.since(const ['a:1', 'b:2']), {'b:2'});
    });
  });
}
