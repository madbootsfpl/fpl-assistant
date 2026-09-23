/// The strip that fields your best eleven (ADR-244).
///
/// ⚠️⚠️ **The claim worth guarding is what the button does NOT do.** Starting a player you already own is
/// free and reversible; a transfer costs points and cannot be undone. ⭐ *One button must not do both,
/// whatever the xP says* — and nothing about the strip's appearance would reveal it if it did.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/apply_plan.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

/// The sample, with the suggestion trimmed to `n` incoming players.
///
/// ⭐ Edits the JSON rather than hand-building a `MyTeam`: the fifteen, the bench order and the fixtures
/// all stay real, and only the thing under test changes.
MyTeam teamBringingIn(int n) {
  final json = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  final plan = json['suggested_lineup'] as Map<String, dynamic>;
  plan['bring_in'] = (plan['bring_in'] as List).take(n).toList();
  plan['drop'] = (plan['drop'] as List).take(n).toList();
  return MyTeam.fromJson(json);
}

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: const Color(0xFF17131F), body: child),
);

void main() {
  test('the committed sample actually carries a suggestion', () {
    // ⚠️⚠️ **Three tests below would silently pass by skipping if it did not.** The sample is regenerated
    // from live data, and a week where the fixture squad happens to be optimal would quietly empty this
    // file of everything it tests. ⭐ *A test that skips itself when the data is uninteresting has to say
    // so out loud, or it reads as coverage.*
    expect(
      sampleTeam().suggestedLineup,
      isNotNull,
      reason:
          'regenerate the samples — or pick a fixture squad with a wrong bench',
    );
  });

  test('a suggestion only ever reorders the fifteen', () {
    final team = sampleTeam();
    final plan = team.suggestedLineup!;
    expect(plan.start, hasLength(11));
    expect(plan.bench, hasLength(4));
    expect(plan.changes, plan.bringIn.length);
    // ⚠️ The fifteen are the fifteen. A suggestion that introduced a player would be a transfer.
    expect({...plan.start, ...plan.bench}, {...team.fplPlayerIds});
  });

  testWidgets('it leads with what the change is worth, and names who', (
    tester,
  ) async {
    final team = sampleTeam();
    final plan = team.suggestedLineup!;
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: team, onApply: (_) async {})),
    );

    // ⭐ The gain first, because it is the reason. "2 changes" is a cost; "+5.5 xP" is what it buys.
    expect(
      find.textContaining('+${plan.gain.toStringAsFixed(1)} xP'),
      findsOneWidget,
    );
    // ⚠️ **Names, not a count** — "2 changes" is a number you then have to go and look up. Asserted on
    // a **name** rather than on the word around it, so the next copy edit changes the sentence without
    // breaking the claim. ⭐ *Pin the thing the test is about, not the wording it happens to sit in.*
    final first = team.nameOf(plan.bringIn.first);
    expect(first, isNotEmpty);
    expect(find.textContaining(first), findsOneWidget);
  });

  testWidgets('nothing to do is said once, quietly, not shouted or hidden', (
    tester,
  ) async {
    final team = sampleTeam();
    // ⭐ Silence and reassurance are different answers, and both are sometimes right. A strip that
    // vanished entirely would leave a reader wondering whether the app had checked at all.
    final optimal = MyTeam.fromJson({
      ...jsonDecode(
        File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
            .readAsStringSync(),
      ) as Map<String, dynamic>,
      'suggested_lineup': null,
    });
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: optimal, onApply: (_) async {})),
    );

    expect(find.textContaining('already the best'), findsOneWidget);
    expect(
      find.byType(TextButton),
      findsNothing,
      reason: 'there is nothing to press',
    );
    expect(team.fplPlayerIds, isNotEmpty);
  });

  testWidgets('pressing it hands back the plan, unchanged', (tester) async {
    final team = sampleTeam();
    final plan = team.suggestedLineup!;
    SuggestedLineup? applied;
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: team, onApply: (p) async => applied = p)),
    );
    // ⚠️ By type, not by label: the label is now count-dependent, and a test that hard-codes one
    // form would break on a sample regenerated with a different number of changes.
    await tester.tap(find.byType(TextButton));
    await tester.pump();

    expect(applied, isNotNull);
    expect(applied!.bench, plan.bench);
    // ⚠️⚠️ The bench order is FPL's substitution order and must survive the handover untouched — the
    // caller stores it verbatim.
    expect(applied!.start, plan.start);
  });

  // ⭐ "Play Him" was asked for by name — ⚠️ but the strip beside it reads "start Salah and Saka", so a
  // flat rename would have said "Play Him" over a two-player change. *A label is part of the sentence the
  // screen is saying, not a word on its own.* (ADR-264)
  testWidgets('one player coming in reads "Play Him"', (tester) async {
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: teamBringingIn(1), onApply: (_) async {})),
    );
    expect(find.text('Play Him'), findsOneWidget);
    expect(find.text('Play Them'), findsNothing);
  });

  testWidgets('two coming in reads "Play Them"', (tester) async {
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: teamBringingIn(2), onApply: (_) async {})),
    );
    expect(find.text('Play Them'), findsOneWidget);
    expect(find.text('Play Him'), findsNothing);
  });

  testWidgets('the old wording is gone entirely', (tester) async {
    await tester.pumpWidget(
      wrap(ApplyPlanStrip(team: sampleTeam(), onApply: (_) async {})),
    );
    expect(find.text('Field it'), findsNothing);
  });
}
