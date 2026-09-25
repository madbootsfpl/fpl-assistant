/// Swiping through the season (ADR-298).
///
/// ⭐⭐⭐ **The index arithmetic is the whole risk here, and it is the reason these exist.** An off-by-one
/// in `page → gameweek` does not throw — it draws the wrong week's team under the right week's heading,
/// which is the one failure this screen cannot survive and the one a smoke test would sail past.
///
/// ⚠️ These also pin what a forward page must *not* show. A bank balance or a deadline countdown under a
/// GW+4 projection is a true number in a place that makes it a false claim.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/season_view.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

/// A client that answers every past week with a fixed, played result.
ServiceClient stubClient({List<String>? asked}) => ServiceClient(
  baseUrl: 'http://x',
  client: MockClient((request) async {
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    asked?.add('${body['gameweek']}');
    return http.Response(
      jsonEncode({
        'gameweek': body['gameweek'],
        'played': true,
        'squad': const [],
        'summary': {'points': 61, 'overall_rank': 250000, 'bench_points': 3},
      }),
      200,
      headers: const {'content-type': 'application/json'},
    );
  }),
);

Widget screen(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: SizedBox(width: 390, height: 760, child: child),
  ),
);

void main() {
  // ── the arithmetic, on its own ────────────────────────────────────────────────

  test('the live pitch is the page the walk opens on', () {
    // ⚠️ GW1 is page 0, so the live page is one less than the gameweek. ⭐ Stated as a *relationship*
    // rather than a pair of numbers, because the relationship is the thing that must hold at GW1 and GW38
    // alike.
    for (final gw in [1, 2, 6, 37, 38]) {
      expect(
        SeasonPages.livePage(gw),
        gw - 1,
        reason: 'GW$gw should sit at page ${gw - 1}',
      );
    }
  });

  test(
    'the walk covers every played week, the live one, five ahead, and the edge',
    () {
      // ⭐ GW6: five pages behind (GW1–5), the live one, GW7–11, and the page that says why it stops = 12.
      expect(SeasonPages.pageCount(6), 12);
      // ⚠️⚠️ **GW1 is the case that breaks naive arithmetic** — nothing behind it, so the walk is the live
      // page, five forward, and the edge. A `pageCount` that returned 0 or a negative here would throw
      // inside `PageView`, and the first week of the season is exactly when the most people look.
      expect(SeasonPages.pageCount(1), 7);
      expect(SeasonPages.livePage(1), 0);
    },
  );

  test('forward reaches exactly five weeks and no further', () {
    // ⚠️ Pinned to the constant *and* to five. If someone widens `kForwardWeeks` the first line still
    // passes — ⭐ the second makes them come here and think about whether the model can stand behind it.
    expect(kForwardWeeks, 5);
    final lastForward = SeasonPages.pageCount(6) - 2;
    expect(
      lastForward + 1,
      11,
      reason: 'GW6 + 5 = GW11 is the last projection',
    );
  });

  // ── what a forward page shows ────────────────────────────────────────────────

  testWidgets('a forward page is about its own week, not the next one', (
    tester,
  ) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: 9,
        ),
      ),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('GW9'), findsOneWidget);
    expect(
      find.text('GW6'),
      findsNothing,
      reason: 'the live week has leaked in',
    );

    // ⭐⭐ The total is that week's, not this week's. Reusing `p.xp` would have printed the same figure on
    // all six pages while the cards underneath changed.
    final live = team.analysis.xi.fold<double>(0, (s, p) => s + p.xp);
    final nine = team.analysis.xi.fold<double>(
      0,
      (s, p) => s + (team.xpAt(p, 9) ?? 0),
    );
    expect(nine, isNot(closeTo(live, 0.05)));
    expect(find.text(nine.toStringAsFixed(1)), findsOneWidget);
  });

  testWidgets('every card on a forward page shows that week, not this one', (
    tester,
  ) async {
    // ⭐⭐⭐ **The gap the header test did not close, found by mutating rather than by reading.** Summing
    // `xpAt` in the header while each card still printed `player.xp` passed every other test here: the
    // total was right and all fifteen numbers under it were the wrong week's. ⚠️ *The header is one number
    // the reader glances at; the cards are the fifteen they actually decide on.*
    final team = sampleTeam();
    final haaland = team.analysis.xi.firstWhere((p) => p.name == 'Haaland');
    expect(haaland.xp, 6.2, reason: 'the sample moved — pick another player');
    expect(team.xpAt(haaland, 9), 7.6);

    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: 9,
        ),
      ),
    );
    expect(
      find.text('7.6'),
      findsWidgets,
      reason: "GW9's projection is missing",
    );
    expect(
      find.text('6.2'),
      findsNothing,
      reason: 'a card is still printing the live week under a GW9 heading',
    );

    // ⚠️⚠️ **And the opponent moves with it.** A GW9 number over a GW6 fixture is the same lie in the
    // other half of the card — ⭐ *the opponent is the thing the projection depends on.*
    final live = team.fixtureAt(haaland, 6)!;
    final nine = team.fixtureAt(haaland, 9)!;
    expect(nine.opponent, isNot(live.opponent), reason: 'the sample moved');
    expect(find.textContaining(nine.opponent), findsWidgets);
  });

  testWidgets('a price is never printed under a projection', (tester) async {
    // ⚠️ Today's price beside a GW+4 number reads as the price *then*, which nobody can know. The live
    // card carries it; this one gives the whole line to the opponent instead.
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: 9,
        ),
      ),
    );
    expect(find.textContaining('£'), findsNothing);
  });

  testWidgets(
    'a forward page drops the deadline, the money and the transfers',
    (tester) async {
      final team = sampleTeam();
      await tester.pumpWidget(
        screen(
          PitchView(
            team: team,
            mode: PitchMode.nextGw,
            onMode: (_) {},
            onTapPlayer: (_) {},
            gameweek: 9,
          ),
        ),
      );
      // ⚠️⚠️ A countdown here would be counting down to a *different* week than the one on screen.
      expect(find.text('projected'), findsOneWidget);
      expect(find.text('In the bank'), findsNothing);
      expect(find.text('Value'), findsNothing);
      expect(find.text('Transfers'), findsNothing);
      // ⭐ And the predicted figure stays, because it is the one number that IS about this page.
      expect(find.text('Predicted'), findsOneWidget);
    },
  );

  testWidgets('a forward page offers no reading it cannot mean', (
    tester,
  ) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: 9,
        ),
      ),
    );
    // ⚠️ "Next 3" from a week that has not happened, and a price that does not vary by week.
    expect(find.text('Next 3'), findsNothing);
    expect(find.text('Price'), findsNothing);
  });

  testWidgets('the live page keeps all of it', (tester) async {
    final team = sampleTeam();
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
        ),
      ),
    );
    // ⭐ The counterpart. Without this, hiding everything on every page would pass the three above.
    expect(find.text('In the bank'), findsOneWidget);
    expect(find.text('Next 3'), findsOneWidget);
    expect(find.text('projected'), findsNothing);
  });

  // ── the walk, end to end ─────────────────────────────────────────────────────

  testWidgets('the walk opens on the live pitch and asks for nothing', (
    tester,
  ) async {
    final asked = <String>[];
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(asked: asked),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('GW6'), findsOneWidget);
    // ⚠️⚠️ **No prefetch.** In October that would be nine round trips in front of a screen whose first
    // job is to draw today's team — ⭐ *a swipe is the cheapest possible trigger, and it is the user's.*
    expect(
      asked,
      isEmpty,
      reason: 'arriving fetched ${asked.length} past weeks nobody looked at',
    );
  });

  testWidgets('swiping back asks for the week behind, and only that one', (
    tester,
  ) async {
    final asked = <String>[];
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(asked: asked),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(PageView), const Offset(360, 0));
    await tester.pumpAndSettle();

    // ⭐ GW6 live → one page back is GW5. An off-by-one shows GW4's result under GW5's heading.
    expect(asked, ['5'], reason: 'asked for $asked');
    expect(find.text('61'), findsOneWidget, reason: "GW5's points");
    expect(find.text('250,000'), findsOneWidget, reason: 'the rank, grouped');
  });

  testWidgets('swiping forward projects, and never asks the server', (
    tester,
  ) async {
    final asked = <String>[];
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(asked: asked),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(PageView), const Offset(-360, 0));
    await tester.pumpAndSettle();

    expect(find.text('GW7'), findsOneWidget);
    // ⭐⭐ The forward pages are free: `run_xp` already carried five weeks when the pitch loaded.
    expect(asked, isEmpty, reason: 'a projection cost a round trip: $asked');
  });

  testWidgets('the last forward page is followed by the reason it stops', (
    tester,
  ) async {
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    // GW6 → six swipes forward: GW7, 8, 9, 10, 11, then the edge.
    for (var i = 0; i < kForwardWeeks + 1; i++) {
      await tester.drag(find.byType(PageView), const Offset(-360, 0));
      await tester.pumpAndSettle();
    }
    // ⚠️⚠️ **A boundary with no explanation reads as a bug**, and this page is the most honest thing on
    // the screen. ⭐ The eleventh week is the last one with a number on it.
    expect(find.textContaining('as far as we will guess'), findsOneWidget);
    expect(find.text('GW12'), findsNothing);
  });

  testWidgets('the footer belongs to the live page alone', (tester) async {
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
          footer: const Text('APPLY-ME'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('APPLY-ME'), findsOneWidget);
    await tester.drag(find.byType(PageView), const Offset(-360, 0));
    await tester.pumpAndSettle();
    // ⚠️ Offering to apply a plan under GW7 is offering to act on a week you cannot act on yet; under a
    // past week it would be offering to change the past.
    expect(find.text('APPLY-ME'), findsNothing);
  });

  // ── the last page has numbers on it ──────────────────────────────────────────

  testWidgets('the fifth forward page is not a page of dashes', (tester) async {
    // ⚠️⚠️⚠️ **The bug, and how it was found.** A surviving mutant — "a missing projection becomes 0.0" —
    // said no test cared about a missing projection. Chasing why led here: the service sent five weeks and
    // the app walked five pages *past* the live one, so GW11 had no data at all. ⭐ *A window includes the
    // week you are standing on*, and the escaping mutant was the only thing that said so.
    final team = sampleTeam();
    final live = team.gameweek!;
    final last = live + kForwardWeeks;
    for (final p in team.analysis.xi) {
      expect(
        team.xpAt(p, last),
        isNotNull,
        reason:
            '${p.name} has no projection for GW$last — the swipe reaches it and '
            'the service is sending one week too few',
      );
    }

    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: last,
        ),
      ),
    );
    expect(find.text('GW$last'), findsOneWidget);
    // ⭐ A page of dashes has a zero total, and that is the cheapest possible check that it is not one.
    final total = team.analysis.xi.fold<double>(
      0,
      (s, p) => s + (team.xpAt(p, last) ?? 0),
    );
    expect(total, greaterThan(10));
    expect(find.text(total.toStringAsFixed(1)), findsOneWidget);
    expect(find.text('—'), findsNothing, reason: 'a card has nothing to say');
  });

  testWidgets('a week with no projection says so rather than guessing zero', (
    tester,
  ) async {
    // ⭐⭐ **Zero is a prediction; absence is the absence of one.** A card reading 0.0 claims the engine
    // expects nothing from him; a dash says the engine was not asked. ⚠️ *The two are opposite claims and
    // only one of them is true here* — this is the case an older server, or a blank gameweek, produces.
    final team = sampleTeam();
    final beyond = team.gameweek! + kForwardWeeks + 4;
    await tester.pumpWidget(
      screen(
        PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: beyond,
        ),
      ),
    );
    expect(find.text('—'), findsWidgets);
    expect(find.text('0.0'), findsNothing);
    // ⚠️ And it says there is no fixture, rather than borrowing another week's opponent.
    expect(find.text('no fixture'), findsWidgets);
  });

  testWidgets(
    'leaving the pitch and coming back returns you to the live week',
    (tester) async {
      // ⚠️⚠️ **The page index lives in `SeasonPages`, which the tab switch rebuilds.** ⭐ That is the wanted
      // behaviour and it is worth pinning rather than leaving to chance: a manager who wandered back to GW2,
      // opened Signals, and returned should be looking at *this* week — *the pitch's job is today, and a
      // screen that reopens four weeks in the past has quietly changed what it is for.*
      //
      // ⚠️ It is also the opposite choice from `PitchMode`, which is held in the screen above precisely so
      // it *does* survive. The difference: a mode is a preference, a page is a place you walked to.
      Widget walk() => screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      );

      await tester.pumpWidget(walk());
      await tester.pumpAndSettle();
      await tester.drag(find.byType(PageView), const Offset(-360, 0));
      await tester.pumpAndSettle();
      expect(find.text('GW7'), findsOneWidget);

      // A different screen, then back — what a tab switch does.
      await tester.pumpWidget(screen(const Text('SIGNALS')));
      await tester.pumpAndSettle();
      await tester.pumpWidget(walk());
      await tester.pumpAndSettle();
      expect(find.text('GW6'), findsOneWidget);
      expect(
        find.text('In the bank'),
        findsOneWidget,
        reason: 'not the live pitch',
      );
    },
  );

  testWidgets('a past week is fetched once, however often you swipe over it', (
    tester,
  ) async {
    // ⭐ The client caches a settled week, and the page holds the future rather than rebuilding it — ⚠️ *a
    // `FutureBuilder` handed a fresh future on every rebuild re-fetches on every frame of the swipe
    // animation*, which is the classic way this widget is got wrong.
    final asked = <String>[];
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(asked: asked),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    for (var i = 0; i < 3; i++) {
      await tester.drag(find.byType(PageView), const Offset(360, 0));
      await tester.pumpAndSettle();
      await tester.drag(find.byType(PageView), const Offset(-360, 0));
      await tester.pumpAndSettle();
    }
    expect(asked, [
      '5',
    ], reason: 'GW5 was fetched ${asked.length} times: $asked');
  });

  // ── which week am I looking at ───────────────────────────────────────────────

  testWidgets('every page in the walk names its own gameweek', (tester) async {
    // ⚠️⚠️⚠️ **The defect a device found and every test here missed.** All sixteen tests above passed
    // while the past pages carried no gameweek at all: the points were right, the rank was right, and
    // after four swipes you had no way of knowing which week you were reading. ⭐ *A screen whose entire
    // purpose is "which week is this?" has to answer it, and the tests were all checking the answers to
    // other questions.*
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('GW6'), findsOneWidget, reason: 'the live page');

    await tester.drag(find.byType(PageView), const Offset(360, 0));
    await tester.pumpAndSettle();
    expect(find.text('GW5'), findsOneWidget, reason: 'a past page');
    // ⭐ And it says what kind of number it is showing, in the same shape as 'projected'.
    expect(find.text('final'), findsOneWidget);

    await tester.drag(find.byType(PageView), const Offset(-720, 0));
    await tester.pumpAndSettle();
    expect(find.text('GW7'), findsOneWidget, reason: 'a forward page');
    expect(find.text('projected'), findsOneWidget);
  });

  testWidgets(
    'a week still being played says which week, and that it is not done',
    (tester) async {
      // ⭐ The state the app spends every Saturday in. ⚠️ *"This gameweek has not been played yet" with no
      // gameweek on it is the same omission in a shorter sentence.*
      final client = ServiceClient(
        baseUrl: 'http://x',
        client: MockClient(
          (request) async => http.Response(
            jsonEncode({
              'gameweek': 5,
              'played': false,
              'squad': const [],
              'summary': const {},
            }),
            200,
            headers: const {'content-type': 'application/json'},
          ),
        ),
      );
      await tester.pumpWidget(
        screen(
          SeasonPages(
            team: sampleTeam(),
            client: client,
            mode: PitchMode.nextGw,
            onMode: (_) {},
            onTapPlayer: (_, _, _) {},
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.drag(find.byType(PageView), const Offset(360, 0));
      await tester.pumpAndSettle();
      expect(find.text('GW5'), findsOneWidget);
      expect(find.text('not played yet'), findsOneWidget);
      expect(find.textContaining('has not been played yet'), findsOneWidget);
    },
  );

  testWidgets('a week the server did not name is a dash, never GW0', (
    tester,
  ) async {
    // ⚠️ Reachable only from an older server that omits `gameweek` — ⭐ *and "GW0" is a week that does not
    // exist, which is a worse answer than admitting we were not told.* The same rule `bank` and `value`
    // already follow on the pitch above.
    final client = ServiceClient(
      baseUrl: 'http://x',
      client: MockClient(
        (request) async => http.Response(
          jsonEncode({'played': false, 'squad': const [], 'summary': const {}}),
          200,
          headers: const {'content-type': 'application/json'},
        ),
      ),
    );
    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: client,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(PageView), const Offset(360, 0));
    await tester.pumpAndSettle();
    expect(find.text('GW—'), findsOneWidget);
    expect(find.text('GW0'), findsNothing);
  });

  testWidgets('the live week is framed and no other week is', (tester) async {
    // ⭐⭐ Owner: *"as I scroll left and right, I wonder could we have a purple border around current GW
    // so it stands out."* ⚠️ *The question a swipe takes away is not "which week is this?" — every page
    // says that — but "how far have I wandered?"*, and a border answers it from the corner of the eye.
    Iterable<Container> framed() => tester
        .widgetList<Container>(find.byType(Container))
        .where(
          (c) =>
              (c.decoration as BoxDecoration?)?.border != null &&
              ((c.decoration as BoxDecoration?)!.border! as Border)
                      .top
                      .color
                      .a >
                  0.5 &&
              ((c.decoration as BoxDecoration?)!.border! as Border).top.width ==
                  2,
        );

    await tester.pumpWidget(
      screen(
        SeasonPages(
          team: sampleTeam(),
          client: stubClient(),
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_, _, _) {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(framed(), hasLength(1), reason: 'the live week is not framed');

    // ⚠️ And the frame does not travel with you — that would make it decoration rather than a landmark.
    await tester.drag(find.byType(PageView), const Offset(-360, 0));
    await tester.pumpAndSettle();
    expect(framed(), isEmpty, reason: 'GW7 is wearing the live week\'s frame');

    await tester.drag(find.byType(PageView), const Offset(360, 0));
    await tester.pumpAndSettle();
    expect(framed(), hasLength(1), reason: 'the frame did not come back');
  });
}
