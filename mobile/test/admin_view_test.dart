/// The owner's stats panel (ADR-305).
///
/// ⭐⭐ **The client holds no credential**, and these pin that as much as the rendering: the key is typed,
/// travels per request, and the server does the reading. ⚠️ *The web build is public JavaScript* — a key
/// shipped here is a key published.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/admin_view.dart';
import 'package:madboots/api/client.dart';

const _usage = {
  'ok': true,
  'reason': '',
  'days': 7,
  'events': 412,
  'installs': 9,
  'failures': 3,
  'platforms': {'android': 220, 'ios': 150, 'web': 42},
  'versions': {'1.0.0+21': 300, '1.0.0+20': 112},
  'pages': {'/api/v1/squad/my-team': 180, '/api/v1/ask': 40},
  'median_ms': 74,
  'p95_ms': 910,
  'slowest_ms': 4300,
};

Future<List<Map<String, dynamic>>> pump(
  WidgetTester tester, {
  Map<String, dynamic> reply = _usage,
  int status = 200,
  String? savedKey,
  List<String>? keysSaved,
}) async {
  final sent = <Map<String, dynamic>>[];
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: SizedBox(
          width: 900,
          height: 700,
          child: AdminView(
            savedKey: savedKey,
            onKey: (k) => keysSaved?.add(k),
            client: ServiceClient(
              baseUrl: 'http://x',
              client: MockClient((request) async {
                sent.add(jsonDecode(request.body) as Map<String, dynamic>);
                return http.Response(
                  jsonEncode(reply),
                  status,
                  headers: const {'content-type': 'application/json'},
                );
              }),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return sent;
}

void main() {
  testWidgets('it asks for nothing until a key is given', (tester) async {
    final sent = await pump(tester);
    expect(sent, isEmpty);
    expect(find.text('Enter the key to load.'), findsOneWidget);
  });

  testWidgets('an empty key does not leave the device', (tester) async {
    // ⭐ *A request that cannot succeed should not be made* — and a blank attempt against the one
    // authenticated endpoint would spend a rate-limit slot for nothing.
    final sent = await pump(tester);
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();
    expect(sent, isEmpty);
  });

  testWidgets('the key travels with the request and is never rendered', (
    tester,
  ) async {
    final saved = <String>[];
    final sent = await pump(tester, keysSaved: saved);

    await tester.enterText(find.byType(TextField), 'sesame');
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();

    expect(sent.single['key'], 'sesame');
    expect(sent.single['days'], 7);
    // ⭐ Remembered on the device so a reload does not ask again.
    expect(saved, ['sesame']);
    // ⚠️ And obscured on screen, like any password.
    expect(
      tester.widget<TextField>(find.byType(TextField)).obscureText,
      isTrue,
    );
  });

  testWidgets('it shows counts, the median and the slow tail', (tester) async {
    await pump(tester, savedKey: 'sesame');
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();

    expect(find.text('412'), findsOneWidget);
    expect(find.text('9'), findsOneWidget); // installs, not people
    expect(find.text('74ms'), findsOneWidget);
    // ⭐ *A median hides the request that made someone give up.*
    expect(find.text('910ms'), findsOneWidget);
    expect(find.text('4300ms'), findsOneWidget);
    expect(find.textContaining('android'), findsOneWidget);
  });

  testWidgets('a breakdown shows a share, not a bare count', (tester) async {
    // ⭐ *A count with no denominator is a number you cannot act on.*
    await pump(tester, savedKey: 'sesame');
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();

    expect(find.textContaining('220  ·  53%'), findsOneWidget);
  });

  testWidgets('a refusal names both possibilities and keeps the field', (
    tester,
  ) async {
    // ⚠️⚠️⚠️ **The owner hit this.** He typed the right PIN — the one the Streamlit app uses — and the
    // screen said *"Not found"*, because the API had never been given it. ⭐ *A door that will not open
    // should at least say which two things to check.*
    await pump(tester, savedKey: 'wrong', reply: const {}, status: 401);
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.textContaining('not accepted'), findsOneWidget);
    expect(find.textContaining('no admin key set'), findsOneWidget);
    expect(find.textContaining('separate secrets'), findsOneWidget);
    // ⭐ And you can try again without leaving the screen.
    expect(find.byType(TextField), findsOneWidget);
  });

  testWidgets('a wrong key and an unconfigured server read identically', (
    tester,
  ) async {
    // ⭐⭐ **The security property, pinned.** The server is deliberately silent about which of the two it
    // is, and ⚠️ *a screen that helpfully distinguished them would undo that silence on the client* —
    // telling a stranger whether this deployment has stats at all.
    await pump(tester, savedKey: 'wrong', reply: const {}, status: 401);
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();
    final wrongKey = tester
        .widgetList<Text>(find.byType(Text))
        .map((w) => w.data)
        .firstWhere((s) => s != null && s.contains('not accepted'));

    await pump(tester, savedKey: 'wrong', reply: const {}, status: 404);
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();
    final unconfigured = tester
        .widgetList<Text>(find.byType(Text))
        .map((w) => w.data)
        .firstWhere((s) => s != null && s.contains('not accepted'));

    expect(unconfigured, wrongKey, reason: 'the client distinguishes them');
  });

  testWidgets('a server that is simply down says something else', (
    tester,
  ) async {
    // ⚠️ *Not every failure is the key* — a 500 must not send the owner hunting for a secret.
    await pump(tester, savedKey: 'sesame', reply: const {}, status: 500);
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();

    expect(find.textContaining('not accepted'), findsNothing);
    expect(find.textContaining('at its end'), findsOneWidget);
  });

  testWidgets('an unreadable store still draws, and says why', (tester) async {
    // ⚠️ *A stats page that errors is indistinguishable from a product that is broken*, and it is read
    // at exactly the moment somebody is checking whether the product is broken.
    await pump(
      tester,
      savedKey: 'sesame',
      reply: const {
        'ok': false,
        'reason': 'could not read the events table (ConnectionError)',
        'days': 7,
        'events': 0,
        'installs': 0,
        'failures': 0,
        'platforms': <String, int>{},
        'versions': <String, int>{},
        'pages': <String, int>{},
      },
    );
    await tester.tap(find.text('7d'));
    await tester.pumpAndSettle();

    expect(find.textContaining('could not read'), findsOneWidget);
    expect(find.text('0'), findsWidgets);
    // ⚠️⚠️ **All three, not "at least one".** A mutation rendering the median as `0ms` survived a
    // `findsWidgets` here, because the other two still drew dashes — ⭐ *a test that asks "is there a
    // dash anywhere?" cannot see one field lying.*
    expect(find.text('—'), findsNWidgets(3));
    expect(
      find.textContaining('0ms'),
      findsNothing,
      reason: 'no timings at all is not "instant"',
    );
  });
}
