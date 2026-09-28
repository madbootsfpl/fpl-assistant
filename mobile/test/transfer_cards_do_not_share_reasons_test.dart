/// Every transfer card carries its own reasons (ADR-327).
///
/// 🔴 **The bug, as a tester met it:** four cards whose headlines differed — *M.Sangaré → Belloumi*,
/// *Egan → Vuskovic*, *Kinsky → Tzolakis*, *Konsa → Schuster* — and whose bodies were identical, down to
/// *"Selling M.Sangaré"* on the card selling Konsa, and *"+3.3 to your starting XI"* under a headline
/// reading +1.8.
///
/// ⭐⭐ The server was asked for one explanation and this view painted it on every card: the headline used
/// the loop variable and the explanation did not. ⚠️ *Invisible until a plan holds more than one move*,
/// which is why it shipped.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/this_week_view.dart';

MyTeam _team() => MyTeam.fromJson(
  jsonDecode(
        File(
          '../spikes/018-flutter-read-slice/api-samples/my-team.json',
        ).readAsStringSync(),
      )
      as Map<String, dynamic>,
);

Map<String, dynamic> _move(
  String out,
  String inName,
  int inId,
  double gain,
  double outXp,
) => {
  'out': {'id': inId + 100, 'web_name': out, 'xp': outXp, 'price': 5.0},
  'in': {'id': inId, 'web_name': inName, 'xp': 6.0, 'price': 4.5},
  'gain': gain,
};

/// A four-move plan whose explanations are, correctly, four different things.
String _planJson() {
  final moves = [
    _move('M.Sangaré', 'Belloumi', 11, 3.3, 2.4),
    _move('Egan', 'Vuskovic', 12, 3.5, 2.0),
    _move('Kinsky', 'Tzolakis', 13, 1.7, 3.0),
    _move('Konsa', 'Schuster', 14, 1.8, 3.1),
  ];
  Map<String, dynamic> ex(String sells, double gain) => {
    'reasons': ['+$gain to your starting XI over 1 GW'],
    'risks': ['Selling $sells'],
    'confidence': 95,
    'band': 'High',
  };
  return jsonEncode({
    'transfer': moves.first,
    'transfers': moves,
    'lineup': <String, dynamic>{},
    'flags': <dynamic>[],
    'timing': <String, dynamic>{},
    'explanation': {
      'transfer': ex('M.Sangaré', 3.3),
      'transfers': {
        '11': ex('M.Sangaré', 3.3),
        '12': ex('Egan', 3.5),
        '13': ex('Kinsky', 1.7),
        '14': ex('Konsa', 1.8),
      },
    },
  });
}

Future<void> _pump(WidgetTester tester) async {
  // ⚠️ A tall viewport on purpose: the cards sit in a `ListView`, which builds lazily, and the fourth
  // card — the one the bug was most visible on — is off-screen at the default 800px test surface.
  // ⭐ *A widget test that only ever renders the first item cannot see a bug about the rest of them.*
  tester.view.physicalSize = const Size(1200, 4000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: ThisWeekView(
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient(
              (_) async => http.Response(
                _planJson(),
                200,
                headers: const {'content-type': 'application/json'},
              ),
            ),
          ),
          team: _team(),
          onApply: (_) async {},
          onAlternatives: () {},
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('each card names the player it actually sells', (tester) async {
    await _pump(tester);
    for (final sold in ['M.Sangaré', 'Egan', 'Kinsky', 'Konsa']) {
      expect(
        find.text('⚠  Selling $sold'),
        findsOneWidget,
        reason: 'no card says it sells $sold — one explanation is being reused',
      );
    }
  });

  testWidgets('no two cards state the same gain', (tester) async {
    await _pump(tester);
    // ⚠️ The screenshot's tell: every body read "+3.3" while the headlines read +3.3, +3.5, +1.7, +1.8.
    for (final gain in ['3.3', '3.5', '1.7', '1.8']) {
      expect(
        find.text('✓  +$gain to your starting XI over 1 GW'),
        findsOneWidget,
        reason: 'the +$gain move does not state its own gain',
      );
    }
  });

  testWidgets('the primary explanation is not repeated across cards', (
    tester,
  ) async {
    await _pump(tester);
    // ⭐ Exactly one card may claim M.Sangaré, not four.
    expect(find.text('⚠  Selling M.Sangaré'), findsOneWidget);
  });
}
