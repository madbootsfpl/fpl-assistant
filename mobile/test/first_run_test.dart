// Whose team is this? (ADR-279)
//
// ⚠️⚠️ The app used to open on the author's squad, from a `const` in the source — and never saved the
// id, so correcting it in Settings lasted until the next launch.
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/main.dart';
import 'package:madboots/manager_store.dart';
import 'package:madboots/welcome_view.dart';
import 'package:shared_preferences/shared_preferences.dart';

Widget wrap(Widget child) => MaterialApp(home: child);

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('ManagerStore', () {
    // ⭐ Null, not a default — a default is a guess about whose team you are looking at.
    test('a fresh install knows nobody', () async {
      expect(await ManagerStore().load(), isNull);
    });

    test('what a manager gives is what comes back', () async {
      await ManagerStore().save(2885974);
      expect(await ManagerStore().load(), 2885974);
    });

    test(
      'it survives a new store instance — that is the whole point',
      () async {
        await ManagerStore().save(1234567);
        expect(await ManagerStore().load(), 1234567);
      },
    );

    // ⚠️ A zero or negative id is not a manager; storing one would make the app ask the API about
    // nobody and render the failure as though the team were empty.
    // ⚠️⚠️ **Checked at the raw preference, not through `load()`.** Both `save` and `load` reject a
    // junk id, so a test going through `load()` passes whichever guard is removed — ⭐ *two defences
    // that hide each other are one defence and one thing nobody will notice breaking.* Found by a
    // mutation that deleted the save-side check and broke nothing.
    test('a nonsense id is never written to storage at all', () async {
      await ManagerStore().save(0);
      await ManagerStore().save(-5);

      final prefs = await SharedPreferences.getInstance();
      expect(
        prefs.getInt('fpl_manager_id'),
        isNull,
        reason: 'junk reached storage',
      );
      expect(await ManagerStore().load(), isNull);
    });

    test('and a junk value already in storage is not returned', () async {
      // ⭐ The other half: `load` still defends, because a preference file can be edited or corrupted
      // by something that never went through `save`.
      SharedPreferences.setMockInitialValues({'fpl_manager_id': 0});
      expect(await ManagerStore().load(), isNull);
    });

    test('clearing it returns to knowing nobody', () async {
      await ManagerStore().save(2885974);
      await ManagerStore().clear();
      expect(await ManagerStore().load(), isNull);
    });
  });

  group('WelcomeView', () {
    testWidgets('it asks, and says what the id is for', (tester) async {
      await tester.pumpWidget(wrap(WelcomeView(onManagerId: (_) async {})));
      expect(find.textContaining('FPL manager ID'), findsOneWidget);
      // ⭐ An app asking for an identifier owes the reader both what it is for and what it is not.
      expect(find.textContaining('no password'), findsOneWidget);
      expect(
        find.textContaining('nothing here can change your real team'),
        findsOneWidget,
      );
    });

    testWidgets('a valid id is handed back', (tester) async {
      int? given;
      await tester.pumpWidget(
        wrap(WelcomeView(onManagerId: (id) async => given = id)),
      );
      await tester.enterText(find.byType(TextField), '2885974');
      await tester.tap(find.text('Show me my team'));
      await tester.pump();
      expect(given, 2885974);
    });

    // ⚠️ Answered without a round trip — "that is not a number" beats "manager not found".
    testWidgets('nonsense is refused locally, not by the API', (tester) async {
      int? given;
      await tester.pumpWidget(
        wrap(WelcomeView(onManagerId: (id) async => given = id)),
      );
      await tester.enterText(find.byType(TextField), 'not a number');
      await tester.tap(find.text('Show me my team'));
      await tester.pump();

      expect(given, isNull, reason: 'it must not be handed on');
      expect(
        find.textContaining('does not look like a manager id'),
        findsOneWidget,
      );
    });

    testWidgets('an empty box is refused too', (tester) async {
      int? given;
      await tester.pumpWidget(
        wrap(WelcomeView(onManagerId: (id) async => given = id)),
      );
      await tester.tap(find.text('Show me my team'));
      await tester.pump();
      expect(given, isNull);
    });

    testWidgets('it offers a way to find the id', (tester) async {
      await tester.pumpWidget(wrap(WelcomeView(onManagerId: (_) async {})));
      // ⭐ "The number in your team URL" is only obvious to someone who already knows.
      expect(find.text('Where do I find it?'), findsOneWidget);
    });
  });

  group('the app shell', () {
    // ⚠️⚠️ **This is the path a tester actually hits**: correct the id in Settings, close the app,
    // reopen. It used to forget. ⭐ *A setting that does not persist is a setting that was never really
    // offered.*
    testWidgets('changing the manager id in Settings persists it', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(500, 3000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      final client = ServiceClient(
        baseUrl: 'http://test',
        client: MockClient(
          (_) async => http.Response(
            File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
                .readAsStringSync(),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          ),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: MyTeamScreen(
            baseUrl: 'http://test',
            managerId: 111,
            client: client,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('More'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Settings'));
      await tester.pumpAndSettle();

      await tester.enterText(find.widgetWithText(TextField, '111'), '7654321');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();

      expect(
        await ManagerStore().load(),
        7654321,
        reason: 'the id a manager typed must outlive the launch',
      );
    });
  });

  group('no manager id is baked into the app', () {
    // ⚠️⚠️ The defect itself: a const in the source meant every install opened on one person's squad.
    test('the author\'s id appears nowhere in lib/', () async {
      final lib = Directory.current.parent.path;
      final offenders = <String>[];
      await for (final entity in Directory(
        '$lib/mobile/lib',
      ).list(recursive: true)) {
        if (entity is File && entity.path.endsWith('.dart')) {
          final text = await entity.readAsString();
          // ⭐ Only a **code** occurrence counts: the welcome screen shows it as a hint, and the
          // comment explaining the defect names it too.
          for (final line in text.split('\n')) {
            final code = line.split('//').first;
            if (code.contains('2885974')) {
              offenders.add('${entity.path}: $line');
            }
          }
        }
      }
      expect(offenders, isEmpty, reason: 'a hardcoded manager id is back');
    });
  });
}
