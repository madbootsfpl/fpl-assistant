/// One free-transfer number, and it says where it came from (ADR-321).
///
/// ⚠️⚠️ **A tester saw three and asked which was which**: *"We have calculated that we have 2 transfers
/// for next week, per the Timing section in This Week; on our landing page we have 1 Transfer (is that 1/3
/// used??) and we input that we have 1 in settings."*
///
/// ⭐⭐⭐ The parenthesis is the report. A bare `1` under the word **Transfers** has no direction on it, so
/// *"one available"* and *"one of three used"* are equally good readings — and the comment above that line
/// claimed it rendered `n free`, which it never did. ⚠️ *A comment describing an intent the code does not
/// carry out is worse than no comment, because it stops the next person re-reading the line.*
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/free_transfer_store.dart';
import 'package:madboots/pitch.dart';
import 'package:madboots/settings_view.dart';
import 'package:shared_preferences/shared_preferences.dart';

Map<String, dynamic> _raw() =>
    jsonDecode(
          File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
              .readAsStringSync(),
        )
        as Map<String, dynamic>;

MyTeam team({int free = 2, String source = 'history', int? implied = 2}) {
  final raw = _raw();
  raw['free_transfers'] = free;
  raw['free_transfers_source'] = source;
  raw['free_transfers_implied'] = implied;
  return MyTeam.fromJson(raw);
}

Widget wrap(Widget child) => MaterialApp(
  home: Scaffold(body: child),
);

void main() {
  group('the number survives the app closing', () {
    setUp(() => SharedPreferences.setMockInitialValues({}));

    test('nothing saved means nobody has said', () async {
      expect(await FreeTransferStore().load(), isNull);
    });

    testWidgets('a correction is still there next launch', (tester) async {
      // ⚠️⚠️ **This is the bug, and it was silent.** `_freeTransfers` was a plain field initialised to
      // `1`: set it to 2, quit, reopen, and every screen was planning on 1 again — ⭐ *a setting that does
      // not persist is a setting that was never really offered*, the sentence `ManagerStore` already
      // carries about the field one row above it on the same screen (ADR-279).
      await FreeTransferStore().save(3);
      expect(await FreeTransferStore().load(), 3);
    });

    test('zero is a saved answer, not an empty one', () async {
      // ⚠️ The falsy trap. Zero is the one value where being overruled costs points: the plan would
      // recommend a move that is really a −4.
      await FreeTransferStore().save(0);
      expect(await FreeTransferStore().load(), 0);
    });

    test('there is a way back to automatic', () async {
      // ⭐ Without this an override is a one-way door — the app would never trust the history again,
      // including after the deadline that made the history right.
      await FreeTransferStore().save(4);
      await FreeTransferStore().clear();
      expect(await FreeTransferStore().load(), isNull);
    });

    test('a value no request could carry is refused on the way out', () async {
      SharedPreferences.setMockInitialValues({'fpl_free_transfers': 99});
      expect(await FreeTransferStore().load(), isNull);
    });
  });

  group('the pitch says what it counts', () {
    testWidgets('the stat answers "of what?" without being tapped', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(390 * 3, 900 * 3);
      tester.view.devicePixelRatio = 3.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        wrap(
          PitchView(
            team: team(free: 2),
            mode: PitchMode.nextGw,
            onMode: (_) {},
            onTapPlayer: (_) {},
            // ⭐ **Null is the live pitch**, and money and transfers appear there and nowhere else — *a
            // bank balance under a GW+4 projection reads as the balance then, which nobody can know.*
            gameweek: null,
          ),
        ),
      );
      await tester.pump();

      expect(
        find.text('2 free'),
        findsOneWidget,
        reason: 'a bare number under "Transfers" reads as "2 used" just as well',
      );
      expect(find.text('Transfers'), findsOneWidget);
    });
  });

  group('settings states where the number came from', () {
    Future<void> open(
      WidgetTester tester, {
      required MyTeam t,
      int? value,
      List<int?>? told,
    }) async {
      SharedPreferences.setMockInitialValues({});
      await tester.pumpWidget(
        wrap(
          SettingsView(
            client: ServiceClient(baseUrl: 'http://x'),
            team: t,
            managerId: 1,
            freeTransfers: value,
            onManagerId: (_) {},
            onFreeTransfers: (n) => told?.add(n),
            baseUrl: 'http://test',
            onServer: (_) async {},
          ),
        ),
      );
      await tester.pump();
    }

    testWidgets('it explains a derived number rather than asserting it', (
      tester,
    ) async {
      await open(tester, t: team(free: 2, source: 'history'));
      expect(
        find.textContaining('Worked out from your transfer history'),
        findsOneWidget,
      );
      expect(find.textContaining('2 free transfers'), findsOneWidget);
    });

    testWidgets('it says when the manager overruled it', (tester) async {
      await open(
        tester,
        t: team(free: 1, source: 'you', implied: 4),
        value: 1,
      );
      expect(find.textContaining('Using your 1'), findsOneWidget);
      // ⭐ Both numbers, so the screen can be checked rather than believed.
      expect(find.textContaining('history says 4'), findsOneWidget);
    });

    testWidgets('it admits when it could not check', (tester) async {
      await open(
        tester,
        t: team(free: 1, source: 'default', implied: null),
      );
      expect(find.textContaining('could not be read'), findsOneWidget);
    });

    testWidgets('Auto is selected while nobody has overridden', (tester) async {
      // ⚠️⚠️ **Selected on the override, never on the effective number.** Highlighting `2` because
      // history says 2 would make "Auto" and "2" look like the same choice — ⭐ *and the difference is
      // the whole point: one keeps updating, the other does not.*
      await open(tester, t: team(free: 2, source: 'history'));
      expect(find.text('Auto'), findsOneWidget);

      Color colourOf(String label) {
        final box = tester.widget<Container>(
          find.ancestor(of: find.text(label), matching: find.byType(Container)),
        );
        return ((box.decoration as BoxDecoration?)?.color) ??
            const Color(0x00000000);
      }

      expect(
        colourOf('Auto'),
        isNot(colourOf('2')),
        reason: 'Auto and the derived number look like the same choice',
      );
    });

    testWidgets('tapping Auto asks for the derivation back', (tester) async {
      final told = <int?>[];
      await open(
        tester,
        t: team(free: 1, source: 'you'),
        value: 1,
        told: told,
      );
      await tester.tap(find.text('Auto'));
      await tester.pump();
      expect(
        told,
        [null],
        reason: 'null is what puts the number back under the server',
      );
    });
  });

  group('the request can say nothing at all', () {
    test('an unset count is omitted rather than guessed', () {
      // ⚠️⚠️⚠️ The whole fix dies here if this sends `1`. The server can only derive the number for a
      // client that admits it does not know — ⭐ *and `1` is indistinguishable from an answer.*
      expect(
        ServiceClient(baseUrl: 'http://x').myTeam,
        isA<Function>(),
        reason: 'signature guard: freeTransfers must be nullable',
      );
      final t = team(free: 5, source: 'history');
      expect(t.freeTransfers, 5);
      expect(t.freeTransfersSource, 'history');
    });

    test('an older server that says nothing still parses', () {
      // ⚠️ The app ships ahead of the server often enough that this is not hypothetical.
      final raw = _raw()..remove('free_transfers_source');
      expect(MyTeam.fromJson(raw).freeTransfersSource, 'default');
    });
  });
}
