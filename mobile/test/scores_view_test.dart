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

    // ⭐ The card names clubs in full now — "Brentford", not "BRE". The short code is the key into the
    // `clubs` sidecar, never what a reader sees.
    expect(find.text(week.club(played.home).name), findsWidgets);
    expect(find.text(week.club(played.away).name), findsWidgets);
    // ⚠️ An en dash, not a hyphen — the glyph the screen actually draws.
    expect(
      find.text('${played.homeScore} – ${played.awayScore}'),
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
      'clubs': <String, dynamic>{},
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

    expect(find.text('0 – 0'), findsOneWidget);
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
          // ⚠️ `status` comes from the server now (ADR-346) — three clients deriving "is it over?"
          // separately is three chances to disagree. A body without it shows no clock, correctly.
          'status': "63'",
          'kickoff_time': '2026-10-17T11:30:00Z',
          'yours': <dynamic>[],
        },
      ],
    };
    await pumpScores(tester, body: body);

    expect(find.text('LIVE'), findsOneWidget);
    expect(find.text('1 – 2'), findsOneWidget);
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
        'clubs': <String, dynamic>{},
        'live': false,
        'yours_known': false,
        'matches': [match],
      },
    );
    expect(find.text('your players not in yet'), findsOneWidget);

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
  });

  testWidgets('your player sits under the club he played for', (tester) async {
    // ⭐⭐ **The point of the layout the owner asked for.** A name under a scoreline does not say who he
    // was playing *for*; a name under a crest does. The sample has one of yours on each side of
    // Brentford–Chelsea, which is the case that looks fine under either arrangement and only reads
    // correctly under this one.
    await pumpScores(tester);
    final week = GameweekScores.fromJson(sampleJson());
    final both = week.matches.firstWhere(
      (m) =>
          m.yours.any((a) => a.player?.team == m.home) &&
          m.yours.any((a) => a.player?.team == m.away),
      orElse: () => week.matches.firstWhere((m) => m.yours.isNotEmpty),
    );

    for (final a in both.yours) {
      final line = find.textContaining(a.player!.name);
      expect(line, findsWidgets, reason: '${a.player!.name} is not named');

      // ⚠️ Horizontal position is what attaches him to a club: home is drawn left of the scoreline,
      // away right of it.
      final x = tester.getCenter(line.first).dx;
      final score = tester
          .getCenter(find.textContaining(RegExp(r'^\d+ – \d+$')).first)
          .dx;
      final atHome = a.player!.team == both.home;
      expect(
        atHome ? x < score : x > score,
        isTrue,
        reason:
            '${a.player!.name} plays for ${a.player!.team} but is drawn on the '
            'wrong side of ${both.home}-${both.away}',
      );
    }
  });

  testWidgets('the card totals what the match did to your team', (
    tester,
  ) async {
    // ⚠️⚠️ **A hand-built body, because the sample cannot catch the bug.** Its one scoring match has
    // 9 pts and 0 pts, so "the first player's points" and "the sum" are the same number — ⭐ *a mutation
    // that replaced the sum with the first survived the version of this test that used the sample.*
    // Two scorers, both non-zero, and the total matches neither on its own.
    Map<String, dynamic> player(String name, String team) => {
      'id': name.hashCode,
      'web_name': name,
      'team': team,
      'position': 'MID',
      'price': 7.0,
      'xp': 4.0,
      'status': 'a',
      'chance': null,
      'minutes_weight': 1.0,
      'leaving': null,
      'by_gameweek': <String, dynamic>{},
    };
    await pumpScores(
      tester,
      key: 'impact',
      body: {
        'gameweek': 6,
        'live': false,
        'yours_known': true,
        'clubs': {
          'CHE': {'name': 'Chelsea', 'badge': ''},
          'BOU': {'name': 'Bournemouth', 'badge': ''},
        },
        'matches': [
          {
            'fixture': 1,
            'home': 'CHE',
            'away': 'BOU',
            'home_score': 5,
            'away_score': 1,
            'minutes': 90,
            'started': true,
            'finished': true,
            'status': 'Full time',
            'kickoff_time': '2026-10-10T11:30:00Z',
            'yours': [
              {
                'player': player('João Pedro', 'CHE'),
                'minutes': 90,
                'goals': 2,
                'assists': 0,
                'points': 13,
                'bonus': 3,
              },
              {
                'player': player('Semenyo', 'BOU'),
                'minutes': 90,
                'goals': 1,
                'assists': 0,
                'points': 6,
                'bonus': 0,
              },
            ],
          },
        ],
      },
    );

    expect(
      find.text('19 pts'),
      findsOneWidget,
      reason: '13 + 6, not either alone',
    );
    expect(find.text('13 pts'), findsNothing);
    // ⭐ "in this match", never "gameweek total": `player_history` is keyed by fixture, so these points
    // were earned here — ⚠️ *the mock-up this came from footnoted the opposite because its source could
    // not make that claim.*
    expect(find.text('this match'), findsOneWidget);
  });

  testWidgets('a name appears once, and carries no "Your player" tag', (
    tester,
  ) async {
    // 🔴 **The two faults the owner reported, pinned.** The card listed your players under the clubs and
    // again in a "Your fantasy impact" row — the same names, no new fact — and tagged each one
    // "· Your player", which is true of everything in the block and so says nothing. ⭐⭐ *Together they
    // cost the width that truncated the names themselves:* "João Pedro · Your pl…".
    await pumpScores(tester);
    final week = GameweekScores.fromJson(sampleJson());
    final m = week.matches.firstWhere((x) => x.yours.isNotEmpty);

    expect(find.textContaining('Your player'), findsNothing);
    for (final a in m.yours) {
      expect(
        find.textContaining(a.player!.name),
        findsOneWidget,
        reason: '${a.player!.name} is drawn more than once',
      );
    }
  });

  testWidgets('a match with none of yours is just a scoreline', (tester) async {
    // ⭐ No divider, no total, no "none of yours" — ⚠️ *a card that explains its own emptiness is a card
    // spending four lines to say nothing happened.*
    await pumpScores(
      tester,
      key: 'empty',
      body: {
        'gameweek': 6,
        'live': false,
        'yours_known': true,
        'clubs': {
          'AVL': {'name': 'Aston Villa', 'badge': ''},
          'BRE': {'name': 'Brentford', 'badge': ''},
        },
        'matches': [
          {
            'fixture': 1,
            'home': 'AVL',
            'away': 'BRE',
            'home_score': 2,
            'away_score': 2,
            'minutes': 90,
            'started': true,
            'finished': true,
            'status': 'Full time',
            'kickoff_time': '2026-10-10T11:30:00Z',
            'yours': <dynamic>[],
          },
        ],
      },
    );
    expect(find.text('2 – 2'), findsOneWidget);
    expect(find.text('none of yours'), findsNothing);
    expect(find.textContaining('this match'), findsNothing);
  });

  testWidgets('one point is a point, not "1 pts"', (tester) async {
    Map<String, dynamic> player(String name, String team) => {
      'id': 1,
      'web_name': name,
      'team': team,
      'position': 'DEF',
      'price': 4.5,
      'xp': 2.0,
      'status': 'a',
      'chance': null,
      'minutes_weight': 1.0,
      'leaving': null,
      'by_gameweek': <String, dynamic>{},
    };
    await pumpScores(
      tester,
      key: 'onept',
      body: {
        'gameweek': 6,
        'live': false,
        'yours_known': true,
        'clubs': {
          'HUL': {'name': 'Hull City', 'badge': ''},
          'EVE': {'name': 'Everton', 'badge': ''},
        },
        'matches': [
          {
            'fixture': 1,
            'home': 'HUL',
            'away': 'EVE',
            'home_score': 2,
            'away_score': 2,
            'minutes': 90,
            'started': true,
            'finished': true,
            'status': 'Full time',
            'kickoff_time': '2026-10-10T11:30:00Z',
            'yours': [
              {
                'player': player('Egan', 'HUL'),
                'minutes': 12,
                'goals': 0,
                'assists': 0,
                'points': 1,
                'bonus': 0,
              },
            ],
          },
        ],
      },
    );
    expect(find.text('1 pt'), findsOneWidget);
    expect(find.text('1 pts'), findsNothing);
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
