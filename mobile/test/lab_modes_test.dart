/// The Lab's three modes, as the screen actually sends them (ADR-294).
///
/// ⭐⭐ **The enum was tested and its use was not.** `lab_apply_test.dart` pins that
/// `LabMode.freeHit.horizon` is 1 and that only a new season starts `fromScratch` — and every one of
/// those assertions passed while `horizon: 5` was hardcoded into the request, because they never looked
/// at the request. ⚠️ *A constant nobody reads is a constant that is correct and irrelevant.*
///
/// These pump the screen, tap the mode, press build, and read what went **on the wire**.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/brand.dart';
import 'package:madboots/lab_view.dart';

String sample(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

/// ⚠️ **With a team value, because the committed sample has none.** The Lab refuses to build without
/// one — *"your team value has not loaded, so there is no budget to build against"* — and a fixture that
/// cannot reach the button cannot test what the button sends. ⭐ *The sample documents the shape; the
/// test supplies the case.*
const double kTeamValue = 100.8;

MyTeam team() {
  final json = jsonDecode(sample('my-team')) as Map<String, dynamic>;
  // ⚠️ Under `squad`, not at the top level — *and setting it at the top level failed silently*, leaving
  // the screen on its no-budget message with no pills to tap. ⭐ *A fixture that patches the wrong key
  // produces a test that fails for a reason unrelated to the thing it is testing.*
  final squad = {...json['squad'] as Map<String, dynamic>};
  squad['value'] = kTeamValue;
  squad['bank'] = 1.3;
  return MyTeam.fromJson({...json, 'squad': squad});
}

/// Builds the screen and hands back the **last body it posted to `squad/build`**.
Future<Map<String, dynamic>> requestFor(
  WidgetTester tester,
  String mode,
) async {
  tester.view.physicalSize = const Size(430, 2200);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  Map<String, dynamic>? sent;
  final client = ServiceClient(
    baseUrl: 'http://test',
    client: MockClient((request) async {
      if (request.url.path.endsWith('squad/build')) {
        sent = jsonDecode(request.body) as Map<String, dynamic>;
      }
      return http.Response(
        sample('build'),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }),
  );

  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: Brand.ink,
        body: LabView(client: client, team: team(), onApply: (_, _) async {}),
      ),
    ),
  );
  await tester.pump();

  await tester.tap(find.text(mode));
  await tester.pump();
  await tester.tap(find.text('Build the best fifteen'));
  await tester.pump();

  expect(sent, isNotNull, reason: 'the $mode build never reached the client');
  return sent!;
}

void main() {
  group('the horizon the mode is played over', () {
    testWidgets('Free Hit asks for one gameweek', (tester) async {
      // ⚠️⚠️ **The point of the mode.** A free hit is played for *this* week; asking the solver for a
      // run gives a different fifteen — ⭐ *and the two answers look equally plausible on the screen,
      // which is why only the request can tell them apart.*
      expect((await requestFor(tester, 'Free Hit'))['horizon'], 1);
    });

    testWidgets('Wildcard asks for the run', (tester) async {
      expect((await requestFor(tester, 'Wildcard'))['horizon'], greaterThan(1));
    });

    testWidgets('New season asks for the run', (tester) async {
      expect(
        (await requestFor(tester, 'New season'))['horizon'],
        greaterThan(1),
      );
    });
  });

  group('the budget the mode spends', () {
    testWidgets('a new season starts from FPL\'s hundred million', (
      tester,
    ) async {
      // ⭐ *That is the whole point of the mode* — it does not spend what you own.
      expect((await requestFor(tester, 'New season'))['budget'], 100.0);
    });

    testWidgets('the other two spend your team value', (tester) async {
      for (final mode in const ['Wildcard', 'Free Hit']) {
        expect(
          (await requestFor(tester, mode))['budget'],
          kTeamValue,
          reason: '$mode should spend the squad you already have',
        );
      }
    });

    testWidgets('and a new season keeps nobody', (tester) async {
      // ⚠️ The keep-list is hidden in that mode, so the request must not carry one either — ⭐ *a
      // hidden control whose value still ships is a setting the reader cannot see and cannot change.*
      expect((await requestFor(tester, 'New season'))['include_ids'], isEmpty);
    });
  });
}
