/// Boot Battle, reached from the browse list (ADR-257).
///
/// ⭐⭐ **The last piece of the mobile audit's §6** — *search, compare, the card*. Compare has existed
/// since ADR-236 and could only be reached from the transfer flow, which answers *"who should replace
/// him?"* — ⚠️ *a different question from "which of these two?"*, and the second is what a browse list is
/// for.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/players_view.dart';

String sampleText(String name) =>
    File('../spikes/018-flutter-read-slice/api-samples/$name.json')
        .readAsStringSync();

ServiceClient sampleClient() => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient((request) async {
    // ⚠️ `/player` before `/players` would never match — `endsWith` is not exclusive, so order the
    // longer path first. ⭐ *A router that tests the shorter prefix first answers the wrong question.*
    if (request.url.path.endsWith('/players')) {
      return http.Response(
        sampleText('players'),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }
    if (request.url.path.endsWith('/player')) {
      return http.Response(
        sampleText('player'),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }
    return http.Response('{}', 404);
  }),
);

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(backgroundColor: const Color(0xFF17131F), body: child),
);

void main() {
  testWidgets('a closed list offers no comparison', (tester) async {
    await tester.pumpWidget(
      wrap(PlayersView(client: sampleClient(), owned: const {})),
    );
    await tester.pumpAndSettle();

    // ⚠️ The button lives on the **expanded** card, where a reader has already said they are interested
    // in this player. A compare button on every one of 481 closed rows is noise.
    expect(find.textContaining('Compare with'), findsNothing);
  });

  testWidgets('expanding a row offers the comparison', (tester) async {
    // ⭐⭐⭐ **The assertion that matters**, and the first version of this file did not have it: a test
    // that only checks the button is *absent* when collapsed passes on a build where it never exists at
    // all. ⚠️ *Asserting an absence proves nothing about a presence.*
    await tester.pumpWidget(
      wrap(PlayersView(client: sampleClient(), owned: const {})),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();

    expect(find.textContaining('Compare with'), findsOneWidget);
  });

  testWidgets('the picker explains why the list is what it is', (tester) async {
    await tester.pumpWidget(
      wrap(PlayersView(client: sampleClient(), owned: const {})),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('Compare with'));
    await tester.pumpAndSettle();

    // ⭐ Otherwise *"where is everyone?"* is the first thought, and the answer — your filters, and his
    // position — is invisible.
    expect(
      find.textContaining('in the list you are looking at'),
      findsOneWidget,
    );
  });

  testWidgets('the count on the button is the widget\'s own, and it is right', (
    tester,
  ) async {
    // ⭐⭐⭐ **Asserts what the widget computed, not what the test would compute.**
    //
    // ⚠️ The first version of this file recomputed the same-position filter in Dart and checked *its own*
    // answer — so two mutations walked straight through it: offering other positions, and offering the
    // player against himself. ⭐ *A test that re-describes the logic guards the description* (ADR-241),
    // and the button's label is the one place the widget states its answer out loud.
    await tester.pumpWidget(
      wrap(PlayersView(client: sampleClient(), owned: const {})),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.expand_more).first);
    await tester.pumpAndSettle();

    final label = tester
        .widgetList<Text>(find.textContaining('Compare with'))
        .map((w) => w.data!)
        .single;
    final offered = int.parse(
      RegExp(r'one of (\d+)').firstMatch(label)!.group(1)!,
    );

    final board =
        (jsonDecode(sampleText('players')) as Map<String, dynamic>)['players']
            as List;
    final subject = board.first as Map<String, dynamic>;
    final samePosition = board
        .where(
          (p) => (p as Map<String, dynamic>)['position'] == subject['position'],
        )
        .length;

    // ⚠️ Same position, **minus himself**. The two mutations differ from this by exactly one and by a
    // great deal, and both now fail.
    expect(
      offered,
      samePosition - 1,
      reason:
          'offered $offered; the board holds $samePosition of his position including him',
    );
  });
}

/// ⭐ A two-field stand-in: this test is about **which** players are offered, not about parsing — and
/// pulling the real model in would make a selection test into a model test.
class PlayerSummaryLite {
  PlayerSummaryLite({required this.id, required this.position});

  factory PlayerSummaryLite.fromJson(Map<String, dynamic> json) =>
      PlayerSummaryLite(
        id: json['id'] as int,
        position: json['position'] as String,
      );

  final int id;
  final String position;
}
