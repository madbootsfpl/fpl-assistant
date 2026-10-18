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
    // ⭐ ADR-360's additions, asserted here so a sample regenerated without them fails loudly rather
    // than quietly rendering an empty dropdown.
    expect(
      week.people,
      isNotEmpty,
      reason: 'no `people` sidecar — every name would draw as a dash',
    );
    expect(week.matches.any((m) => m.events.goals.isNotEmpty), isTrue);
    expect(week.matches.any((m) => m.events.cards.isNotEmpty), isTrue);
    expect(week.matches.any((m) => m.bonusRace.isNotEmpty), isTrue);
  });

  testWidgets('the scoreline carries both clubs and the state', (tester) async {
    await pumpScores(tester);
    expect(find.text('3 – 0'), findsWidgets);
    expect(find.text('BRE'), findsOneWidget);
    expect(find.text('CHE'), findsOneWidget);
    expect(find.text('Full time'), findsWidgets);
  });

  testWidgets(
    'the scorers are on the closed card, so the result reads at a glance',
    (tester) async {
      // ⭐⭐ This is A-the-summary from the owner's chosen combination: the score, the state and who
      // scored, with nothing to tap for the result itself.
      await pumpScores(tester);
      expect(find.text('Carvalho'), findsOneWidget);
      expect(find.text('Anthony'), findsOneWidget);
      expect(find.text('Thiago'), findsWidgets);
    },
  );

  testWidgets('assists are listed, and never attached to a goal', (
    tester,
  ) async {
    // ⚠️⚠️ **FPL links a goal to no assist.** Brentford scored three and two men assisted; which set up
    // which is not in the data. ⭐⭐ *Pairing two sorted lists is the ADR-351 mistake*, so no rendered
    // string may contain a scorer and an assister together.
    await pumpScores(tester);
    expect(find.text('Schuster'), findsOneWidget);
    expect(find.text('Schade'), findsOneWidget);

    final texts = tester
        .widgetList<Text>(find.byType(Text))
        .map((t) => t.data ?? '')
        .toList();
    for (final line in texts) {
      final pairing = line.contains('Carvalho') && line.contains('Schuster');
      expect(
        pairing,
        isFalse,
        reason: 'a goal was printed as if it had an assist: "$line"',
      );
    }
  });

  testWidgets('the dropdown is shut until it is asked for', (tester) async {
    await pumpScores(tester);
    // ⭐ Cards, the bonus race and the per-player lines all live behind the chevron.
    expect(find.text('CARDS'), findsNothing);
    expect(find.text('BONUS RACE'), findsNothing);
    expect(find.text('This match'), findsNothing);
    expect(find.byIcon(Icons.expand_more), findsWidgets);
  });

  testWidgets('tapping a match opens one dropdown with everything else in it', (
    tester,
  ) async {
    await pumpScores(tester);
    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();

    expect(find.text('CARDS'), findsOneWidget);
    expect(find.text('YOUR PLAYERS'), findsOneWidget);
    expect(find.text('This match'), findsOneWidget);
    expect(find.text('BONUS RACE'), findsOneWidget);
    // ⚠️ One card open, not all ten: ⭐ *a tap that expands the whole list is a different gesture.*
    expect(find.byIcon(Icons.expand_less), findsOneWidget);
  });

  testWidgets('nothing is said twice between the summary and the dropdown', (
    tester,
  ) async {
    // 🔴 The owner's verdict on the first rebuild of this screen was *"its duplicated and not well laid
    // out"*. ⭐ The scorers belong to the summary; the dropdown holds only what the summary does not say.
    await pumpScores(tester);
    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();

    expect(
      find.text('Carvalho'),
      findsOneWidget,
      reason: 'the scorer is printed in both halves',
    );
  });

  testWidgets('a goalless draw prints 0–0 and not a kick-off time', (
    tester,
  ) async {
    final body = sampleJson();
    final m = (body['matches'] as List).first as Map<String, dynamic>;
    m['home_score'] = 0;
    m['away_score'] = 0;
    m['started'] = true;
    m['finished'] = true;
    m['status'] = 'Full time';
    await pumpScores(tester, body: body, key: 'goalless');

    // ⚠️ `findsWidgets`: the sample holds another goalless match of its own, and ⭐ *a count that depends
    // on the rest of the fixture breaks the day the fixture is regenerated.*
    expect(find.text('0 – 0'), findsWidgets);
  });

  testWidgets('a match that has not kicked off shows when it will', (
    tester,
  ) async {
    final body = sampleJson();
    for (final m in (body['matches'] as List).cast<Map<String, dynamic>>()) {
      m['home_score'] = null;
      m['away_score'] = null;
      m['started'] = false;
      m['finished'] = false;
      m['status'] = '';
      m['events'] = {'goals': [], 'assists': [], 'cards': []};
      m['bonus_race'] = [];
    }
    await pumpScores(tester, body: body, key: 'future');

    // ⚠️⚠️ **Never `0 – 0`** — ⭐ *a goalless draw and a match not yet played are opposite facts.*
    expect(find.text('0 – 0'), findsNothing);
    expect(find.text('v'), findsWidgets);
  });

  testWidgets('a future week names who of yours is involved', (tester) async {
    // ⭐ `yours` is built from history, which does not exist before a match, so the server falls back to
    // team membership and sends the counters as null (ADR-360).
    final body = sampleJson();
    final m = (body['matches'] as List).first as Map<String, dynamic>;
    m['home_score'] = null;
    m['away_score'] = null;
    m['started'] = false;
    m['status'] = '';
    m['events'] = {'goals': [], 'assists': [], 'cards': []};
    m['bonus_race'] = [];
    m['yours'] = [
      {
        'player': {
          'id': 1,
          'web_name': 'Petrovic',
          'team': 'BRE',
          'position': 'GK',
          'price': 4.5,
          'xp': 3.0,
          'status': 'a',
          'chance': null,
          'minutes_weight': 1.0,
          'leaving': null,
          'by_gameweek': <String, dynamic>{},
        },
        'minutes': null,
        'goals': null,
        'assists': null,
        'points': null,
        'bonus': null,
      },
    ];
    await pumpScores(tester, body: body, key: 'lining');

    expect(find.textContaining('Yours: Petrovic'), findsOneWidget);
    // ⚠️ No points: ⭐ *a nil return and a match not yet played must not look alike.*
    expect(find.text('0 pts'), findsNothing);
  });

  testWidgets('a live match says so, and shows the clock', (tester) async {
    final body = sampleJson();
    body['live'] = true;
    final m = (body['matches'] as List).first as Map<String, dynamic>;
    m['started'] = true;
    m['finished'] = false;
    m['status'] = "63'";
    await pumpScores(tester, body: body, key: 'live');

    expect(find.text('LIVE'), findsOneWidget);
    expect(find.text("63'"), findsOneWidget);
  });

  testWidgets('an unknown `yours` says so rather than claiming nobody played', (
    tester,
  ) async {
    final body = sampleJson();
    body['yours_known'] = false;
    await pumpScores(tester, body: body, key: 'unknown');

    expect(find.text('your players not in yet'), findsOneWidget);
  });

  testWidgets('one point is a point, not "1 pts"', (tester) async {
    final body = sampleJson();
    for (final m in (body['matches'] as List).cast<Map<String, dynamic>>()) {
      final yours = (m['yours'] as List).cast<Map<String, dynamic>>();
      for (var i = 0; i < yours.length; i++) {
        yours[i]['points'] = i == 0 ? 1 : 0;
      }
    }
    await pumpScores(tester, body: body, key: 'onept');
    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();

    expect(find.text('1 pt'), findsOneWidget);
    expect(find.text('1 pts'), findsNothing);
  });

  testWidgets('a sending off is drawn red, a booking yellow', (tester) async {
    await pumpScores(tester);
    // EVE-IPS carries the sample's one red card.
    final chevrons = find.byIcon(Icons.expand_more);
    await tester.tap(chevrons.at(3));
    await tester.pumpAndSettle();

    expect(find.text('Fatawu'), findsWidgets);
  });

  group('the week bar (ADR-360)', () {
    testWidgets('it names the week and offers both directions', (tester) async {
      await pumpScores(tester);
      expect(find.text('Gameweek 5'), findsOneWidget);
      expect(find.byIcon(Icons.chevron_left), findsOneWidget);
      expect(find.byIcon(Icons.chevron_right), findsOneWidget);
    });

    testWidgets('it asks the server for the week it moved to', (tester) async {
      // ⭐ The bar is the whole feature: a label that changes without re-fetching is decoration.
      final asked = <int>[];
      tester.view.physicalSize = const Size(500, 2600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ScoresView(
              client: ServiceClient(
                baseUrl: 'http://x',
                client: MockClient((req) async {
                  final sent = jsonDecode(req.body) as Map<String, dynamic>;
                  asked.add((sent['gameweek'] as num).toInt());
                  return http.Response(
                    jsonEncode(sampleJson()),
                    200,
                    headers: const {'content-type': 'application/json'},
                  );
                }),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(asked, [
        0,
      ], reason: 'the first load must let the server choose the week');

      await tester.tap(find.byIcon(Icons.chevron_left));
      await tester.pumpAndSettle();
      expect(asked, [
        0,
        4,
      ], reason: 'going back did not ask for the previous week');
    });

    testWidgets('it will not go back past the first week', (tester) async {
      final body = sampleJson();
      body['gameweek'] = 1;
      await pumpScores(tester, body: body, key: 'first');

      final back = tester.widget<IconButton>(
        find.ancestor(
          of: find.byIcon(Icons.chevron_left),
          matching: find.byType(IconButton),
        ),
      );
      expect(back.onPressed, isNull, reason: 'there is no gameweek zero');
    });

    testWidgets('forward stops at the house horizon, not at GW38', (
      tester,
    ) async {
      // ⚠️⚠️ **All 380 fixtures are scheduled**, so forwards could run thirty-one weeks — but *"which of
      // your players are in it"* uses the squad held today. ⭐ Five is the number `analyse`, `board`,
      // `dead_slot` and `explain` already use.
      //
      // ⚠️ The server is mocked to **echo the week it was asked for**: the anchor comes from the first
      // answer, so a mock that always replies "gameweek 5" can never walk the bar anywhere — ⭐ *the
      // first version of this test set the week in the body and proved nothing.*
      tester.view.physicalSize = const Size(500, 2600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ScoresView(
              client: ServiceClient(
                baseUrl: 'http://x',
                client: MockClient((req) async {
                  final sent = jsonDecode(req.body) as Map<String, dynamic>;
                  final asked = (sent['gameweek'] as num).toInt();
                  final body = sampleJson();
                  if (asked > 0) body['gameweek'] = asked;
                  return http.Response(
                    jsonEncode(body),
                    200,
                    headers: const {'content-type': 'application/json'},
                  );
                }),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Gameweek 5'), findsOneWidget);

      IconButton forward() => tester.widget<IconButton>(
        find.ancestor(
          of: find.byIcon(Icons.chevron_right),
          matching: find.byType(IconButton),
        ),
      );

      for (var i = 0; i < kForwardWeeks; i++) {
        expect(
          forward().onPressed,
          isNotNull,
          reason: 'stopped short at step $i',
        );
        await tester.tap(find.byIcon(Icons.chevron_right));
        await tester.pumpAndSettle();
      }

      expect(find.text('Gameweek ${5 + kForwardWeeks}'), findsOneWidget);
      expect(
        forward().onPressed,
        isNull,
        reason: 'the bar ran past the horizon it anchored on',
      );
    });
  });

  testWidgets('an early week says why it has no highlights', (tester) async {
    // 🔴 GW1–GW5 pre-date ADR-357 and their videos are gone for good. ⚠️ *A silent gap reads as a bug.*
    final body = sampleJson();
    body['gameweek'] = 3;
    await pumpScores(tester, body: body, key: 'early');

    expect(find.textContaining('No highlights this far back'), findsOneWidget);
  });

  testWidgets(
    'a recent week does not apologise for highlights it may still get',
    (tester) async {
      final body = sampleJson();
      body['gameweek'] = kFirstWeekWithHighlights;
      await pumpScores(tester, body: body, key: 'recent');

      expect(find.textContaining('No highlights this far back'), findsNothing);
    },
  );

  group('the owner\'s build-46 notes (ADR-362)', () {
    testWidgets('a scorer of yours is dotted even before the backfill lands', (
      tester,
    ) async {
      // 🔴 **GW7 had no dots at all.** They were derived from `yours`, which waits for `player_history`,
      // and the week being played has none — ⭐ *the dot marked the data source, not the squad.*
      final body = sampleJson();
      final first = (body['matches'] as List).first as Map<String, dynamic>;
      final scorer =
          ((first['events'] as Map)['goals'] as List).first
              as Map<String, dynamic>;
      body['squad'] = [scorer['player']];
      for (final m in (body['matches'] as List).cast<Map<String, dynamic>>()) {
        m['yours'] = <dynamic>[];
      }
      await pumpScores(tester, body: body, key: 'dots');

      // ⭐ The dot is drawn beside the scorer; with `yours` empty there is nothing else it could be.
      expect(find.byType(ScoresView), findsOneWidget);
      final dots = find.byWidgetPredicate((w) {
        if (w is! Container) return false;
        final d = w.decoration;
        return d is BoxDecoration &&
            d.shape == BoxShape.circle &&
            d.color == const Color(0xFFB45CF0);
      });
      expect(
        dots,
        findsWidgets,
        reason: 'no purple dot was drawn for a squad member who scored',
      );
    });

    testWidgets('nobody in the squad means nobody is dotted', (tester) async {
      // ⚠️ The guard on the other side: ⭐ *a dot on every name marks nothing at all.*
      final body = sampleJson();
      body['squad'] = <dynamic>[];
      for (final m in (body['matches'] as List).cast<Map<String, dynamic>>()) {
        m['yours'] = <dynamic>[];
      }
      await pumpScores(tester, body: body, key: 'nodots');

      final dots = find.byWidgetPredicate((w) {
        if (w is! Container) return false;
        final d = w.decoration;
        return d is BoxDecoration &&
            d.shape == BoxShape.circle &&
            d.color == const Color(0xFFB45CF0);
      });
      expect(dots, findsNothing);
    });

    testWidgets('the bonus race says its right-hand column is BPS', (
      tester,
    ) async {
      // ⚠️ The owner: *"dont know what the Bonus Race scores on the right hand mean, eg Neto 64?"*
      // ⭐ *A number with no unit is a number the reader has to guess at.*
      await pumpScores(tester);
      await tester.tap(find.byIcon(Icons.expand_more).first);
      await tester.pumpAndSettle();

      expect(find.text('BPS'), findsOneWidget);
    });

    testWidgets('cards are split by club, like the scoreline above them', (
      tester,
    ) async {
      // ⭐ One run of chips makes the reader match each name to a club from memory — the work this card
      // exists to save.
      //
      // ⚠️⚠️ **Counted, not shaped.** The first version looked for a `Wrap` inside a `Row` and passed
      // happily with **every card in both columns** — ⭐ *a layout assertion that cannot tell right from
      // doubled.* Each booking belongs to one side, so the chips must equal the cards.
      final body = sampleJson();
      final first = (body['matches'] as List).first as Map<String, dynamic>;
      final cards = ((first['events'] as Map)['cards'] as List).length;
      expect(
        cards,
        greaterThan(1),
        reason: 'a one-card match cannot show a split',
      );

      await pumpScores(tester);
      await tester.tap(find.byIcon(Icons.expand_more).first);
      await tester.pumpAndSettle();

      final chips = tester.widgetList<Container>(find.byType(Container)).where((
        c,
      ) {
        final d = c.decoration;
        if (d is! BoxDecoration) return false;
        return d.borderRadius == BorderRadius.circular(6);
      }).length;
      expect(
        chips,
        cards,
        reason: 'the cards were doubled across both columns, not split between them',
      );
    });
  });

  group('a finished match is not finished points (ADR-363)', () {
    Future<void> pumpWithStatus(
      WidgetTester tester,
      String status,
      String key,
    ) async {
      final body = sampleJson();
      for (final m in (body['matches'] as List).cast<Map<String, dynamic>>()) {
        m['bonus_status'] = status;
      }
      await pumpScores(tester, body: body, key: key);
      await tester.tap(find.byIcon(Icons.expand_more).first);
      await tester.pumpAndSettle();
    }

    testWidgets('full time with no award yet says the bonus is still to come', (
      tester,
    ) async {
      // ⭐⭐ The state the card could not say before: the whistle has gone, the score is final, and the
      // 3-2-1 has not been given out.
      await pumpWithStatus(tester, 'pending', 'pending');
      expect(find.text('bonus to come'), findsOneWidget);
      expect(
        find.text('Full time'),
        findsWidgets,
        reason: 'the football is over either way',
      );
    });

    testWidgets('an awarded but unlocked week says provisional', (
      tester,
    ) async {
      await pumpWithStatus(tester, 'provisional', 'prov');
      expect(find.text('provisional'), findsOneWidget);
    });

    testWidgets('a match still running says live', (tester) async {
      await pumpWithStatus(tester, 'live', 'livebonus');
      expect(find.text('live'), findsOneWidget);
    });

    testWidgets('a locked week says nothing at all', (tester) async {
      // ⚠️ *A label on every state is a label nobody reads* — once the week is settled there is nothing
      // to warn about, so the chip goes.
      await pumpWithStatus(tester, 'final', 'finalbonus');
      expect(find.text('provisional'), findsNothing);
      expect(find.text('bonus to come'), findsNothing);
      expect(find.text('live'), findsNothing);
      // ⭐ and the race itself is still there
      expect(find.text('BONUS RACE'), findsOneWidget);
    });
  });
}
