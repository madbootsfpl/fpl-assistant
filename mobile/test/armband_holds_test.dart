/// Does the captain survive? (tester feedback, item 1 — *"My team, C doesn't hold"*)
///
/// ⭐⭐ **A reproduction before a fix.** The whole armband path reads correctly — the draft serialises
/// `captain_id`, the overlay applies at render, the reload restores it — so reading it again was not going
/// to find the fault. This walks the exact sequence the app walks and asserts at each joint.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/draft.dart';
import 'package:shared_preferences/shared_preferences.dart';

MyTeam sampleTeam() {
  final file = File(
    '../spikes/018-flutter-read-slice/api-samples/my-team.json',
  );
  return MyTeam.fromJson(
    jsonDecode(file.readAsStringSync()) as Map<String, dynamic>,
  );
}

/// ⭐ Exactly what `_setArmband` builds when there is no draft yet — copied deliberately rather than
/// simplified, because a simplification is where a reproduction stops reproducing.
Draft asTheAppBuildsIt(
  MyTeam team,
  int managerId, {
  int? captainId,
  int? viceCaptainId,
}) {
  final base = Draft(
    managerId: managerId,
    gameweek: team.gameweek ?? 0,
    basePlayerIds: team.fplPlayerIds,
    playerIds: team.fplPlayerIds,
    benchIds: team.analysis.bench.map((p) => p.id).toList(),
    savedAt: DateTime.now(),
  );
  final nextCaptain = captainId ?? base.captainId ?? team.captainId;
  final nextVice = viceCaptainId ?? base.viceCaptainId ?? team.viceCaptainId;
  final collides = nextVice == nextCaptain;
  return base.copyWith(
    captainId: nextCaptain,
    viceCaptainId: collides ? null : nextVice,
    clearViceCaptain: collides,
  );
}

/// ⭐⭐ **The SECOND change takes a different path**, and that is the one worth testing: `_setArmband`
/// builds `base` from the existing draft rather than from a fresh one, so every `??` in it now falls
/// through to a value that is already set instead of to null.
Draft asTheAppBuildsItAgain(
  Draft existing,
  MyTeam team, {
  int? captainId,
  int? viceCaptainId,
}) {
  final base = existing;
  final nextCaptain = captainId ?? base.captainId ?? team.captainId;
  final nextVice = viceCaptainId ?? base.viceCaptainId ?? team.viceCaptainId;
  final collides = nextVice == nextCaptain;
  return base.copyWith(
    captainId: nextCaptain,
    viceCaptainId: collides ? null : nextVice,
    clearViceCaptain: collides,
  );
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('the armband survives a save and a reload', () async {
    final team = sampleTeam();
    final newCaptain = team.analysis.xi
        .firstWhere((p) => p.id != team.captainId)
        .id;

    final store = DraftStore();
    await store.save(asTheAppBuildsIt(team, 1, captainId: newCaptain));

    final back = await store.load();
    expect(back, isNotNull, reason: 'the draft did not come back at all');
    expect(
      back!.captainId,
      newCaptain,
      reason: 'the captain did not survive storage',
    );

    final verdict = back.checkAgainst(
      managerId: 1,
      gameweek: team.gameweek,
      fplPlayerIds: team.fplPlayerIds,
    );
    expect(
      verdict,
      DraftStaleness.fresh,
      reason: 'the app discards a draft that is not fresh — this is where a captain would vanish',
    );

    final shown = team.withArmbands(
      captainId: back.captainId ?? team.captainId,
      viceCaptainId: back.viceCaptainId ?? team.viceCaptainId,
    );
    expect(
      shown.captainId,
      newCaptain,
      reason: 'the overlay did not reach the pitch',
    );
  });

  test('promoting your vice to captain does not leave him wearing both', () {
    // ⚠️⚠️ `copyWith` is `viceCaptainId ?? this.viceCaptainId`, so passing **null to clear** the vice
    // does nothing at all. Making your vice the captain should empty the vice slot.
    final team = sampleTeam();
    final vice = team.viceCaptainId;
    expect(
      vice,
      isNotNull,
      reason: 'the sample has no vice-captain to promote',
    );

    final draft = asTheAppBuildsIt(team, 1, captainId: vice);
    expect(draft.captainId, vice);
    expect(
      draft.viceCaptainId,
      isNot(vice),
      reason:
          'one player is wearing C and V at once — FPL would reject this squad',
    );
  });

  test('changing your mind moves the armband', () {
    // ⭐ Tap one player, then another. The C must be on the second.
    final team = sampleTeam();
    final first = team.analysis.xi[0].id;
    final second = team.analysis.xi[1].id;

    final once = asTheAppBuildsIt(team, 1, captainId: first);
    final twice = asTheAppBuildsItAgain(once, team, captainId: second);
    expect(
      twice.captainId,
      second,
      reason: 'the armband did not move to the second player',
    );
  });

  test(
    'promoting your vice AFTER a vice has been set clears the vice slot',
    () {
      // ⚠️⚠️ The path the first vice test could not reach: once `base.viceCaptainId` is non-null,
      // `copyWith(viceCaptainId: null)` can no longer clear it — `null ?? this.viceCaptainId` keeps it.
      final team = sampleTeam();
      final a = team.analysis.xi[0].id;
      final b = team.analysis.xi[1].id;

      final withVice = asTheAppBuildsIt(team, 1, viceCaptainId: b);
      expect(withVice.viceCaptainId, b);

      // Now make that same player the captain.
      final promoted = asTheAppBuildsItAgain(withVice, team, captainId: b);
      expect(promoted.captainId, b);
      expect(
        promoted.viceCaptainId,
        isNot(b),
        reason: 'he is wearing C and V at once — FPL would reject this squad',
      );
      expect(a, isNotNull);
    },
  );

  /// ⭐⭐ **Calls the shipping function.** The earlier version of this helper re-described `_planSwap`
  /// in the test file — and a re-description is the thing that let the bug exist: it carried the armbands
  /// while the real code did not, so the test passed and proved nothing. `Draft.swap` now has one
  /// implementation and both sides call it.
  Draft asTheAppPlansASwap(Draft? existing, MyTeam team, int outId, int inId) =>
      Draft.swap(
        existing: existing,
        managerId: 1,
        gameweek: team.gameweek ?? 0,
        basePlayerIds: team.fplPlayerIds,
        benchIds: team.analysis.bench.map((p) => p.id).toList(),
        outId: outId,
        inId: inId,
        savedAt: DateTime.now(),
        teamCaptainId: team.captainId,
        teamViceCaptainId: team.viceCaptainId,
      );

  test('a transfer does not take your armband off — THE bug', () {
    // ⚠️⚠️ **"My team, C doesn't hold."** `_planSwap` built a fresh `Draft` and never carried the
    // armbands over, so the sequence the owner uses most — set a captain, then apply a suggested
    // transfer — silently dropped the C. ⭐ *The armband survived storage, a reload and a restart; what
    // it did not survive was the other feature.*
    final team = sampleTeam();
    final captain = team.analysis.xi[0].id;
    final out = team.analysis.xi.last.id;
    const incoming = 999999;

    final withCaptain = asTheAppBuildsIt(team, 1, captainId: captain);
    final afterSwap = asTheAppPlansASwap(withCaptain, team, out, incoming);

    expect(
      afterSwap.playerIds,
      contains(incoming),
      reason: 'the transfer itself must still happen',
    );
    expect(
      afterSwap.captainId,
      captain,
      reason: 'the armband came off during a transfer',
    );
  });

  test('transferring away your captain takes the armband with him', () {
    // ⭐ The other half: carrying an armband forward is only right while the player is still yours.
    // A C on a player who has been sold is worse than no C.
    final team = sampleTeam();
    final captain = team.analysis.xi[0].id;
    const incoming = 999999;

    final withCaptain = asTheAppBuildsIt(team, 1, captainId: captain);
    final afterSwap = asTheAppPlansASwap(withCaptain, team, captain, incoming);

    expect(afterSwap.playerIds, isNot(contains(captain)));
    expect(
      afterSwap.captainId,
      isNot(captain),
      reason: 'the armband is on a player who is no longer in the squad',
    );
  });

  test('selling a bench player puts his replacement on the bench', () {
    // ⚠️ Not covered until a mutation removed the line and nothing went red: the outgoing player has to
    // leave the bench too, or the plan holds a man you no longer own **and** omits the one you bought.
    final team = sampleTeam();
    final out = team.analysis.bench.first.id;
    const incoming = 999999;

    final draft = asTheAppPlansASwap(null, team, out, incoming);
    expect(
      draft.benchIds,
      isNot(contains(out)),
      reason: 'the sold player is still on the bench',
    );
    expect(
      draft.benchIds,
      contains(incoming),
      reason: 'his replacement never reached the bench',
    );
  });

  test('the armband does not quietly reorder your bench', () {
    // ⚠️ `_setArmband` stores `analysis.bench` — the **engine's recommended** bench — as the draft's.
    // Tapping "make captain" must not submit a lineup change nobody asked for.
    final team = sampleTeam();
    final draft = asTheAppBuildsIt(
      team,
      1,
      captainId: team.analysis.xi.first.id,
    );
    expect(
      draft.swaps,
      isEmpty,
      reason: 'an armband change produced transfers',
    );
    expect(
      draft.benchIds.toSet(),
      team.analysis.bench.map((p) => p.id).toSet(),
    );
  });
}
