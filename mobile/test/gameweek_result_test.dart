/// Reading a played gameweek (ADR-298).
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madboots/api/client.dart';
import 'package:madboots/api/models.dart';

/// ⚠️⚠️ **Through a real JSON round trip**, because a Dart map literal is not typed like decoded JSON:
/// `{}` is a `_Map<dynamic, dynamic>` and the model's cast expects what `jsonDecode` produces. ⭐ *A
/// fixture built by hand tests the parser against a shape the network never sends* — three of these
/// failed on exactly that, and the product was fine.
Map<String, dynamic> json_(Object o) =>
    jsonDecode(jsonEncode(o)) as Map<String, dynamic>;

Map<String, dynamic> entry({
  int id = 1,
  int points = 6,
  bool captain = false,
  bool benched = false,
  bool cameOn = false,
  int yellow = 0,
  bool played = true,
}) => json_({
  'player': {
    'id': id,
    'web_name': 'P$id',
    'position': 'MID',
    'team': 'ARS',
    'price': 5.0,
    'xp': 0.0,
    'status': 'a',
    'chance': null,
    'leaving': null,
    'minutes_weight': 1.0,
    'by_gameweek': {},
  },
  'result': {
    'points': points,
    'minutes': 90,
    'goals': 1,
    'assists': 0,
    'bonus': 1,
    'saves': 0,
    'clean_sheet': false,
    'yellow_cards': yellow,
    'red_cards': 0,
    'played': played,
  },
  'pick': {
    'multiplier': captain ? 2 : 1,
    'is_captain': captain,
    'is_vice_captain': false,
    'benched': benched,
    'came_on': cameOn,
    'went_off': false,
  },
});

ServiceClient serving(Map<String, dynamic> body, {List<String>? seen}) =>
    ServiceClient(
      baseUrl: 'http://test',
      client: MockClient((request) async {
        seen?.add(request.body);
        return http.Response(
          jsonEncode(body),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

void main() {
  group('reading a week', () {
    test('the squad splits into the eleven and the bench', () {
      final r = GameweekResult.fromJson(
        json_({
          'gameweek': 5,
          'played': true,
          'squad': [
            for (var i = 0; i < 15; i++) entry(id: i, benched: i >= 11),
          ],
          'summary': {'points': 77, 'overall_rank': 3842466},
        }),
      );

      expect(r.xi, hasLength(11));
      expect(r.bench, hasLength(4));
      expect(r.summary.points, 77);
    });

    test('a zero is not the same as a blank', () {
      // ⚠️⚠️ ⭐ *A zero that means "he did not play" must not draw like a zero that means "he played
      // badly"* — the two are distinguished by `didPlay`, never by the score.
      final blank = GameweekPlayer.fromJson(entry(points: 0, played: false));
      final bad = GameweekPlayer.fromJson(entry(points: 0, played: true));

      expect(blank.didPlay, isFalse);
      expect(bad.didPlay, isTrue);
      expect(blank.points, bad.points);
    });

    test('an unplayed week parses as empty rather than failing', () {
      final r = GameweekResult.fromJson({
        'gameweek': 38,
        'played': false,
        'squad': [],
        'summary': {},
      });

      expect(r.played, isFalse);
      expect(r.squad, isEmpty);
      expect(
        r.summary.points,
        isNull,
        reason: 'null is "not known", never zero',
      );
    });

    test('cards and the armband survive the round trip', () {
      final p = GameweekPlayer.fromJson(
        entry(captain: true, yellow: 1, cameOn: true),
      );

      expect(p.yellowCards, 1);
      expect(p.isCaptain, isTrue);
      expect(p.cameOn, isTrue);
    });
  });

  group('the cache', () {
    test('a played week is fetched once and kept', () async {
      final calls = <String>[];
      final client = serving({
        'gameweek': 5,
        'played': true,
        'squad': [entry()],
        'summary': {'points': 40},
      }, seen: calls);

      await client.gameweekResult(1, 5);
      await client.gameweekResult(1, 5);
      await client.gameweekResult(1, 5);

      // ⭐⭐ *A cache whose entries can never go stale is the only kind that needs no invalidation.*
      expect(calls, hasLength(1));
    });

    test('an unplayed week is asked again', () async {
      // ⚠️⚠️ ⭐ *Caching "it has not happened yet" is how a screen stays empty after it has.*
      final calls = <String>[];
      final client = serving({
        'gameweek': 38,
        'played': false,
        'squad': [],
        'summary': {},
      }, seen: calls);

      await client.gameweekResult(1, 38);
      await client.gameweekResult(1, 38);

      expect(calls, hasLength(2));
    });

    test('each gameweek is cached separately', () async {
      final calls = <String>[];
      final client = serving({
        'gameweek': 5,
        'played': true,
        'squad': [entry()],
        'summary': {},
      }, seen: calls);

      await client.gameweekResult(1, 4);
      await client.gameweekResult(1, 5);
      await client.gameweekResult(1, 4);

      expect(calls, hasLength(2));
    });
  });
}
