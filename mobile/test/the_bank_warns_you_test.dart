/// The bank says when you cannot afford the plan (ADR-337).
///
/// 🔴 **Reported**: *"I can make a transfer and have no idea if I have enough funds to do same."* Five
/// changes, and £1.0m In the bank sat still through all of them.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/pitch.dart';

/// ⭐ Built by editing the sample's JSON rather than adding a `copyWith` to production for a test's
/// benefit — and it exercises the parse path on the way through.
MyTeam teamWithBank(double? bank, {required bool estimated}) {
  final json = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  final squad = json['squad'] as Map<String, dynamic>;
  squad['bank'] = bank;
  squad['bank_is_estimated'] = estimated;
  return MyTeam.fromJson(json);
}

Future<void> pumpWithBank(
  WidgetTester tester, {
  required double? bank,
  required bool estimated,
}) async {
  await tester.binding.setSurfaceSize(const Size(390, 900));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: PitchView(
          team: teamWithBank(bank, estimated: estimated),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Color? bankColour(WidgetTester tester) {
  final value = tester
      .widgetList<Text>(find.byType(Text))
      .firstWhere(
        (t) => (t.data ?? '').startsWith('£-') || (t.data ?? '') == '£1.0m',
      );
  return value.style?.color;
}

void main() {
  testWidgets('FPL\'s own bank is plain and unlabelled as an estimate', (
    tester,
  ) async {
    await pumpWithBank(tester, bank: 1.0, estimated: false);

    expect(find.text('In the bank'), findsOneWidget);
    expect(find.textContaining('est.'), findsNothing);
    expect(bankColour(tester), isNot(Brand.bad));
  });

  testWidgets('a planned bank says it is an estimate', (tester) async {
    // ⚠️ FPL pays back only half of a player's rise since you bought him and publishes no selling
    // price, so this errs optimistic. ⭐ An estimate that flatters the reader about money must admit it.
    await pumpWithBank(tester, bank: 0.4, estimated: true);

    expect(find.textContaining('est.'), findsOneWidget);
  });

  testWidgets('an unaffordable plan turns the bank red and says over budget', (
    tester,
  ) async {
    // 🔴 The whole report: this is the state that was unreachable before.
    await pumpWithBank(tester, bank: -8.1, estimated: true);

    expect(find.text('£-8.1m'), findsOneWidget);
    expect(find.textContaining('Over budget'), findsOneWidget);
    expect(
      bankColour(tester),
      Brand.bad,
      reason: 'an overdrawn bank is not flagged',
    );
  });

  testWidgets('an unknown bank is still a dash, not zero', (tester) async {
    // ⭐ The rule that was already right: `—` says "not known"; £0.0m says "you are skint".
    await pumpWithBank(tester, bank: null, estimated: false);

    expect(find.text('—'), findsWidgets);
  });
}
