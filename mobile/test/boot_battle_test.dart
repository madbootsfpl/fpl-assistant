/// Boot Battle — its name, and whether it can be read (ADR-258).
///
/// ⭐⭐⭐ **The contrast test walks the rendered tree, not the source.** The owner could not read this page
/// on a phone in dark mode, and the cause was three separate choices that each looked reasonable in
/// isolation: the losing value at `white38`, one form row at `white10`, and one projection line at
/// `white30`. ⚠️ *Grepping the source for a colour would catch the ones I remembered to look for* — this
/// asks every `Text` actually on screen how visible it is.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/boot_battle.dart';

BootBattle sample() => BootBattle.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/compare.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(
    // ⭐ The app's real ground, not a default. Contrast is a relationship, and testing against white
    // would pass everything the owner could not read.
    backgroundColor: const Color(0xFF17131F),
    body: SingleChildScrollView(child: child),
  ),
);

void main() {
  testWidgets('it is called Boot Battle, and wears the brand', (tester) async {
    // ⚠️ *A feature with two names is two features to anyone who has to be told which is which.*
    // `player_card.py` has titled it **Boot Battle** since the wave-3 feedback; the phone called it
    // "Compare" and titled the page "A v B".
    await tester.pumpWidget(
      wrap(BootBattleView(future: Future.value(sample()))),
    );
    await tester.pumpAndSettle();

    expect(find.text('BOOT BATTLE'), findsOneWidget);
    expect(find.textContaining('MAD'), findsWidgets);
  });

  testWidgets('every word on the page is legible on the dark ground', (
    tester,
  ) async {
    await tester.pumpWidget(
      wrap(BootBattleView(future: Future.value(sample()))),
    );
    await tester.pumpAndSettle();

    final faint = <String>[];
    for (final text in tester.widgetList<Text>(find.byType(Text))) {
      final colour = text.style?.color;
      final shown = text.data ?? text.textSpan?.toPlainText() ?? '';
      if (colour == null || shown.trim().isEmpty) continue;
      // ⚠️ **0.30 is the floor, and it is deliberately low.** This is not an accessibility standard — it
      // is the line below which the owner could not read his own screen. `white24` sits under it; the
      // brand's own colours sit far above.
      if (colour.a < 0.30) {
        faint.add('"$shown" at alpha ${colour.a.toStringAsFixed(2)}');
      }
    }
    expect(
      faint,
      isEmpty,
      reason: 'unreadable on a near-black background: $faint',
    );
  });

  testWidgets('each player owns a colour, and keeps it', (tester) async {
    // ⭐⭐ **Colour is identity here, not victory — the web does it the other way round.**
    //
    // The web tints the winning value teal and leaves the loser grey **on a white card**, where grey is
    // legible. On this ground that made the losing side, its form row and its line all but invisible.
    // ⚠️ So a reader can follow one player down the page, and nobody disappears for losing.
    final battle = sample();
    await tester.pumpWidget(wrap(BootBattleView(future: Future.value(battle))));
    await tester.pumpAndSettle();

    Color? colourOf(String name) => tester
        .widgetList<Text>(find.text(name))
        .map((t) => t.style?.color)
        .firstWhere((c) => c != null, orElse: () => null);

    expect(colourOf(battle.a.player.name), aColour);
    expect(colourOf(battle.b.player.name), bColour);
    expect(aColour, isNot(bColour), reason: 'the two sides share a colour');
  });

  testWidgets('the two form rows are visibly different from each other', (
    tester,
  ) async {
    // ⚠️⚠️ **The boxes, not the text.** One row used to be `white10` on `#17131F` — a dark grey box on a
    // dark ground, which is half of what the owner could not read. A mutation restoring it survived a
    // contrast test that inspected only `Text`, because the numbers inside stayed white.
    await tester.pumpWidget(
      wrap(BootBattleView(future: Future.value(sample()))),
    );
    await tester.pumpAndSettle();

    Color fillOf(String key) {
      final box = tester
          .widgetList<Container>(
            find.descendant(
              of: find.byKey(Key(key)),
              matching: find.byType(Container),
            ),
          )
          .first;
      return (box.decoration! as BoxDecoration).color!;
    }

    final a = fillOf('form-a');
    final b = fillOf('form-b');
    expect(a, isNot(b), reason: 'both rows drew the same fill');
    for (final fill in [a, b]) {
      // ⭐ Enough alpha to separate from the page. `white10` is 0.10 and sits below it.
      expect(
        fill.a,
        greaterThanOrEqualTo(0.18),
        reason: 'a form row is nearly the same colour as the background',
      );
    }
  });

  testWidgets('a losing value is still readable', (tester) async {
    // ⚠️⚠️ **The specific failure.** Every stat a player lost rendered at `white38` — and on the grid,
    // that is most of the page.
    final battle = sample();
    await tester.pumpWidget(wrap(BootBattleView(future: Future.value(battle))));
    await tester.pumpAndSettle();

    final loser = battle.rows.firstWhere(
      (r) => r.winner == 'b',
      orElse: () => battle.rows.first,
    );
    final value = tester
        .widgetList<Text>(find.text(loser.a))
        .map((t) => t.style)
        .first;
    expect(
      value?.color?.a,
      greaterThanOrEqualTo(0.6),
      reason: 'the losing side of "${loser.label}" is barely visible',
    );
  });

  test('the committed sample really is two of the same position', () {
    // ⚠️ `compare` refuses a cross-position pairing, so a sample that drifted would make every widget
    // test above render an error instead of a battle.
    final battle = sample();
    expect(battle.a.player.position, battle.b.player.position);
    expect(battle.rows, isNotEmpty);
  });
}
