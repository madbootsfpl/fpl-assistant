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
    for (final label in const [
      'Make captain',
      'Make vice-captain',
      'Transfer…',
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

    expect(find.text('Make captain'), findsOneWidget);
    expect(find.text('Transfer…'), findsOneWidget);
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
}
