/// Changing two players' places (ADR-246).
///
/// ⭐⭐⭐ **The rule under test is the server's, and that is the point.** FPL's formation limits live in
/// `XI_FLEX`; the client only renders the list it is given. ⚠️ These tests guard the half the client owns:
/// that the swap lands in the right bench slot, that the fifteen are untouched, and that a nonsensical
/// pair changes nothing.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/draft.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
        File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
            .readAsStringSync(),
      )
      as Map<String, dynamic>,
);

Draft swap(MyTeam team, int a, int b, {Draft? existing}) => Draft.substitute(
  existing: existing,
  managerId: 1,
  gameweek: team.gameweek ?? 0,
  basePlayerIds: team.fplPlayerIds,
  benchIds: team.analysis.bench.map((p) => p.id).toList(),
  a: a,
  b: b,
  savedAt: DateTime.now(),
  teamCaptainId: team.captainId,
  teamViceCaptainId: team.viceCaptainId,
);

void main() {
  test('the server tells the client who is legal, and keepers are the hard case', () {
    final team = sampleTeam();
    expect(team.swaps, isNotEmpty, reason: 'the sample carries no swap lists');

    final keepers = [
      ...team.analysis.xi,
      ...team.analysis.bench,
    ].where((p) => p.position == 'GK').toList();
    expect(keepers, hasLength(2));

    // ⚠️ A keeper may only ever change places with the other keeper. A client that worked this out
    // itself would be a second implementation of a rule the engine owns — and this is the one everybody
    // gets wrong first.
    for (final gk in keepers) {
      expect(team.swapsFor(gk.id), [keepers.firstWhere((o) => o.id != gk.id).id]);
    }
  });

  test('a substitution takes the outgoing player’s bench slot, not the end of the queue', () {
    final team = sampleTeam();
    final bench = team.analysis.bench.map((p) => p.id).toList();
    final coming = bench.first;
    final going = team.swapsFor(coming).first;

    final draft = swap(team, coming, going);
    // ⭐ FPL substitutes in bench order, so appending would quietly demote him to last — a change the
    // manager did not ask for, hidden inside one he did.
    expect(draft.benchIds.indexOf(going), 0);
    expect(draft.benchIds, hasLength(4));
  });

  test('the fifteen are never touched', () {
    final team = sampleTeam();
    final bench = team.analysis.bench.map((p) => p.id).toList();
    final draft = swap(team, bench.first, team.swapsFor(bench.first).first);

    expect(draft.playerIds.toSet(), team.fplPlayerIds.toSet());
    expect(draft.swaps, isEmpty, reason: 'a substitution is not a transfer');
  });

  test('armbands survive a substitution', () {
    // ⚠️ ADR-241 was exactly this failure in `_planSwap`: a new Draft built without carrying them.
    final team = sampleTeam();
    final bench = team.analysis.bench.map((p) => p.id).toList();
    final captain = team.analysis.xi.first.id;

    final first = swap(team, bench.first, team.swapsFor(bench.first).first)
        .copyWith(captainId: captain);
    final second = swap(team, bench.last, team.swapsFor(bench.last).first, existing: first);

    expect(second.captainId, captain);
  });

  test('two starters is not a substitution and changes nothing', () {
    // ⭐ A no-op beats inventing a lineup nobody asked for.
    final team = sampleTeam();
    final xi = team.analysis.xi.map((p) => p.id).toList();
    final before = swap(team, xi[0], xi[1]);
    expect(before.benchIds, team.analysis.bench.map((p) => p.id).toList());
  });
}
