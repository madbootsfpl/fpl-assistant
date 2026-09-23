// The group headings actually render (ADR-271/273).
//
// ⚠️ Written because the owner sent the desktop screenshot a second time. ⭐ *"I built it" is not
// evidence that it draws* — this pumps the real widget against the real sample.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/trending_view.dart';

String sample(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

MyTeam team() => MyTeam.fromJson(
  jsonDecode(sample('my-team')) as Map<String, dynamic>,
);

ServiceClient clientServing(String body) => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient(
    (_) async => http.Response(
      body,
      200,
      headers: {'content-type': 'application/json; charset=utf-8'},
    ),
  ),
);

Widget wrap(Widget child) =>
    MaterialApp(home: Scaffold(backgroundColor: Brand.ink, body: child));

void main() {
  testWidgets('the three headings are drawn, once each', (tester) async {
    tester.view.physicalSize = const Size(600, 3000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      wrap(
        TrendingBoards(
          client: clientServing(sample('worth-noticing')),
          team: team(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    for (final heading in const [
      'In form, still under-owned',
      'A bandwagon forming',
      'The template breaking up',
    ]) {
      expect(find.text(heading), findsOneWidget, reason: '$heading is missing');
    }
  });

  testWidgets('a heading sits above the rows it describes', (tester) async {
    tester.view.physicalSize = const Size(600, 3000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      wrap(
        TrendingBoards(
          client: clientServing(sample('worth-noticing')),
          team: team(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final board = TrendingBoard.fromJson(
      jsonDecode(sample('worth-noticing')) as Map<String, dynamic>,
    );
    final firstOfSecondGroup = board.rows
        .firstWhere((r) => r.group == 'A bandwagon forming')
        .player
        .name;

    final heading = tester.getTopLeft(find.text('A bandwagon forming')).dy;
    final row = tester.getTopLeft(find.text(firstOfSecondGroup)).dy;
    expect(heading, lessThan(row), reason: 'the heading must precede its rows');
  });

  testWidgets('a crowd board draws no headings at all', (tester) async {
    tester.view.physicalSize = const Size(600, 3000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      wrap(
        TrendingBoards(
          client: clientServing(sample('trending')),
          team: team(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // ⚠️ The four crowd boards are flat lists; a stray heading there would be a heading over nothing.
    expect(find.text('In form, still under-owned'), findsNothing);
    expect(find.text('A bandwagon forming'), findsNothing);
  });
}
