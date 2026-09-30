/// Finding the players a price note just told you about (ADR-336).
///
/// 🔴 **Mobile had no price movement at all.** Price was a max-price filter and nothing else, so a reader
/// told *"he may cost £0.1m more if you wait"* on a transfer card had nowhere to go and check, and no way
/// to find anyone else in the same position.
///
/// ⭐ A **filter**, not a board: a risers leaderboard is a different thing competing with this page for
/// the same job.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/players_view.dart';

/// The real sample, so the test breaks if the endpoint stops sending the key.
String sampleText() =>
    File('../spikes/018-flutter-read-slice/api-samples/players.json')
        .readAsStringSync();

ServiceClient client() => ServiceClient(
  baseUrl: 'http://test',
  client: MockClient(
    (request) async => request.url.path.endsWith('/players')
        ? http.Response(
            sampleText(),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          )
        : http.Response('{}', 404),
  ),
);

Future<void> pump(WidgetTester tester) async {
  // ⚠️ The default 800x600 surface, as the other filter tests use. At 420 wide the chip row scrolls and
  // the Filter chip is off-screen — ⭐ *a test that cannot reach the control is not testing the control.*
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: PlayersView(client: client(), owned: const {}),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('the endpoint sends the directions beside the list', () {
    // ⚠️ The sample is the contract (ADR-327). Without this key the filter is a control that does
    // nothing at all.
    //
    // ⭐⭐ **Beside, not inside.** `tests/test_player_shape.py` rejected a `price_direction` field on the
    // player — ADR-227 keeps every player in every answer the same shape, because four shapes once
    // drifted far enough that one shipped 45 database columns to a phone. So the extra fact rides in a
    // sidecar, the way my-team's `prices` does.
    final body = jsonDecode(sampleText()) as Map<String, dynamic>;
    final rows = body['players'] as List;
    expect(rows, isNotEmpty);
    expect(
      (rows.first as Map).containsKey('price_direction'),
      isFalse,
      reason: 'the direction leaked onto the player and broke the shared shape',
    );

    final directions = (body['price_directions'] as Map).values.toSet();
    expect(
      directions,
      containsAll(<String>{'rise', 'fall'}),
      reason: 'the board has no movers — the fixture cannot test the filter',
    );
  });

  test('a player without the key has no opinion rather than an error', () {
    final quiet = PlayerSummary.fromJson({
      'id': 9,
      'web_name': 'X',
      'team': 'ARS',
      'position': 'MID',
      'price': 7.0,
      'xp': 5.0,
    });
    expect(quiet.priceDirection, 'stable');
    expect(quiet.rising, isFalse);
    expect(quiet.falling, isFalse);
  });

  testWidgets('the filter sheet offers rising and falling', (tester) async {
    await pump(tester);
    await tester.tap(
      find.text('Filter'),
    ); // the chip; 'Add a filter' titles the sheet it opens
    await tester.pumpAndSettle();

    expect(find.text('Rising in price'), findsOneWidget);
    expect(find.text('Falling in price'), findsOneWidget);
    // ⚠️ The promise is pressure, never the outcome — the rule is right about 40% of the time (ADR-334).
    expect(find.textContaining('may go up'), findsOneWidget);
    expect(find.textContaining('will rise'), findsNothing);
  });

  /// ⚠️ The rows are a private `_Row`, not `ListTile` — counting widgets found zero on both sides and
  /// the assertion passed vacuously. ⭐ *The board states its own size*, and changes wording when
  /// filtered: `481 players, best first` becomes `10 of 481`, so both shapes have to be read.
  int shown(WidgetTester tester) {
    final counts = tester
        .widgetList<Text>(find.byType(Text))
        .map((t) => t.data ?? '')
        .where(
          (t) =>
              t.contains('players, best first') ||
              RegExp(r'^\d+ of \d+$').hasMatch(t),
        );
    expect(counts, isNotEmpty, reason: 'the board printed no count');
    return int.parse(RegExp(r'\d+').firstMatch(counts.first)!.group(0)!);
  }

  testWidgets('picking rising leaves only players under buying pressure', (
    tester,
  ) async {
    await pump(tester);
    final before = shown(tester);
    expect(
      before,
      greaterThan(50),
      reason: 'the whole board should list first',
    );

    await tester.tap(find.text('Filter'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rising in price'));
    await tester.pumpAndSettle();

    // ⚠️ `textContaining`: the chip renders label and value as one string, `Movement: rising`.
    expect(
      find.textContaining('rising'),
      findsWidgets,
      reason: 'no chip appeared',
    );
    expect(shown(tester), lessThan(before), reason: 'the board did not narrow');
    expect(
      shown(tester),
      greaterThan(0),
      reason: 'the filter emptied the board',
    );
  });

  testWidgets('and tapping the chip takes it off again', (tester) async {
    // ⭐ The page's own pattern — tapping a chip removes it, rather than a second ✕ control.
    await pump(tester);
    await tester.tap(find.text('Filter'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Falling in price'));
    await tester.pumpAndSettle();
    final filtered = shown(tester);

    await tester.tap(find.textContaining('falling'));
    await tester.pumpAndSettle();

    expect(
      shown(tester),
      greaterThan(filtered),
      reason: 'the filter did not come off',
    );
  });
}
