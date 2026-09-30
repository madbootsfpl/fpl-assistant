/// A fact and a forecast, told apart (ADR-335).
///
/// ⭐⭐⭐ **The card was about to carry two arrows meaning different things.** One is what the price *did*
/// — certain. The other is what pressure says it *might* do — right about 40% of the time (ADR-334).
/// ⚠️ *An estimate that looks like a fact is worse than no estimate*, because a reader cannot discount
/// what they cannot tell apart. So the forecast keeps the colour and the fact is plain.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/pitch.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Future<void> pumpPitch(WidgetTester tester, PitchMode mode) async {
  await tester.binding.setSurfaceSize(const Size(390, 900));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: PitchView(
          team: sampleTeam(),
          mode: mode,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('the endpoint sends the squad line', () {
    // ⚠️ The sample is the contract (ADR-327). If this key vanishes the app silently shows zeros.
    final team = sampleTeam();
    expect(
      team.squadPrice.falling + team.squadPrice.rising,
      greaterThan(0),
      reason: 'no squad price summary in the sample',
    );
  });

  test('a price move carries what it DID as well as what it might do', () {
    // 🔴 `changedThisGameweek` has been parsed since the endpoint shipped and was never rendered.
    final team = sampleTeam();
    expect(team.prices, isNotEmpty);
    expect(
      team.prices.values.any((m) => m.changedThisGameweek != 0),
      isTrue,
      reason: 'no player in the sample has moved price — the fixture cannot test this',
    );
  });

  testWidgets('the squad line appears in PRICE mode', (tester) async {
    await pumpPitch(tester, PitchMode.price);
    expect(find.textContaining('Squad'), findsOneWidget);
  });

  testWidgets('and nowhere else', (tester) async {
    // ⭐ A squad-value line above the fixtures view is a number competing with what the reader came for.
    await pumpPitch(tester, PitchMode.nextGw);
    expect(find.textContaining('under selling pressure'), findsNothing);
    expect(find.textContaining('Squad value'), findsNothing);
  });

  testWidgets('selling pressure is named with what it is worth', (
    tester,
  ) async {
    await pumpPitch(tester, PitchMode.price);
    final line = tester
        .widgetList<Text>(find.byType(Text))
        .map((t) => t.textSpan?.toPlainText() ?? t.data ?? '')
        .firstWhere((s) => s.contains('Squad'), orElse: () => '');
    expect(line, contains('£'), reason: 'the squad line names no money: $line');
  });

  testWidgets('the fact is plain and the forecast is coloured', (tester) async {
    // ⭐⭐ The property the whole ADR turns on, asserted rather than described.
    await pumpPitch(tester, PitchMode.price);
    final spans = tester
        .widgetList<Text>(find.byType(Text))
        .map((t) => t.textSpan)
        .whereType<TextSpan>()
        .where((s) => s.toPlainText().contains('Squad'));
    expect(spans, isNotEmpty, reason: 'no squad line found');

    for (final root in spans) {
      for (final child in root.children!.cast<TextSpan>()) {
        final text = child.text ?? '';
        final colour = child.style?.color;
        if (text.contains('this week') || text.contains('unchanged')) {
          expect(
            colour,
            isNot(Brand.bad),
            reason: 'the FACT is painted like a forecast: "$text"',
          );
          expect(
            colour,
            isNot(Brand.green),
            reason: 'the FACT is painted like a forecast: "$text"',
          );
        }
        if (text.contains('pressure')) {
          expect(
            colour,
            Brand.bad,
            reason: 'the forecast lost its colour: "$text"',
          );
        }
      }
    }
  });
}
