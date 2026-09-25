// The fixture ticker (ADR-265) — parsed from the committed sample the server actually produced.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/ticker_view.dart';

FixtureTicker sample() => FixtureTicker.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/ticker.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

/// Renders the grid against the committed sample, and returns the name of a club that is **not** in
/// `myClubs` — so a filter test can assert on something it should have removed.
Future<String> pumpTicker(
  WidgetTester tester, {
  Set<String> myClubs = const {},
}) async {
  final body = File('../spikes/018-flutter-read-slice/api-samples/ticker.json')
      .readAsStringSync();
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: TickerView(
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient(
              (_) async => http.Response(
                body,
                200,
                headers: const {'content-type': 'application/json'},
              ),
            ),
          ),
          myClubs: myClubs,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return sample().rows
      .map((r) => r.team)
      .firstWhere((c) => !myClubs.contains(c));
}

void main() {
  group('parsing', () {
    test('every club arrives, easiest run first', () {
      final grid = sample();
      expect(grid.rows.length, 20);
      final rated = grid.rows
          .map((r) => r.avgDifficulty)
          .whereType<double>()
          .toList();
      expect(rated, orderedEquals([...rated]..sort()));
    });

    // ⚠️ JSON has no integer object keys; the server stringifies them and the client must parse back,
    // or "10" sorts before "6" (ADR-219).
    test('gameweek keys parse back to integers and match the header', () {
      final grid = sample();
      for (final row in grid.rows) {
        expect(row.cells.keys.toSet(), grid.gameweeks.toSet());
      }
    });

    test('the order comes from gameweeks, not from the cell map', () {
      final grid = sample();
      expect(grid.gameweeks, orderedEquals([...grid.gameweeks]..sort()));
    });

    test('a blank gameweek parses as a present key holding null', () {
      final grid = FixtureTicker.fromJson({
        'gameweeks': [6, 7],
        'rows': [
          {
            'team': 'ARS',
            'avg_difficulty': 2.0,
            'cells': {
              '6': {'opponent': 'CHE', 'venue': 'H', 'difficulty': 2},
              '7': null,
            },
          },
        ],
      });
      final cells = grid.rows.single.cells;
      expect(cells.containsKey(7), isTrue, reason: 'the key must exist');
      expect(cells[7], isNull, reason: 'and say "they do not play"');
    });

    test('a club with no rated fixture has no average rather than a zero', () {
      final grid = FixtureTicker.fromJson({
        'gameweeks': [6],
        'rows': [
          {
            'team': 'ARS',
            'avg_difficulty': null,
            'cells': {'6': null},
          },
        ],
      });
      // ⚠️ 0 would read as *the easiest run in the league*.
      expect(grid.rows.single.avgDifficulty, isNull);
    });
  });

  group('a double', () {
    final double_ = TickerCell.fromJson({
      'opponent': 'CHE',
      'venue': 'H',
      'difficulty': 5,
      'opponents': ['CHE', 'ARS'],
      'venues': ['H', 'A'],
    });

    test('is recognised, and labels both matches', () {
      expect(double_.isDouble, isTrue);
      expect(double_.label, 'CHE (H) + ARS (A)');
    });

    test('a single fixture is not a double', () {
      final one = TickerCell.fromJson({
        'opponent': 'CHE',
        'venue': 'A',
        'difficulty': 3,
        'opponents': ['CHE'],
        'venues': ['A'],
      });
      expect(one.isDouble, isFalse);
      expect(one.label, 'CHE (A)');
    });
  });

  group('colours', () {
    // ⚠️⚠️ The one reversal that would be silently catastrophic: nobody checks a colour legend, they act
    // on it. Green must mean easy.
    test('easy is green and hard is red, FPL\'s direction', () {
      expect(difficultyColour(1).g, greaterThan(difficultyColour(1).r));
      expect(difficultyColour(5).r, greaterThan(difficultyColour(5).g));
    });

    // ⚠️ **Not "redness rises monotonically"** — that was this test's first draft and it failed against
    // correct colours: FPL's band 5 is a *dark maroon*, so it carries less red than the brighter band 4.
    // ⭐ *A property the design does not have is not a property worth asserting.* The real rule is the
    // direction of dominance, which is what a reader actually decodes.
    test('1-2 read green, 3 is neutral, 4-5 read red', () {
      for (final easy in [1, 2]) {
        expect(
          difficultyColour(easy).g,
          greaterThan(difficultyColour(easy).r),
          reason: 'band $easy must read as easy',
        );
      }
      final mid = difficultyColour(3);
      expect(
        (mid.r - mid.g).abs(),
        lessThan(0.08),
        reason: 'band 3 must not lean either way',
      );
      for (final hard in [4, 5]) {
        expect(
          difficultyColour(hard).r,
          greaterThan(difficultyColour(hard).g),
          reason: 'band $hard must read as hard',
        );
      }
    });

    // ⚠️⚠️ **A raw luminance difference was too lenient and let a real defect through.** White ink on
    // the bright green band scored 0.5 on that measure and is genuinely hard to read; forcing every band
    // to white ink survived the first mutation run. ⭐ *A threshold invented to look strict is not a
    // threshold* — this is the WCAG contrast ratio, with the published bar for large text.
    double contrastRatio(Color a, Color b) {
      final l1 = a.computeLuminance();
      final l2 = b.computeLuminance();
      final hi = l1 > l2 ? l1 : l2;
      final lo = l1 > l2 ? l2 : l1;
      return (hi + 0.05) / (lo + 0.05);
    }

    test('every band gets ink that is actually readable on it', () {
      for (var d = 1; d <= 5; d++) {
        expect(
          contrastRatio(difficultyInk(d), difficultyColour(d)),
          greaterThanOrEqualTo(3.0),
          reason: 'band $d is unreadable',
        );
      }
    });

    test(
      'an out-of-range difficulty still gets a colour rather than throwing',
      () {
        expect(difficultyColour(9), isA<Color>());
        expect(difficultyColour(0), isA<Color>());
      },
    );
  });

  // ── owner feedback: the venue, and a squad filter ───────────────────────────

  testWidgets('a fixture says (H) or (A), never an unmarked home game', (
    tester,
  ) async {
    // ⚠️⚠️ **An asterisk marks one case and leaves the other unmarked**, so the *absence* of a mark has
    // to be read as information — ⭐ *a reader who has not found the legend cannot tell a home fixture
    // from a typo.* Two labels are longer than one mark and shorter than the explanation one mark needs.
    await pumpTicker(tester);

    expect(find.textContaining('(H)'), findsWidgets);
    expect(find.textContaining('(A)'), findsWidgets);
    expect(find.textContaining('*'), findsNothing);
    // ⭐ And the legend goes with it: `CHE (A)` needs none, which is the point.
    expect(find.textContaining('asterisk'), findsNothing);
    expect(find.text('CHE* = away'), findsNothing);
  });

  testWidgets('the squad filter narrows the grid to your clubs', (
    tester,
  ) async {
    final mine = await pumpTicker(tester, myClubs: {'ARS'});
    expect(find.text('My squad'), findsOneWidget);
    expect(find.text('All clubs'), findsOneWidget);

    // ⭐ Off by default: the grid's job is the whole league, and a reader who lands on a filtered view
    // has to notice the filter before they can trust what is missing.
    expect(find.text('ARS'), findsWidgets);
    expect(find.text(mine), findsWidgets, reason: 'another club is missing');

    await tester.tap(find.text('My squad'));
    await tester.pumpAndSettle();
    expect(find.text('ARS'), findsWidgets);
    expect(
      find.text(mine),
      findsNothing,
      reason: '$mine survived a filter that should have removed it',
    );
  });

  testWidgets('a filter that matches nothing says so', (tester) async {
    // ⚠️ *An empty grid with a filter on is indistinguishable from a broken one* — the rule the Players
    // board already follows: name the filter that emptied it.
    await pumpTicker(tester, myClubs: {'NOPE'});
    await tester.tap(find.text('My squad'));
    await tester.pumpAndSettle();
    expect(find.textContaining('None of your clubs'), findsOneWidget);
  });

  testWidgets(
    'no squad means no filter, rather than one that matches nothing',
    (tester) async {
      // ⭐ The honest state before a squad has loaded.
      await pumpTicker(tester);
      expect(find.text('My squad'), findsNothing);
    },
  );
}
