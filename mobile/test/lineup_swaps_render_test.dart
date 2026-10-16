/// The LINEUP block prints pairs the server made, and never a pair of its own (ADR-351).
///
/// 🔴 **The bug, as the owner met it in build 44:** *"3 changes"*, then
///
/// ```
/// ▲ Leno      ▼ Barry      ← a goalkeeper for a midfielder
/// ▲ Guéhi     ▼ Pickford   ← and the reverse
/// ▲ Semenyo   ▼ Virgil
/// ```
///
/// ⭐⭐ **The XI was legal and the sentence describing it was not.** `bring_in` and `drop` are two set
/// differences — who enters the XI and who leaves it — sorted **by player id**, and this view zipped them
/// by index. ⚠️ *The pairing was invented here*, which is why the CLI and `ask`, which never claimed one,
/// were always right.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/this_week_view.dart';

import 'transfers_under_this_week_test.dart' show sampleText, team, wrap;

Map<String, dynamic> _p(String name, String position) => {
  'id': name.hashCode.abs() % 900,
  'web_name': name,
  'position': position,
  'price': 5.0,
  'xp': 4.0,
};

/// The real `gameweek-plan` sample with its lineup replaced, so everything around the block under test
/// is the payload the app actually parses.
String _planWith(Map<String, dynamic> lineup) {
  final plan = jsonDecode(sampleText('gameweek-plan')) as Map<String, dynamic>;
  plan['lineup'] = {...?plan['lineup'] as Map<String, dynamic>?, ...lineup};
  return jsonEncode(plan);
}

Future<List<String>> _pumpLines(
  WidgetTester tester,
  Map<String, dynamic> lineup,
) async {
  // ⚠️ A tall window: This Week scrolls, and on the default 800×600 the list stops building before the
  // Lineup card is ever constructed.
  tester.view.physicalSize = const Size(1200, 5000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  final body = _planWith(lineup);
  await tester.pumpWidget(
    wrap(
      ThisWeekView(
        client: ServiceClient(
          baseUrl: 'http://test',
          client: MockClient(
            (request) async => http.Response(
              request.url.path.contains('gameweek') ? body : '{}',
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            ),
          ),
        ),
        team: team(),
        onApply: (_) async {},
        onAlternatives: () {},
      ),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 50));

  return tester
      .widgetList<Text>(find.byType(Text))
      .map((t) => t.data ?? '')
      .toList();
}

/// The '▲ in ▼ out' lines, as the screen shows them — one Text holds them all, newline-joined.
List<String> _swapLines(List<String> labels) => labels
    .expand((l) => l.split('\n'))
    .where((l) => l.contains('▲') && l.contains('▼'))
    .map((l) => l.replaceAll(RegExp(r'\s+'), ' ').trim())
    .toList();

String _headline(List<String> labels) =>
    labels.firstWhere((l) => l.endsWith('change') || l.endsWith('changes'));

void main() {
  group('the pairs the server made', () {
    testWidgets('a keeper is shown against the keeper, not the midfielder', (
      tester,
    ) async {
      // ⭐ The owner's own three changes, paired as FPL would allow them.
      final labels = await _pumpLines(tester, {
        'bring_in': [
          _p('Leno', 'GK'),
          _p('Guéhi', 'DEF'),
          _p('Semenyo', 'MID'),
        ],
        'drop': [_p('Pickford', 'GK'), _p('Barry', 'MID'), _p('Virgil', 'DEF')],
        'swaps': [
          {'in': _p('Leno', 'GK'), 'out': _p('Pickford', 'GK')},
          {'in': _p('Guéhi', 'DEF'), 'out': _p('Virgil', 'DEF')},
          {'in': _p('Semenyo', 'MID'), 'out': _p('Barry', 'MID')},
        ],
      });

      expect(_swapLines(labels), [
        '▲ Leno ▼ Pickford',
        '▲ Guéhi ▼ Virgil',
        '▲ Semenyo ▼ Barry',
      ]);
    });

    testWidgets('the heading counts the lines it prints, not the set', (
      tester,
    ) async {
      // ⚠️⚠️ **The heading read `bring_in` and the lines read `swaps`.** A change the server declines to
      // pair — a keeper with no keeper to replace — was announced and then not shown. ⭐ *Two numbers
      // from two lists is a discrepancy waiting for the input that separates them.*
      final labels = await _pumpLines(tester, {
        'bring_in': [_p('Leno', 'GK'), _p('Semenyo', 'MID')],
        'drop': [_p('Barry', 'MID'), _p('Virgil', 'DEF')],
        'swaps': [
          {'in': _p('Semenyo', 'MID'), 'out': _p('Barry', 'MID')},
        ],
      });

      expect(_swapLines(labels), hasLength(1));
      expect(_headline(labels), '1 change');
    });
  });

  group('a payload that predates the pairing', () {
    testWidgets('prints two groups and invents no pair', (tester) async {
      // ⭐ The shape the CLI and `ask` have always used. ⚠️ Testers keep an old build for weeks, so this
      // path is live, not hypothetical — and it is the path that must not guess.
      final labels = await _pumpLines(tester, {
        'bring_in': [_p('Leno', 'GK'), _p('Guéhi', 'DEF')],
        'drop': [_p('Barry', 'MID'), _p('Pickford', 'GK')],
        'swaps': null,
      });

      expect(_swapLines(labels), isEmpty);
      final lines = labels.expand((l) => l.split('\n'));
      expect(lines, contains('▲ Start Leno, Guéhi'));
      expect(lines, contains('▼ Bench Barry, Pickford'));
    });
  });

  testWidgets('no change at all says so', (tester) async {
    final labels = await _pumpLines(tester, {
      'bring_in': <Map<String, dynamic>>[],
      'drop': <Map<String, dynamic>>[],
      'swaps': <Map<String, dynamic>>[],
    });

    expect(labels, contains('No change'));
    expect(_swapLines(labels), isEmpty);
  });
}
