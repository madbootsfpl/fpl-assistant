// The desktop mini-card, merged into the sheet you already tap (ADR-276).
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/player_sheet.dart';

String sample(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

MyTeam team() =>
    MyTeam.fromJson(jsonDecode(sample('my-team')) as Map<String, dynamic>);

ServiceClient clientServing(String body, {int status = 200}) => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient(
    (_) async => http.Response(
      body,
      status,
      headers: {'content-type': 'application/json; charset=utf-8'},
    ),
  ),
);

Future<void> openSheet(
  WidgetTester tester,
  ServiceClient client,
  PlayerSummary player,
) async {
  tester.view.physicalSize = const Size(420, 1800);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: Brand.ink,
        body: Builder(
          builder: (context) => TextButton(
            onPressed: () => showPlayerSheet(
              context,
              team: team(),
              player: player,
              client: client,
            ),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
}

void main() {
  final starter = team().analysis.xi.first;

  testWidgets('the four actions are still there', (tester) async {
    await openSheet(tester, clientServing(sample('player')), starter);
    // ⚠️ **Shortened to fit four across** (ADR-286). The icon above each word carries the recognition;
    // "Make captain" needed the verb when it was a full-width row with three others stacked under it.
    for (final label in const [
      'Captain',
      'Vice-captain',
      'Bench',
      'Transfer',
    ]) {
      expect(find.text(label), findsOneWidget, reason: '$label is missing');
    }
  });

  testWidgets('the season stats arrive beside them', (tester) async {
    await openSheet(tester, clientServing(sample('player')), starter);

    final card = PlayerCard.fromJson(
      jsonDecode(sample('player')) as Map<String, dynamic>,
    );
    // ⭐ Four, not nine — a block long enough to push the actions off-screen has replaced them.
    for (final stat in card.stats.take(4)) {
      expect(
        find.text(stat.label),
        findsOneWidget,
        reason: '${stat.label} is missing',
      );
    }
    expect(
      find.text(card.stats[4].label),
      findsNothing,
      reason: 'too many stats shown',
    );
  });

  testWidgets('his run is shown with the per-gameweek number', (tester) async {
    await openSheet(tester, clientServing(sample('player')), starter);

    final run = team().runFor(starter);
    expect(run, isNotEmpty, reason: 'the fixture squad must carry a run');
    expect(find.text(run.first.label), findsOneWidget);
  });

  // ⚠️⚠️ The reason the sheet exists is the four buttons; a network error must not take them with it.
  testWidgets('a failed stats fetch loses the stats, never the actions', (
    tester,
  ) async {
    await openSheet(tester, clientServing('nope', status: 500), starter);

    expect(find.text('Captain'), findsOneWidget);
    expect(find.text('Transfer'), findsOneWidget);
    expect(find.textContaining('did not load'), findsOneWidget);
  });

  testWidgets('the header still names him', (tester) async {
    await openSheet(tester, clientServing(sample('player')), starter);
    expect(find.text(starter.name), findsWidgets);
    expect(
      find.textContaining('£${starter.price.toStringAsFixed(1)}m'),
      findsWidgets,
    );
  });

  testWidgets('every fixture on the card carries its own xP', (tester) async {
    /// ⚠️⚠️ **The bug the owner photographed.** The sheet read `player.byGameweek`, and `my-team` is
    /// fetched with `horizon: 1` — so it held **one** gameweek and the second and third fixtures
    /// rendered as `—` while the web card showed 5.4 / 5.4 / 5.3.
    ///
    /// ⭐ *A value that is fetched, parsed, stored and then read from the wrong place looks exactly like
    /// a value the server never sent* — which is why this asserts there is **no** em-dash, not merely
    /// that the first number is right.
    await openSheet(tester, clientServing(sample('player')), starter);

    final run = team().runFor(starter).take(3);
    expect(
      run.length,
      greaterThan(1),
      reason: 'the fixture strip needs a run to test',
    );
    for (final fixture in run) {
      expect(find.text(fixture.label), findsOneWidget);
    }
    expect(
      find.text('—'),
      findsNothing,
      reason: 'a fixture with no xP means the sheet is reading the one-gameweek map again',
    );
  });

  testWidgets('the fixture xP comes from the run, not the squad summary', (
    tester,
  ) async {
    // ⭐ Pinned against the model rather than a literal, so the numbers can change without this failing
    // and the *source* still cannot.
    final xp = team().runXpFor(starter);
    await openSheet(tester, clientServing(sample('player')), starter);

    for (final fixture in team().runFor(starter).take(3)) {
      final gw = fixture.gameweek;
      if (gw == null || xp[gw] == null) continue;
      expect(find.text(xp[gw]!.toStringAsFixed(1)), findsWidgets);
    }
  });

  testWidgets('the lenses are shown, glyph and word together', (tester) async {
    // ⭐ The web card has shown these for a year (ADR-081/US-289); the phone showed neither, because the
    // endpoint never sent them.
    await openSheet(tester, clientServing(sample('player')), starter);

    final card = PlayerCard.fromJson(
      jsonDecode(sample('player')) as Map<String, dynamic>,
    );
    expect(
      card.badges,
      isNotEmpty,
      reason: 'the sample has no badges to render',
    );
    for (final badge in card.badges) {
      // ⚠️ Both halves. *Three unlabelled pictures is a rebus, and the reader who does not already know
      // what 🎯 means has no way to find out from a phone.*
      expect(find.text('${badge.glyph} ${badge.label}'), findsOneWidget);
    }
  });

  testWidgets('a card with no badges renders no strip', (tester) async {
    // ⚠️ An empty row of pills would read as "loading", not as "nothing to say".
    final bare = jsonDecode(sample('player')) as Map<String, dynamic>;
    bare.remove('badges');
    await openSheet(tester, clientServing(jsonEncode(bare)), starter);

    expect(find.byType(Wrap), findsNothing);
    expect(
      find.text('Captain'),
      findsOneWidget,
      reason: 'the actions must survive it',
    );
  });
}
