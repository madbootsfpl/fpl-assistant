/// Your team's own name, where it was missing (ADR-311).
///
/// ⚠️⚠️⚠️ **The name was never missing from the data.** FPL gives it as `entry.name`,
/// `fetch_manager_team` reads it, `my_team` returns it as `squad.name`, and this app already parsed it
/// into `MyTeam.squadName` — ⭐ *three layers deep, and displayed nowhere.* Meanwhile every Ask answer
/// read `(squad 'yours')`, because the one request that needed the name had no field to carry it.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/settings_view.dart';
import 'package:shared_preferences/shared_preferences.dart';

MyTeam named(String name) {
  final raw = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  (raw['squad'] as Map<String, dynamic>)['name'] = name;
  return MyTeam.fromJson(raw);
}

/// ⚠️⚠️ **The size has to go on the VIEW, not on a `SizedBox`.** The header asks
/// `MediaQuery.orientationOf`, which reads the window — so wrapping the pitch in a 390×760 box left the
/// harness's default 800×600 surface in charge and reported **landscape** for every case. ⭐ *A test that
/// sizes the widget instead of the screen is testing a different question than the one the code asks.*
Future<void> pumpPitch(
  WidgetTester tester,
  MyTeam team, {
  int? gameweek,
  Size size = const Size(390, 760),
}) async {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = size;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: PitchView(
          team: team,
          mode: PitchMode.nextGw,
          onMode: (_) {},
          onTapPlayer: (_) {},
          gameweek: gameweek,
        ),
      ),
    ),
  );
  await tester.pump();
}

void main() {
  testWidgets('the live pitch says whose team it is', (tester) async {
    await pumpPitch(tester, named('The 4-4-2 Towers'));

    expect(find.text('The 4-4-2 Towers'), findsOneWidget);
  });

  testWidgets('a forward page does not repeat it', (tester) async {
    // ⭐⭐ ADR-253 cut this header from three lines to one because the space is the screen's most
    // valuable. ⚠️ A name on all six swipe pages spends it six times to say something that does not
    // change — *identity belongs where you land, not on every page you pass through.*
    await pumpPitch(tester, named('The 4-4-2 Towers'), gameweek: 9);

    expect(find.text('The 4-4-2 Towers'), findsNothing);
  });

  testWidgets('an unnamed team shows no empty line', (tester) async {
    // ⚠️ *A caption with nothing after it reads as a failure, not as "not yet".*
    await pumpPitch(tester, named(''));

    expect(find.text(''), findsNothing);
  });

  testWidgets('landscape keeps the pitch, not the caption', (tester) async {
    // ⚠️⚠️⚠️ **A layout test caught this, not me.** The line costs ~16pt, and in landscape the pitch has
    // none to give: `pitch_layout_test`'s "the bench never outgrows the eleven" went from 15 to 4. ⭐ *The
    // header is where ADR-253 already found the most expensive space, and landscape is where it is most
    // expensive.*
    await pumpPitch(
      tester,
      named('The 4-4-2 Towers'),
      size: const Size(760, 390),
    );

    expect(find.text('The 4-4-2 Towers'), findsNothing);
  });

  testWidgets('Settings names the team the id belongs to', (tester) async {
    // ⭐ An id on its own is only verifiable by pasting it somewhere else — ⚠️ *a number a reader cannot
    // check is a number they either trust blindly or ignore.*
    SharedPreferences.setMockInitialValues({});
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(500, 2600);
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsView(
            client: ServiceClient(baseUrl: 'http://x'),
            team: named('The 4-4-2 Towers'),
            managerId: 1013841,
            freeTransfers: 1,
            baseUrl: 'http://x',
            onServer: (_) async {},
            onManagerId: (_) {},
            onFreeTransfers: (_) {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('FPL manager id'), findsOneWidget);
    expect(find.text('The 4-4-2 Towers'), findsOneWidget);
  });
}
