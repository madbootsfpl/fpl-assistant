// The Server field is not in a tester's build (ADR-270).
//
// ⚠️⚠️ A tester handed an editable API address has a way to point the app at nothing, and the only bug
// report that follows is "the app stopped working" — with no sign in it that a field was ever touched.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/server.dart';
import 'package:madboots/settings_view.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'dart:convert';
import 'dart:io';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Widget wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('a default build offers no Server field', (tester) async {
    tester.view.physicalSize = const Size(500, 2600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      wrap(
        SettingsView(
          team: sampleTeam(),
          managerId: 2885974,
          freeTransfers: 2,
          baseUrl: 'https://madboots-api.onrender.com',
          onServer: (_) async {},
          onManagerId: (_) {},
          onFreeTransfers: (_) {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      kServerFieldEnabled,
      isFalse,
      reason: 'tests run without the dev flag',
    );
    expect(find.text('Server'), findsNothing);

    // ⭐ **And no input holding an address.** The heading being gone would mean little if the field
    // survived — ⚠️ *hiding a label is not removing a control.* Checked by content rather than by
    // counting fields, because Settings legitimately keeps one: the FPL manager id.
    for (final field in tester.widgetList<TextField>(find.byType(TextField))) {
      expect(
        field.controller?.text ?? '',
        isNot(contains('http')),
        reason: 'an editable API address reached a tester build',
      );
    }
    // ⚠️ And the screen did not lose the field it is supposed to have.
    expect(find.text('FPL manager id'), findsOneWidget);
  });

  testWidgets('the rest of Settings is unaffected', (tester) async {
    tester.view.physicalSize = const Size(500, 2600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      wrap(
        SettingsView(
          team: sampleTeam(),
          managerId: 2885974,
          freeTransfers: 2,
          baseUrl: 'https://madboots-api.onrender.com',
          onServer: (_) async {},
          onManagerId: (_) {},
          onFreeTransfers: (_) {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    // ⚠️ Hiding one section must not take the screen with it.
    expect(find.textContaining('2885974'), findsWidgets);
  });

  test(
    'the flag is compile-time, so the control is absent rather than hidden',
    () {
      // ⭐ `bool.fromEnvironment` is a const, which is what lets the branch be tree-shaken — *a control
      // you can reach by accident is a control that is enabled.*
      const flag = kServerFieldEnabled;
      expect(flag, isA<bool>());
    },
  );
}
