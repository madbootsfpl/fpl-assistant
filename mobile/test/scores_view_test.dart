// The scores screen (ADR-346) — rendered from the committed sample the server actually produced.
//
// ⭐⭐ **Two pairs of states that look alike and mean opposite things**, which is what this file is for:
// `0-0` against *not kicked off*, and an empty `yours` against *we do not know yet*.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/scores_view.dart';

const _sample =
    '../spikes/018-flutter-read-slice/api-samples/gameweek-scores.json';

Map<String, dynamic> sampleJson() =>
    jsonDecode(File(_sample).readAsStringSync()) as Map<String, dynamic>;

/// ⚠️⚠️ **`key` is not decoration.** Pumping a second `ScoresView` of the same type at the same position
/// **reuses the existing State**, so its `late _future` never re-runs and the screen keeps showing the
/// first body — ⭐ *a test that pumps twice and asserts on the second is asserting on the first.* A
/// distinct key forces a fresh State.
Future<void> pumpScores(
  WidgetTester tester, {
  Map<String, dynamic>? body,
  String key = 'scores',
}) async {
  // ⚠️ A tall viewport: a ListView does not build off-screen children, and ten matches run well past a
  // phone's fold — ⭐ *a test that cannot see a widget reports the same failure as one that is not there.*
  tester.view.physicalSize = const Size(500, 2600);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  final payload = jsonEncode(body ?? sampleJson());
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: ScoresView(
          key: ValueKey(key),
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient(
              (_) async => http.Response(
                payload,
                200,
                headers: const {'content-type': 'application/json'},
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('the committed sample carries what this screen is for', () {
    final week = GameweekScores.fromJson(sampleJson());
    expect(week.matches, isNotEmpty);
    expect(
      week.matches.any((m) => m.hasScore),
      isTrue,
      reason: 'a sample with no score cannot exercise the screen',
    );
    expect(
      week.matches.any((m) => m.yours.isNotEmpty),
      isTrue,
      reason: 'the `yours` line is the feature — a sample without one tests nothing',
    );
  });

  testWidgets('a real scoreline renders with the clubs either side', (
    tester,
  ) async {
    await pumpScores(tester);
    final week = GameweekScores.fromJson(sampleJson());
    final played = week.matches.firstWhere((m) => m.hasScore);

    expect(find.text(played.home), findsWidgets);
    expect(find.text(played.away), findsWidgets);
    // ⚠️ An en dash, not a hyphen — the glyph the screen actually draws.
    expect(
      find.text('${played.homeScore}–${played.awayScore}'),
      // ⚠️ `findsWidgets`: two matches in one gameweek can share a scoreline, and the sample
      // has two 3–0s. ⭐ *A uniqueness the data never owed the test.*
      findsWidgets,
    );
  });

  testWidgets('your player is named beside the match, with his points', (
    tester,
  ) async {
    await pumpScores(tester);
    final week = GameweekScores.fromJson(sampleJson());
    final withYours = week.matches.firstWhere((m) => m.yours.isNotEmpty);
    final mine = withYours.yours.first;

    expect(find.textContaining(mine.player!.name), findsWidgets);
    expect(find.text('${mine.points} pts'), findsWidgets);
  });

  testWidgets('a goalless draw prints 0–0 and not a kick-off time', (
    tester,
  ) async {
    // 🔴 **The pair this screen exists to keep apart.** Both matches below are "nothing happened" to a
    // renderer that defaults a missing score to zero — and they are opposite facts.
    final body = {
      'gameweek': 7,
      'live': false,
      'yours_known': true,
      'matches': [
        {
          'fixture': 1,
          'home': 'LEE',
          'away': 'CRY',
          'home_score': 0,
          'away_score': 0,
          'minutes': 90,
          'started': true,
          'finished': true,
          'kickoff_time': '2026-10-17T11:30:00Z',
          'yours': <dynamic>[],
        },
        {
          'fixture': 2,
          'home': 'ARS',
          'away': 'TOT',
          'home_score': null,
          'away_score': null,
          'minutes': null,
          'started': false,
          'finished': false,
          'kickoff_time': '2026-10-17T14:00:00Z',
          'yours': <dynamic>[],
        },
      ],
    };
    await pumpScores(tester, body: body);

    expect(find.text('0–0'), findsOneWidget);
    // ⭐ The unplayed match shows a kick-off time, never a score. ⚠️ Local time, so the digits depend on
    // the machine — the assertion is that a clock is drawn at all, not what it reads.
    expect(find.textContaining(RegExp(r'^\d{2}:\d{2}$')), findsOneWidget);
  });

  testWidgets('a live match says so, and shows the clock', (tester) async {
    final body = {
      'gameweek': 7,
      'live': true,
      'yours_known': false,
      'matches': [
        {
          'fixture': 1,
          'home': 'MUN',
          'away': 'LIV',
          'home_score': 1,
          'away_score': 2,
          'minutes': 63,
          'started': true,
          'finished': false,
          'kickoff_time': '2026-10-17T11:30:00Z',
          'yours': <dynamic>[],
        },
      ],
    };
    await pumpScores(tester, body: body);

    expect(find.text('LIVE'), findsOneWidget);
    expect(find.text('1–2'), findsOneWidget);
    expect(find.text("63'"), findsOneWidget);
  });

  testWidgets('an unknown `yours` says so rather than claiming nobody played', (
    tester,
  ) async {
    // ⚠️⚠️ The second pair. Scores publish before player history does, so an empty `yours` after full
    // time means *we do not know yet* — ⭐ *which is the opposite of "none of your players featured".*
    final match = {
      'fixture': 1,
      'home': 'CHE',
      'away': 'BOU',
      'home_score': 5,
      'away_score': 1,
      'minutes': 90,
      'started': true,
      'finished': true,
      'kickoff_time': '2026-10-10T11:30:00Z',
      'yours': <dynamic>[],
    };
    await pumpScores(
      tester,
      key: 'unknown',
      body: {
        'gameweek': 6,
        'live': false,
        'yours_known': false,
        'matches': [match],
      },
    );
    expect(find.text('your players not in yet'), findsOneWidget);
    expect(find.text('none of yours'), findsNothing);

    await pumpScores(
      tester,
      key: 'known',
      body: {
        'gameweek': 6,
        'live': false,
        'yours_known': true,
        'matches': [match],
      },
    );
    expect(find.text('your players not in yet'), findsNothing);
    expect(find.text('none of yours'), findsOneWidget);
  });

  testWidgets(
    'a season with no matches says so instead of drawing an empty list',
    (tester) async {
      await pumpScores(
        tester,
        body: {
          'gameweek': null,
          'live': false,
          'yours_known': false,
          'matches': <dynamic>[],
        },
      );
      expect(find.text('No matches yet.'), findsOneWidget);
    },
  );
}
