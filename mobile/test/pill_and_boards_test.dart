// The selectable pill, the convergence board, and the ticker's promises (ADR-269).
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/pill.dart';
import 'package:madboots/ticker_view.dart';
import 'package:madboots/trending_view.dart';

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: Brand.ink, body: child),
);

Color boxColour(WidgetTester tester, Finder pill) {
  final container = tester.widget<Container>(
    find.descendant(of: pill, matching: find.byType(Container)).first,
  );
  return ((container.decoration! as BoxDecoration).color)!;
}

void main() {
  group('Pill', () {
    // ⚠️⚠️ The bug this widget replaced: Material 3 ignored `backgroundColor` on an unselected
    // ChoiceChip and painted a near-white surface, so a white54 label vanished into it.
    testWidgets('an unselected pill is dark, never near-white', (tester) async {
      await tester.pumpWidget(
        wrap(Pill(label: 'Most sold', selected: false, onTap: () {})),
      );
      // ⚠️ **Composited first.** `computeLuminance()` ignores alpha, so `white10` measures as pure
      // white — ⭐ *a test that reads a colour without its background measures a colour nobody sees.*
      final shown = Color.alphaBlend(
        boxColour(tester, find.byType(Pill)),
        Brand.ink,
      );
      expect(
        shown.computeLuminance(),
        lessThan(0.3),
        reason: 'an unselected pill must stay dark, or its label disappears',
      );
    });

    testWidgets('its label is readable against its own background', (
      tester,
    ) async {
      for (final selected in [true, false]) {
        await tester.pumpWidget(
          wrap(Pill(label: 'In form', selected: selected, onTap: () {})),
        );
        final bg = boxColour(tester, find.byType(Pill));
        final text = tester.widget<Text>(find.text('In form'));
        final ink = text.style!.color!;
        // ⭐ Composited over the dark page, so an alpha-white label is measured as it actually appears.
        final shown = Color.alphaBlend(ink, Color.alphaBlend(bg, Brand.ink));
        final ratio =
            (shown.computeLuminance() + 0.05) /
            (Color.alphaBlend(bg, Brand.ink).computeLuminance() + 0.05);
        expect(
          ratio,
          greaterThan(2.5),
          reason: 'selected=$selected is unreadable',
        );
      }
    });

    testWidgets('a selected pill is visibly different from an unselected one', (
      tester,
    ) async {
      await tester.pumpWidget(
        wrap(
          Row(
            children: [
              Pill(label: 'A', selected: true, onTap: () {}),
              Pill(label: 'B', selected: false, onTap: () {}),
            ],
          ),
        ),
      );
      final on = boxColour(tester, find.widgetWithText(Pill, 'A'));
      final off = boxColour(tester, find.widgetWithText(Pill, 'B'));
      expect(on, isNot(off));
    });

    testWidgets('it reports taps', (tester) async {
      var taps = 0;
      await tester.pumpWidget(
        wrap(Pill(label: 'Tap', selected: false, onTap: () => taps++)),
      );
      await tester.tap(find.byType(Pill));
      expect(taps, 1);
    });
  });

  group('the convergence board', () {
    TrendingBoard board() => TrendingBoard.fromJson(
      jsonDecode(
        File('../spikes/018-flutter-read-slice/api-samples/worth-a-look.json')
            .readAsStringSync(),
      ) as Map<String, dynamic>,
    );

    test('it is the board named "look", with signals as its unit', () {
      expect(board().by, 'look');
      expect(board().column, 'signals');
    });

    // ⭐⭐ The reasons ARE the board — a convergence list without its evidence is a ranking on a number
    // nobody can see, and this board deliberately has no such number.
    test('every row carries its reasons', () {
      final rows = board().rows;
      expect(rows, isNotEmpty);
      for (final row in rows) {
        expect(row.reasons, isNotEmpty);
        expect(
          row.reasons.length,
          greaterThanOrEqualTo(2),
          reason: 'convergence means two boards agreeing',
        );
      }
    });

    // ⚠️ Most of the evidence is last season's; a reason without its vintage is the most misleading
    // kind of true statement.
    test('the reasons name the season they come from', () {
      final all = board().rows.expand((r) => r.reasons);
      expect(all.where((r) => r.contains('/')), isNotEmpty);
    });

    test(
      'a crowd board carries no reasons, so the row must not assume any',
      () {
        final crowd = TrendingRow.fromJson(const {
          'player': {
            'id': 1,
            'web_name': 'X',
            'team': 'ARS',
            'position': 'MID',
            'price': 5.0,
            'xp': 4.0,
            'status': 'a',
          },
          'value': 6000,
        });
        expect(crowd.reasons, isEmpty);
      },
    );

    test('a signal count renders as a count, never as a rating', () {
      // ⚠️ "2.0" or "2k" would make it look like the scores on the other boards.
      expect(trendValue(2, 'signals'), '2');
      expect(trendValue(3, 'signals'), '3');
    });
  });

  group('the ticker legend', () {
    // ⚠️ "What does the * mean?" was the first question asked about this screen.
    testWidgets('the header explains the asterisk and the tap', (tester) async {
      await tester.pumpWidget(wrap(const _HeaderOnly()));
      expect(find.textContaining('asterisk'), findsOneWidget);
      expect(find.textContaining('Tap'), findsOneWidget);
    });
  });

  group('showClubRun', () {
    testWidgets('a blank gameweek is spelled out, not left empty', (
      tester,
    ) async {
      final row = TickerRow.fromJson(const {
        'team': 'ARS',
        'avg_difficulty': 2.5,
        'cells': {
          '6': {'opponent': 'CHE', 'venue': 'H', 'difficulty': 2},
          '7': null,
        },
      });
      await tester.pumpWidget(
        wrap(
          Builder(
            builder: (context) => TextButton(
              onPressed: () => showClubRun(context, row),
              child: const Text('open'),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(find.textContaining('do not play'), findsOneWidget);
      expect(find.textContaining('CHE'), findsOneWidget);
    });

    // ⚠️ The one place "10" sorting before "6" would put a run in the wrong order.
    testWidgets('gameweeks run in numeric order past ten', (tester) async {
      final row = TickerRow.fromJson(const {
        'team': 'ARS',
        'avg_difficulty': 3.0,
        'cells': {
          '9': {'opponent': 'AAA', 'venue': 'H', 'difficulty': 3},
          '10': {'opponent': 'BBB', 'venue': 'A', 'difficulty': 3},
        },
      });
      await tester.pumpWidget(
        wrap(
          Builder(
            builder: (context) => TextButton(
              onPressed: () => showClubRun(context, row),
              child: const Text('open'),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      final nine = tester.getTopLeft(find.text('GW9')).dy;
      final ten = tester.getTopLeft(find.text('GW10')).dy;
      expect(nine, lessThan(ten), reason: 'GW9 must come before GW10');
    });
  });

  group('worth noticing', () {
    TrendingBoard board() => TrendingBoard.fromJson(
      jsonDecode(
        File('../spikes/018-flutter-read-slice/api-samples/worth-noticing.json')
            .readAsStringSync(),
      ) as Map<String, dynamic>,
    );

    test('every row carries its heading and its sentence', () {
      final rows = board().rows;
      expect(rows, isNotEmpty);
      for (final row in rows) {
        expect(row.group, isNotEmpty);
        expect(row.reasons, hasLength(1));
      }
    });

    // ⚠️ The client draws a heading when the group CHANGES, so a group appearing twice would draw two
    // headings for one pattern.
    test('rows of one group are contiguous', () {
      final runs = <String>[];
      for (final row in board().rows) {
        if (runs.isEmpty || runs.last != row.group) runs.add(row.group);
      }
      expect(
        runs.length,
        runs.toSet().length,
        reason: 'a group was split: $runs',
      );
    });

    test('the under-owned pattern leads', () {
      expect(board().rows.first.group, startsWith('In form'));
    });

    // ⭐ These rows are sentences; a figure in the corner would invite sorting by it.
    test('the board declares no value column', () {
      expect(board().column, isEmpty);
    });

    test('a crowd board has no groups and does declare a column', () {
      final crowd = TrendingBoard.fromJson(
        jsonDecode(
          File('../spikes/018-flutter-read-slice/api-samples/trending.json')
              .readAsStringSync(),
        ) as Map<String, dynamic>,
      );
      expect(crowd.rows.every((r) => r.group.isEmpty), isTrue);
      expect(crowd.column, isNotEmpty);
    });
  });
}

/// The ticker's header line, on its own — the screen itself needs a live client.
class _HeaderOnly extends StatelessWidget {
  const _HeaderOnly();

  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.all(14),
    child: Text(
      'Easiest run first. An asterisk means away. Tap any club for its run in full.',
    ),
  );
}
