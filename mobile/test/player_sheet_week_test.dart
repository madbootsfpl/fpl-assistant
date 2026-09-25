/// The card knows which week you are in (ADR-299).
///
/// ⭐⭐⭐ **ADR-298 made the pitch week-aware and left the sheet behind.** Swipe to GW9, tap a player, and
/// the card answered a question about *this* Saturday — three correct numbers about a week the reader had
/// already swiped past. ⚠️ *A screen that changes what it is about must change what its children are
/// about.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/player_sheet.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

/// Opens the sheet over a bare page and settles it.
Future<void> open(
  WidgetTester tester,
  MyTeam team,
  PlayerSummary player, {
  int? gameweek,
  GameweekPlayer? result,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          backgroundColor: const Color(0xFF17131F),
          body: Center(
            child: ElevatedButton(
              onPressed: () => showPlayerSheet(
                context,
                team: team,
                player: player,
                client: ServiceClient(baseUrl: 'http://x'),
                gameweek: gameweek,
                result: result,
              ),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('open'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
}

void main() {
  testWidgets('the live pitch opens on the next gameweek, as it always did', (
    tester,
  ) async {
    // ⭐ The counterpart, and the one that must not move. Without it, "always start at the page's week"
    // could be implemented as "always start at index 0" and both tests would pass.
    final team = sampleTeam();
    final haaland = team.analysis.xi.firstWhere((p) => p.name == 'Haaland');
    await open(tester, team, haaland);

    final run = team.runFor(haaland);
    expect(find.textContaining(run.first.opponent), findsWidgets);
  });

  testWidgets('a forward page opens on that week, not on this one', (
    tester,
  ) async {
    // ⚠️⚠️ **This is the report.** Tapping a player on the GW9 page showed GW6 · GW7 · GW8.
    final team = sampleTeam();
    final haaland = team.analysis.xi.firstWhere((p) => p.name == 'Haaland');
    final live = team.fixtureAt(haaland, 6)!;
    final nine = team.fixtureAt(haaland, 9)!;
    expect(nine.opponent, isNot(live.opponent), reason: 'the sample moved');

    await open(tester, team, haaland, gameweek: 9);

    expect(find.textContaining(nine.opponent), findsWidgets);
    expect(
      find.textContaining(live.opponent),
      findsNothing,
      reason: 'the card is still starting from the live week',
    );
    // ⭐ And the number beside it is that week's, not this week's.
    expect(find.text(team.xpAt(haaland, 9)!.toStringAsFixed(1)), findsWidgets);
  });

  testWidgets('the window shortens as it approaches the cap', (tester) async {
    // ⚠️⚠️ **Three weeks at GW9, one at GW11 — and that is ADR-298's cap holding, not a bug.** Running
    // to GW14 would mean projecting nine weeks out, which is the decision that ADR took deliberately.
    // ⭐ *A card that kept showing three boxes would have to invent the last two.*
    final team = sampleTeam();
    final haaland = team.analysis.xi.firstWhere((p) => p.name == 'Haaland');
    final last = team.fixtureAt(haaland, 11)!;

    await open(tester, team, haaland, gameweek: 11);

    expect(find.textContaining(last.opponent), findsWidgets);
    // Nothing from before it, and nothing invented after it.
    for (final gw in [6, 7, 8, 9, 10]) {
      final f = team.fixtureAt(haaland, gw);
      if (f == null || f.opponent == last.opponent) continue;
      expect(
        find.textContaining(f.opponent),
        findsNothing,
        reason: 'GW$gw leaked onto a GW11 card',
      );
    }
  });

  testWidgets('a week the run does not carry falls back rather than blanking', (
    tester,
  ) async {
    // ⚠️ A blank gameweek, or a page left open while the data moved on. ⭐ *An empty row reads as a
    // broken card*, and the front of the run is at least true.
    final team = sampleTeam();
    final haaland = team.analysis.xi.firstWhere((p) => p.name == 'Haaland');

    await open(tester, team, haaland, gameweek: 34);

    expect(tester.takeException(), isNull);
    expect(
      find.textContaining(team.runFor(haaland).first.opponent),
      findsWidgets,
    );
  });

  // ── a week that has been played ─────────────────────────────────────────────

  /// One played week for a player, as the service sends it.
  GameweekPlayer played({
    int points = 11,
    List<Map<String, dynamic>> breakdown = const [
      {'stat': 'minutes', 'value': 90, 'points': 2},
      {'stat': 'assists', 'value': 1, 'points': 3},
      {'stat': 'clean_sheets', 'value': 1, 'points': 4},
      {'stat': 'yellow_cards', 'value': 1, 'points': -1},
      {'stat': 'bonus', 'value': 3, 'points': 3},
    ],
    List<Map<String, dynamic>> matches = const [
      {'opponent': 'MUN', 'home': false, 'scored': 1, 'conceded': 0},
    ],
    bool didPlay = true,
    bool benched = false,
    bool captain = false,
  }) => GameweekPlayer.fromJson(
    jsonDecode(
      jsonEncode({
        'player': {
          'id': 1,
          'web_name': 'Gvardiol',
          'position': 'DEF',
          'team': 'MCI',
          'price': 5.7,
          'xp': 4.0,
          'status': 'a',
          'chance': null,
          'leaving': null,
          'minutes_weight': 1.0,
          'by_gameweek': {},
        },
        'result': {
          'points': points,
          'minutes': 90,
          'goals': 0,
          'assists': 1,
          'bonus': 3,
          'saves': 0,
          'clean_sheet': true,
          'yellow_cards': 1,
          'red_cards': 0,
          'played': didPlay,
          'breakdown': breakdown,
          'matches': matches,
        },
        'pick': {
          'multiplier': 1,
          'is_captain': captain,
          'is_vice_captain': false,
          'benched': benched,
          'came_on': false,
          'went_off': false,
        },
      }),
    ) as Map<String, dynamic>,
  );

  testWidgets("a played week shows what he did, not what he might do", (
    tester,
  ) async {
    // ⭐⭐⭐ **The owner's report**: *"it needs to show the history of that GW and not the prediction from
    // the current gameweek onwards."*
    final team = sampleTeam();
    final p = team.analysis.xi.first;
    await open(tester, team, p, gameweek: 4, result: played());

    // FPL's own attribution, line by line.
    expect(find.text('Minutes played'), findsOneWidget);
    expect(find.text("90'"), findsOneWidget);
    expect(find.text('+2'), findsOneWidget);
    expect(find.text('Yellow cards'), findsOneWidget);
    expect(find.text('-1'), findsOneWidget);
    expect(find.text('Clean sheet'), findsOneWidget);
    expect(find.text('+4'), findsOneWidget);
    // The total, and the match it came from.
    expect(find.text('11'), findsOneWidget);
    expect(find.textContaining('MUN'), findsWidgets);
    expect(find.textContaining('1–0'), findsOneWidget);
  });

  testWidgets('a played week offers nothing you can no longer do', (
    tester,
  ) async {
    // ⚠️⚠️ Captain · Vice · Bench · Transfer were being offered against a gameweek that finished eleven
    // days ago. ⭐ *An action that cannot be taken is worse than a missing one, because the reader has to
    // work out why it did nothing.*
    final team = sampleTeam();
    await open(
      tester,
      team,
      team.analysis.xi.first,
      gameweek: 4,
      result: played(),
    );

    expect(find.text('Captain'), findsNothing);
    expect(find.text('Vice-captain'), findsNothing);
    expect(find.text('Bench'), findsNothing);
    expect(find.text('Transfer'), findsNothing);
  });

  testWidgets('a played week prints no price and no projection', (
    tester,
  ) async {
    // ⚠️ Both are facts about *today*. A projection for a match already played is meaningless, and
    // today's price under a GW4 heading reads as the price then — ⭐ *a true number in the wrong place
    // becomes a false claim.*
    final team = sampleTeam();
    await open(
      tester,
      team,
      team.analysis.xi.first,
      gameweek: 4,
      result: played(),
    );

    expect(find.textContaining('£'), findsNothing);
    expect(find.textContaining('xP'), findsNothing);
    expect(find.textContaining('GW4'), findsOneWidget);
  });

  testWidgets('a blank week says so rather than tabling zeroes', (
    tester,
  ) async {
    // ⚠️⚠️ FPL publishes **no lines** for a man who never came on. ⭐ *A table of zeroes claims he played
    // and scored nothing, which is a different week.*
    final team = sampleTeam();
    await open(
      tester,
      team,
      team.analysis.xi.first,
      gameweek: 4,
      result: played(
        points: 0,
        didPlay: false,
        benched: true,
        breakdown: const [],
        matches: const [],
      ),
    );

    expect(find.text('—'), findsOneWidget);
    expect(find.textContaining('did not come on'), findsOneWidget);
    expect(find.text('Minutes played'), findsNothing);
  });

  testWidgets('a stat this app has never heard of still shows its points', (
    tester,
  ) async {
    // ⭐⭐ **FPL adds stats between seasons** — `defensive_contribution` arrived this one, and inventing a
    // scoring table here is exactly what this feature refused to do. ⚠️ *A label map that silently drops
    // an unknown line loses points the reader can see in the total.*
    final team = sampleTeam();
    await open(
      tester,
      team,
      team.analysis.xi.first,
      gameweek: 4,
      result: played(
        points: 4,
        breakdown: const [
          {'stat': 'some_future_stat', 'value': 7, 'points': 4},
        ],
      ),
    );

    expect(find.text('some future stat'), findsOneWidget);
    expect(find.text('+4'), findsOneWidget);
  });

  testWidgets('a double gameweek shows both matches', (tester) async {
    // ⚠️ *Showing one of two is worse than showing neither, because it looks complete.*
    final team = sampleTeam();
    await open(
      tester,
      team,
      team.analysis.xi.first,
      gameweek: 4,
      result: played(
        matches: const [
          {'opponent': 'MUN', 'home': false, 'scored': 1, 'conceded': 0},
          {'opponent': 'EVE', 'home': true, 'scored': 2, 'conceded': 2},
        ],
      ),
    );

    expect(find.textContaining('MUN'), findsWidgets);
    expect(find.textContaining('EVE'), findsWidgets);
  });
}
