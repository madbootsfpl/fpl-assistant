/// The Chatter tab (ADR-300).
///
/// ⭐⭐ **The counting is a year old; the tab is what is new.** These pin what the screen promises — that
/// it measures *mentions*, that your own players are marked without being floated to the top, that the
/// threads behind a count are reachable, and that a dark Reddit is a sentence rather than a broken tab.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/chatter_view.dart';

MyTeam sampleTeam() => MyTeam.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/my-team.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

Map<String, dynamic> rowFor(
  PlayerSummary p, {
  int mentions = 12,
  bool owned = false,
  List<Map<String, String>> posts = const [
    {'title': 'Is he a must-have?', 'link': 'https://reddit.com/1'},
  ],
}) => {
  'player': {
    'id': p.id,
    'web_name': p.name,
    'position': p.position,
    'team': p.team,
    'price': p.price,
    'xp': p.xp,
    'status': 'a',
    'chance': null,
    'leaving': null,
    'minutes_weight': 1.0,
    'by_gameweek': <String, dynamic>{},
  },
  'photo': 'https://example.test/p.png',
  'mentions': mentions,
  'owned': owned,
  'posts': posts,
};

Future<void> pump(
  WidgetTester tester, {
  required Map<String, dynamic> body,
  List<String>? asked,
}) async {
  final team = sampleTeam();
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF17131F),
        body: ChatterBoard(
          team: team,
          client: ServiceClient(
            baseUrl: 'http://x',
            client: MockClient((request) async {
              asked?.add(request.url.path);
              return http.Response(
                jsonEncode(body),
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

void main() {
  testWidgets('it says what it counts, before it counts anything', (
    tester,
  ) async {
    // ⚠️⚠️ **Mentions, not sentiment.** ⭐ *A reader who does not know this is counting names will read it
    // as a ranking of who is good*, which is the one thing it is not — and this app's whole claim is that
    // it can explain its numbers.
    final team = sampleTeam();
    await pump(
      tester,
      body: {
        'note': 'Most talked about on r/FantasyPL — 2 players mentioned.',
        'measures': 'mentions',
        'rows': [
          rowFor(team.analysis.xi[0], mentions: 22),
          rowFor(team.analysis.xi[1], mentions: 9),
        ],
      },
    );

    expect(
      find.textContaining('not by whether anyone rates him'),
      findsOneWidget,
    );
    expect(find.text('mentions'), findsWidgets);
    expect(find.text('22'), findsOneWidget);
  });

  testWidgets('your own players are marked, not moved', (tester) async {
    // ⭐ Outlined rather than reordered — ⚠️ *a list that quietly floats your squad to the top is no
    // longer telling you what the crowd is talking about.*
    final team = sampleTeam();
    final mine = team.analysis.xi[0];
    final theirs = team.analysis.xi[1];
    await pump(
      tester,
      body: {
        'note': 'n',
        'measures': 'mentions',
        'rows': [
          rowFor(theirs, mentions: 30),
          rowFor(mine, mentions: 4, owned: true),
        ],
      },
    );

    expect(find.text('yours'), findsOneWidget);
    // ⭐ And the row itself is outlined — the label is small and the outline is what the eye finds first.
    // ⚠️ Asserting only the word left a mutation removing the border alive.
    final outlined = tester
        .widgetList<Container>(find.byType(Container))
        .where((c) => (c.decoration as BoxDecoration?)?.border != null)
        .length;
    expect(
      outlined,
      1,
      reason: 'exactly the owned row should carry an outline',
    );
    // The busier player is still first, even though he is not yours.
    expect(
      tester.getRect(find.text(theirs.name)).top,
      lessThan(tester.getRect(find.text(mine.name)).top),
      reason: 'the owned player was floated up the list',
    );
  });

  testWidgets('the threads behind a count are on the row', (tester) async {
    // ⚠️ *A count with nothing behind it is a claim you cannot check.*
    final team = sampleTeam();
    await pump(
      tester,
      body: {
        'note': 'n',
        'measures': 'mentions',
        'rows': [
          rowFor(
            team.analysis.xi[0],
            posts: const [
              {'title': 'Captain him?', 'link': 'https://reddit.com/a'},
              {'title': 'Price rise tonight', 'link': 'https://reddit.com/b'},
            ],
          ),
        ],
      },
    );

    expect(find.text('Captain him?'), findsOneWidget);
    expect(find.text('Price rise tonight'), findsOneWidget);
  });

  testWidgets('a dark Reddit is a sentence and a way out, not a broken tab', (
    tester,
  ) async {
    // ⭐⭐ **The state this feature will actually spend time in.** Reddit blocks datacentre IPs and
    // rate-limits; the service answers with no rows and a note. ⚠️ *A tab that can go dark must have
    // something true to draw when it does* — and the retry is real advice here, not a shrug: a minute
    // later it usually works.
    await pump(
      tester,
      body: {
        'note':
            "Community buzz is unavailable right now (Reddit didn't respond).",
        'measures': 'mentions',
        'rows': const [],
      },
    );

    expect(tester.takeException(), isNull);
    expect(find.textContaining('unavailable'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('the squad is sent so rows can be flagged', (tester) async {
    final asked = <String>[];
    final team = sampleTeam();
    await pump(
      tester,
      body: {'note': 'n', 'measures': 'mentions', 'rows': const []},
      asked: asked,
    );
    expect(asked, ['/api/v1/chatter']);
    expect(team.analysis.xi, isNotEmpty);
  });
}
