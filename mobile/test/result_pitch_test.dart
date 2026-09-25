/// A played gameweek is a pitch (ADR-298, after feedback).
///
/// ⭐⭐⭐ **These exist because twenty passing tests did not notice the screen was the wrong shape.** The
/// first build drew a played week as a list; every test asserted the numbers on it and every one of them
/// passed. The owner's reply was one sentence: *"the right swipe into history shows a list rather than a
/// pitch layout."*
///
/// ⚠️ *A test that checks the values a screen shows cannot tell you the screen is the wrong screen.* So
/// these assert the shape first — there is a pitch, the shirts are on it — and the numbers second.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/pitch_markings.dart';
import 'package:madboots/result_pitch.dart';
import 'package:madboots/season_view.dart';

Map<String, dynamic> json_(Object o) =>
    jsonDecode(jsonEncode(o)) as Map<String, dynamic>;

Map<String, dynamic> man({
  required int id,
  required String name,
  String position = 'MID',
  String team = 'ARS',
  int points = 4,
  int minutes = 90,
  int goals = 0,
  int assists = 0,
  int bonus = 0,
  int saves = 0,
  bool cleanSheet = false,
  int yellow = 0,
  int red = 0,
  bool played = true,
  bool captain = false,
  bool vice = false,
  bool benched = false,
  bool cameOn = false,
  bool wentOff = false,
}) => {
  'player': {
    'id': id,
    'web_name': name,
    'position': position,
    'team': team,
    'price': 5.0,
    'xp': 0.0,
    'status': 'a',
    'chance': null,
    'leaving': null,
    'minutes_weight': 1.0,
    'by_gameweek': {},
  },
  'result': {
    'points': points,
    'minutes': minutes,
    'goals': goals,
    'assists': assists,
    'bonus': bonus,
    'saves': saves,
    'clean_sheet': cleanSheet,
    'yellow_cards': yellow,
    'red_cards': red,
    'played': played,
    // ⭐ Who it was against — the card prints it under the events.
    'matches': [
      if (played) {'opponent': team, 'home': true, 'scored': 2, 'conceded': 0},
    ],
  },
  'pick': {
    'multiplier': captain ? 2 : 1,
    'is_captain': captain,
    'is_vice_captain': vice,
    'benched': benched,
    'came_on': cameOn,
    'went_off': wentOff,
  },
};

/// A legal-looking fifteen: 1 GK, 4 DEF, 4 MID, 2 FWD, plus four on the bench.
GameweekResult week({List<Map<String, dynamic>>? squad}) =>
    GameweekResult.fromJson(
      json_({
        'gameweek': 5,
        'played': true,
        'kits': const {
          'ARS': {'outfield': '', 'gk': ''},
        },
        'summary': const {
          'points': 61,
          'overall_rank': 250000,
          'bench_points': 3,
        },
        'squad':
            squad ??
            [
              man(id: 1, name: 'Keeper', position: 'GK', points: 6),
              for (var i = 0; i < 4; i++)
                man(id: 10 + i, name: 'Def$i', position: 'DEF'),
              for (var i = 0; i < 4; i++)
                man(id: 20 + i, name: 'Mid$i', position: 'MID'),
              for (var i = 0; i < 2; i++)
                man(id: 30 + i, name: 'Fwd$i', position: 'FWD'),
              for (var i = 0; i < 4; i++)
                man(id: 40 + i, name: 'Sub$i', benched: true),
            ],
      }),
    );

Widget screen(Widget child) => MaterialApp(
  home: Scaffold(
    backgroundColor: const Color(0xFF17131F),
    body: SizedBox(width: 390, height: 760, child: child),
  ),
);

void main() {
  testWidgets('a played week is drawn on the green, not in a column', (
    tester,
  ) async {
    // ⭐⭐ **The shape, asserted before any number.** This is the whole of the owner's report and the one
    // thing no previous test could have caught.
    await tester.pumpWidget(screen(PastGameweek(result: week())));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.byType(PitchMarkings), findsOneWidget);
    expect(find.byType(ResultPitch), findsOneWidget);
    // ⚠️ And it is the *same* board the live pitch uses — not a second copy of the layout.
    expect(find.byType(PitchBoard<GameweekPlayer>), findsOneWidget);
  });

  testWidgets('the eleven are on the pitch and the four are on the bench', (
    tester,
  ) async {
    await tester.pumpWidget(screen(PastGameweek(result: week())));
    await tester.pumpAndSettle();
    expect(find.text('BENCH'), findsOneWidget);
    final bench = tester.getRect(find.text('BENCH'));
    final keeper = tester.getRect(find.text('Keeper'));
    final sub = tester.getRect(find.text('Sub0'));
    // ⭐ The keeper above the bench label, the substitutes below it — the arrangement that makes this a
    // team sheet rather than fifteen names.
    expect(keeper.top, lessThan(bench.top));
    expect(sub.top, greaterThan(bench.top));
  });

  testWidgets("a player's points are on his card", (tester) async {
    await tester.pumpWidget(screen(PastGameweek(result: week())));
    await tester.pumpAndSettle();
    expect(find.text('6'), findsOneWidget, reason: "the keeper's score");
    expect(find.text('4'), findsWidgets);
    // ⭐ And the week's own total is still above the pitch, where the live page puts its projection.
    expect(find.text('61'), findsOneWidget);
    expect(find.text('250,000'), findsOneWidget);
  });

  // ── the thing the owner went looking for and could not find ─────────────────

  testWidgets('a booking is drawn as a yellow card, not buried in a sentence', (
    tester,
  ) async {
    // ⚠️⚠️ **The second half of the report: *"the list does not have yellow or red cards."*** They were
    // in the build — as a 🟨 glyph inside a run-on line of events, on a row that had to be read. ⭐ *An
    // event you have to read a sentence to find is an event the screen did not report.*
    final booked = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK'),
        man(id: 10, name: 'Booked', position: 'DEF', yellow: 1),
        for (var i = 1; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        for (var i = 0; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        for (var i = 0; i < 2; i++)
          man(id: 30 + i, name: 'Fwd$i', position: 'FWD'),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: booked)));
    await tester.pumpAndSettle();

    // ⭐ A coloured rectangle, found by its colour — *the one event whose entire meaning is its colour*,
    // which is also why it is not an emoji: 🟨 renders grey on some Android builds.
    expect(
      _badges(tester, const Color(0xFFF5C518)),
      1,
      reason: 'the booking is not on the pitch',
    );
    expect(_badges(tester, const Color(0xFFE5343D)), 0);
  });

  testWidgets('a sending-off is red, and a second yellow says so', (
    tester,
  ) async {
    final sent = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK'),
        man(id: 10, name: 'Sent', position: 'DEF', red: 1, yellow: 2),
        man(id: 11, name: 'Twice', position: 'DEF', yellow: 2),
        for (var i = 2; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        for (var i = 0; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        for (var i = 0; i < 2; i++)
          man(id: 30 + i, name: 'Fwd$i', position: 'FWD'),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: sent)));
    await tester.pumpAndSettle();
    // ⚠️ A red card wins: a man who was sent off for two yellows is shown as sent off, not as booked.
    expect(_badges(tester, const Color(0xFFE5343D)), 1);
    expect(
      _badges(tester, const Color(0xFFF5C518)),
      1,
      reason: 'the two-yellow man',
    );
    // ⭐ The count only when it is more than one — a "1" beside every booking is noise on a 70pt card.
    expect(find.text('2'), findsWidgets);
  });

  // ── the two kinds of zero ────────────────────────────────────────────────────

  testWidgets('a blank gameweek is a dash and a dimmed shirt, never a zero', (
    tester,
  ) async {
    // ⭐⭐ *Zero is a score; absence is the absence of one* — and on a real played week the two are
    // genuinely different facts. ⚠️ A man who did not play and a man who played badly must not read the
    // same at a glance.
    final blank = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK'),
        man(
          id: 10,
          name: 'Absent',
          position: 'DEF',
          played: false,
          points: 0,
          minutes: 0,
        ),
        for (var i = 1; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        for (var i = 0; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        for (var i = 0; i < 2; i++)
          man(id: 30 + i, name: 'Fwd$i', position: 'FWD'),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: blank)));
    await tester.pumpAndSettle();
    expect(find.text('—'), findsOneWidget);
    expect(find.text('did not play'), findsOneWidget);

    final shirts = tester
        .widgetList<Opacity>(find.byType(Opacity))
        .map((o) => o.opacity)
        .toList();
    expect(
      shirts.where((o) => o < 0.5).length,
      1,
      reason: 'the absent man is not dimmed',
    );
  });

  testWidgets('the armband survives the week it was worn in', (tester) async {
    final led = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK'),
        for (var i = 0; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        man(
          id: 20,
          name: 'Skipper',
          position: 'MID',
          captain: true,
          points: 12,
        ),
        for (var i = 1; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        for (var i = 0; i < 2; i++)
          man(id: 30 + i, name: 'Fwd$i', position: 'FWD'),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: led)));
    await tester.pumpAndSettle();
    // ⭐ Who you actually captained that week is half the reason to look back at it.
    expect(find.text('C'), findsOneWidget);
    expect(find.text('12'), findsOneWidget);
  });

  testWidgets('what the points were for is drawn, one icon per event', (
    tester,
  ) async {
    // ⭐⭐ **One icon per goal, not a number beside one icon** (owner: *"football for each goal, a boot
    // for assist etc., bonus point in a coloured circle"*). Two footballs read as *two goals* before
    // anything is parsed; `⚽2` has to be read.
    //
    // ⚠️ Counted by **shape**, not by text — which is the whole point of the change: the previous version
    // asserted the string `'⚽2 +3'`, and a string is exactly what Android was free to re-render as
    // something else.
    final scored = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK', saves: 5, cleanSheet: true),
        for (var i = 0; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        for (var i = 0; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        man(id: 30, name: 'Striker', position: 'FWD', goals: 2, bonus: 3),
        man(id: 31, name: 'Fwd1', position: 'FWD', assists: 1),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: scored)));
    await tester.pumpAndSettle();

    // Two goals → two balls: white circles, 10pt.
    final balls = tester
        .widgetList<Container>(find.byType(Container))
        .where(
          (c) =>
              c.constraints?.maxWidth == 10 &&
              (c.decoration as BoxDecoration?)?.shape == BoxShape.circle &&
              (c.decoration as BoxDecoration?)?.color == Colors.white,
        )
        .length;
    expect(balls, 2, reason: 'two goals should draw two footballs');

    // One assist → one boot.
    // ⚠️ A drawn boot, not an icon: Material has no football boot and the nearest was a ball
    // outline — the one shape it must not be, on a strip whose first icon is a ball.
    expect(find.byType(CustomPaint), findsWidgets);
    expect(
      tester
          .widgetList<CustomPaint>(find.byType(CustomPaint))
          .where((c) => c.painter.runtimeType.toString().contains('Boot'))
          .length,
      1,
      reason: 'one assist should draw one boot',
    );
    // One clean sheet → one shield.
    expect(find.byIcon(Icons.shield), findsOneWidget);
    // ⭐ Bonus in its own coloured circle, which is how FPL itself prints it.
    final bonus = tester
        .widgetList<Container>(find.byType(Container))
        .where(
          (c) =>
              (c.decoration as BoxDecoration?)?.color ==
              const Color(0xFFE59A1B),
        )
        .length;
    expect(bonus, 1, reason: 'the bonus pip is missing');
    expect(find.text('3'), findsWidgets, reason: 'the bonus count');
    expect(find.text('5'), findsWidgets, reason: 'the save count');
  });

  testWidgets('a hat-trick does not run off the card', (tester) async {
    // ⚠️ Capped at three — *a 70pt card runs out of room, and four of anything is a number again anyway.*
    final haul = week(
      squad: [
        man(id: 1, name: 'Keeper', position: 'GK'),
        for (var i = 0; i < 4; i++)
          man(id: 10 + i, name: 'Def$i', position: 'DEF'),
        for (var i = 0; i < 4; i++)
          man(id: 20 + i, name: 'Mid$i', position: 'MID'),
        man(id: 30, name: 'Striker', position: 'FWD', goals: 5, points: 24),
        man(id: 31, name: 'Fwd1', position: 'FWD'),
        for (var i = 0; i < 4; i++)
          man(id: 40 + i, name: 'Sub$i', benched: true),
      ],
    );
    await tester.pumpWidget(screen(PastGameweek(result: haul)));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    final balls = tester
        .widgetList<Container>(find.byType(Container))
        .where(
          (c) =>
              c.constraints?.maxWidth == 10 &&
              (c.decoration as BoxDecoration?)?.color == Colors.white,
        )
        .length;
    expect(balls, 3, reason: 'five goals drew $balls footballs');
  });

  testWidgets('a past card says who he played', (tester) async {
    // ⭐⭐ Owner: *"for history GWs, can we see which club player played against."* ⚠️ *Two points against
    // City and two against Burnley are different weeks*, and the column that told them apart was missing.
    await tester.pumpWidget(screen(PastGameweek(result: week())));
    await tester.pumpAndSettle();
    expect(find.textContaining('ARS (H)'), findsWidgets);
  });
}

/// How many card badges of a given colour are on screen.
int _badges(WidgetTester tester, Color colour) => tester
    .widgetList<Container>(find.byType(Container))
    .where((c) => (c.decoration as BoxDecoration?)?.color == colour)
    .length;
