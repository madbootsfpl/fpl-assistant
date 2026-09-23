// Feedback you can act on: an address to reply to, and where it happened.
//
// ⚠️ Both were missing in a way the screen's own copy concealed — it promised the screen travelled with
// the report while sending the literal string 'mobile' every time (ADR-263).
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/feedback_view.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// ⭐ Reads the **request the client actually sent**, rather than stubbing `feedback()` out.
///
/// ⚠️ Subclassing would have skipped `_post`, which is where a field silently fails to be serialised —
/// exactly the defect being tested for (ADR-241's lesson: *test the output, do not re-implement it*).
class _Recording {
  Map<String, dynamic> sent = {};

  late final ServiceClient client = ServiceClient(
    baseUrl: 'http://test',
    client: MockClient((request) async {
      sent = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(
        '{"sent": true}',
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }),
  );
}

/// ⚠️⚠️ **The `UniqueKey` is load-bearing, and its absence made a test pass for the wrong reason.**
///
/// `pumpWidget` reuses the `State` when the widget type and position are unchanged, so a second pump kept
/// the first one's `TextEditingController` — and *"the address is remembered"* passed with the save
/// removed entirely. ⭐ *It was asserting that a controller holds its own text, which nothing has ever
/// doubted.* A distinct key forces a genuinely new screen, which is what "next time" means. Found by
/// mutation, not by review.
Future<void> _pump(
  WidgetTester tester,
  _Recording rec, {
  String from = '',
}) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: FeedbackView(key: UniqueKey(), client: rec.client, from: from),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('an address typed by the tester reaches the report', (
    tester,
  ) async {
    final client = _Recording();
    await _pump(tester, client);
    await tester.enterText(
      find.byType(TextField).first,
      'the captain armband does not hold',
    );
    await tester.enterText(find.byType(TextField).last, 'tester@example.com');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    expect(client.sent['contact'], 'tester@example.com');
    expect(client.sent['message'], contains('armband'));
  });

  testWidgets('the address is optional — a report with none still sends', (
    tester,
  ) async {
    final client = _Recording();
    await _pump(tester, client);
    await tester.enterText(find.byType(TextField).first, 'no address from me');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    expect(client.sent['contact'], '');
    expect(client.sent['message'], 'no address from me');
  });

  // ⭐ The bug: every report said 'mobile' while the page promised otherwise.
  testWidgets('the report names the screen the tester came from', (
    tester,
  ) async {
    final client = _Recording();
    await _pump(tester, client, from: 'Signals');
    await tester.enterText(
      find.byType(TextField).first,
      'a signal looked wrong',
    );
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    expect(client.sent['screen'], 'Signals');
    expect(client.sent['screen'], isNot('mobile'));
  });

  testWidgets(
    'with no screen known it names the app rather than inventing one',
    (tester) async {
      final client = _Recording();
      await _pump(tester, client, from: '   ');
      await tester.enterText(find.byType(TextField).first, 'general note');
      await tester.tap(find.text('Send'));
      await tester.pumpAndSettle();

      // ⚠️ *An invented location is worse than none, because it is believed.*
      expect(client.sent['screen'], 'mobile');
    },
  );

  testWidgets(
    'the page states the screen it will report, so the claim is checkable',
    (tester) async {
      await _pump(tester, _Recording(), from: 'Transfers');
      expect(find.textContaining('Transfers'), findsWidgets);
    },
  );

  testWidgets('the address is remembered for the next report', (tester) async {
    final first = _Recording();
    await _pump(tester, first);
    await tester.enterText(find.byType(TextField).first, 'first report');
    await tester.enterText(find.byType(TextField).last, 'tester@example.com');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    final second = _Recording();
    await _pump(tester, second);
    await tester.enterText(find.byType(TextField).first, 'second report');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    // ⭐ The point: an optional field that must be retyped every time gets filled in once.
    expect(second.sent['contact'], 'tester@example.com');
  });

  testWidgets('clearing the address clears it for next time too', (
    tester,
  ) async {
    final first = _Recording();
    await _pump(tester, first);
    await tester.enterText(find.byType(TextField).first, 'a report');
    await tester.enterText(find.byType(TextField).last, 'tester@example.com');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    final second = _Recording();
    await _pump(tester, second);
    await tester.enterText(find.byType(TextField).last, '');
    await tester.enterText(find.byType(TextField).first, 'remove me');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    final third = _Recording();
    await _pump(tester, third);
    await tester.enterText(find.byType(TextField).first, 'third');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();

    // ⚠️ A tester removing their address means it.
    expect(third.sent['contact'], '');
  });
}
