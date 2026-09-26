/// The Ask screen (ADR-302).
///
/// ⭐⭐ **The routing is a year old; the screen is what is new.** These pin what it promises: that the
/// squad and the money go with the question, that a fallback replaces the headline rather than sitting
/// beside it, and that the engine's own plain-text layout survives the trip.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/ask_view.dart';

/// The committed sample, optionally with different money.
///
/// ⚠️⚠️ **The overrides exist because the sample's own values are `1` and `null`** — which are exactly
/// the numbers a hard-coding would use. ⭐ *A fixture whose values match the bug is a fixture that cannot
/// see it*: a mutation replacing `team.freeTransfers` with `1` survived every assertion until this.
MyTeam sampleTeam({int? free, double? bank}) {
  final raw = jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>;
  if (free != null) raw['free_transfers'] = free;
  if (bank != null) (raw['squad'] as Map<String, dynamic>)['bank'] = bank;
  return MyTeam.fromJson(raw);
}

Future<void> pump(
  WidgetTester tester, {
  required Map<String, dynamic> reply,
  List<Map<String, dynamic>>? sent,
  MyTeam? team,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: AskView(
          team: team ?? sampleTeam(),
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient((request) async {
              sent?.add(jsonDecode(request.body) as Map<String, dynamic>);
              return http.Response(
                jsonEncode(reply),
                200,
                headers: const {'content-type': 'application/json'},
              );
            }),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

const _captain = {
  'question': 'who should I captain?',
  'intent': 'captain',
  'headline': "Captain pick (squad 'yours'): Saka — xP 6.7 next GW",
  'detail': 'Captain Pick\n\n🥇 Saka\n   home against BUR',
  'message': '',
  'facts': {'player': 'Saka (ARS)'},
};

void main() {
  _bankMayBeUnknown();
  testWidgets('it offers real questions before anything has been asked', (
    tester,
  ) async {
    // ⭐ *A free-text box with no examples is a box people type one thing into and give up on.*
    await pump(tester, reply: _captain);

    expect(find.text('Who should I captain?'), findsOneWidget);
    expect(find.text('What should I do this week?'), findsOneWidget);
    expect(find.textContaining('in your own words'), findsOneWidget);
  });

  testWidgets('tapping an example asks it', (tester) async {
    final sent = <Map<String, dynamic>>[];
    await pump(tester, reply: _captain, sent: sent);

    await tester.tap(find.text('Who should I captain?'));
    await tester.pumpAndSettle();

    expect(sent, hasLength(1));
    expect(sent.first['question'], 'Who should I captain?');
    expect(find.textContaining('Saka'), findsWidgets);
  });

  testWidgets('the squad and the money go with the question', (tester) async {
    // ⚠️⚠️ **`ask.py` records this defect at its own call site**: free transfers and the bank were
    // *"hard-coded here (1 and £0.0m) while the Transfer tab collected them three tabs away, so the
    // surface a manager reads was advising a position he was not in."* ⭐ *A plan that ignores what you
    // can afford is a plan for somebody else.*
    final sent = <Map<String, dynamic>>[];
    // ⭐ Deliberately **not** 1 and 0 — see `sampleTeam`.
    final team = sampleTeam(free: 3, bank: 4.5);
    await pump(tester, reply: _captain, sent: sent, team: team);

    await tester.tap(find.text('What should I do this week?'));
    await tester.pumpAndSettle();

    final body = sent.single;
    expect((body['player_ids'] as List), hasLength(15));
    expect((body['bench_ids'] as List), hasLength(4));
    expect(body['free'], 3);
    expect(body['bank'], 4.5);
  });

  testWidgets("the engine's own layout survives the trip", (tester) async {
    // ⭐ It indents and bullets in plain text, and *a renderer that re-flowed it would be a second
    // opinion about how the answer reads.*
    await pump(tester, reply: _captain);
    await tester.tap(find.text('Who should I captain?'));
    await tester.pumpAndSettle();

    expect(find.textContaining('🥇 Saka'), findsOneWidget);
    expect(find.textContaining('home against BUR'), findsOneWidget);
    expect(find.text(_captain['headline']! as String), findsOneWidget);
  });

  testWidgets(
    'an unrecognised question shows the fallback INSTEAD of a headline',
    (tester) async {
      // ⚠️⚠️ An unrecognised question routes to `chat`, whose whole answer is a list of what it *can* be
      // asked. ⭐ *A free-text box that only ever says "I don't understand" teaches people to stop typing.*
      await pump(
        tester,
        reply: const {
          'question': 'what is the airspeed velocity of an unladen swallow?',
          'intent': 'chat',
          'headline': '',
          'detail': '',
          'message': 'I can answer about:\n  • captaincy\n  • transfers',
          'facts': <String, dynamic>{},
        },
      );
      await tester.tap(find.text('Who should I captain?'));
      await tester.pumpAndSettle();

      expect(find.textContaining('I can answer about'), findsOneWidget);
      expect(find.textContaining('captaincy'), findsOneWidget);
    },
  );

  testWidgets('the examples get out of the way once something is asked', (
    tester,
  ) async {
    await pump(tester, reply: _captain);
    expect(find.text('Who should I transfer?'), findsOneWidget);

    await tester.tap(find.text('Who should I captain?'));
    await tester.pumpAndSettle();

    expect(find.text('Who should I transfer?'), findsNothing);
  });

  testWidgets('an empty box asks nothing', (tester) async {
    // ⚠️ The server refuses it anyway; ⭐ *a request that cannot succeed should not leave the device.*
    final sent = <Map<String, dynamic>>[];
    await pump(tester, reply: _captain, sent: sent);

    await tester.tap(find.byIcon(Icons.arrow_upward));
    await tester.pumpAndSettle();

    expect(sent, isEmpty);
  });

  testWidgets('a failure names itself and keeps the box', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AskView(
            team: sampleTeam(),
            client: ServiceClient(
              baseUrl: 'http://x',
              client: MockClient((_) async => http.Response('nope', 500)),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Who should I captain?'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.textContaining('did not reach the engine'), findsOneWidget);
    // ⭐ And you can try again without leaving the screen.
    expect(find.byType(TextField), findsOneWidget);
  });
}

void _bankMayBeUnknown() {
  testWidgets('an unpublished bank is sent as zero, not as null', (
    tester,
  ) async {
    // ⚠️ `bank` is nullable on `MyTeam` — FPL does not always publish it — and the engine takes a
    // number. ⭐ *Zero is the honest substitute here*, unlike on a display where it would read as "you
    // are skint": the engine is being told what you can spend, and "unknown" spends nothing.
    final sent = <Map<String, dynamic>>[];
    await pump(tester, reply: _captain, sent: sent);

    await tester.tap(find.text('Who should I captain?'));
    await tester.pumpAndSettle();

    expect(sampleTeam().bank, isNull, reason: 'the sample changed');
    expect(sent.single['bank'], 0);
  });
}
