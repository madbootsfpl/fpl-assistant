// Mini-leagues (ADR-267) — parsed from the committed samples the server produced.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';

Map<String, dynamic> _sample(String name) => jsonDecode(
  File('../spikes/018-flutter-read-slice/api-samples/$name.json')
      .readAsStringSync(),
) as Map<String, dynamic>;

void main() {
  group('the league list', () {
    List<LeagueSummary> leagues() => [
      for (final l in _sample('leagues')['leagues'] as List)
        LeagueSummary.fromJson(l as Map<String, dynamic>),
    ];

    // ⭐ FPL mixes the league you joined with friends in among automatic ones, which are always bigger.
    test('a private league leads, however small', () {
      final list = leagues();
      expect(list.first.private, isTrue);
      expect(list.first.size, lessThan(list.last.size));
    });

    test('each one carries a name, a size and a rank', () {
      for (final l in leagues()) {
        expect(l.id, greaterThan(0));
        expect(l.name, isNotEmpty);
        expect(l.size, greaterThan(0));
      }
    });

    // ⚠️ 0 would read as *first*.
    test('an unranked manager has no rank rather than rank zero', () {
      final l = LeagueSummary.fromJson(const {
        'id': 1,
        'name': 'x',
        'rank': null,
      });
      expect(l.rank, isNull);
    });
  });

  group('the table', () {
    LeagueTable table() => LeagueTable.fromJson(_sample('league'));

    test('rows arrive in rank order with points', () {
      final rows = table().rows;
      expect(rows, isNotEmpty);
      expect(
        rows.map((r) => r.rank),
        orderedEquals([for (var i = 1; i <= rows.length; i++) i]),
      );
      expect(rows.first.total, greaterThan(0));
    });

    // ⚠️ `greaterThan(0)` was this test's first form and a fabricated 99 sailed through it — ⭐ *a bound
    // that any wrong answer also satisfies is not an assertion.* The real invariant: nobody can have been
    // captained by more managers than were actually read.
    test('it says how many squads the captain split stands on', () {
      final t = table();
      expect(t.captainsFrom, greaterThan(0));
      expect(t.captains, isNotEmpty);
      for (final pick in t.captains) {
        expect(
          pick.count,
          lessThanOrEqualTo(t.captainsFrom),
          reason: 'more captains than squads read is impossible',
        );
      }
      // ⭐ And the shares must account for every squad read, since everyone captains somebody.
      final counted = t.captains.fold<int>(0, (n, c) => n + c.count);
      expect(counted, t.captainsFrom);
    });

    // ⚠️⚠️ Null means NEW, not "level" — a manager with no previous rank has not fallen 400 places.
    test('a manager with no previous rank reads as new, not as a fall', () {
      final row = LeagueStanding.fromJson(const {
        'entry': 1,
        'manager': 'A',
        'team': 'B',
        'rank': 1,
        'movement': null,
      });
      expect(row.movement, isNull);
    });

    test('positive movement means climbing', () {
      final row = LeagueStanding.fromJson(const {
        'entry': 1,
        'rank': 3,
        'movement': 2,
      });
      expect(row.movement, 2);
    });

    test('a captain pick carries a share as well as a count', () {
      final pick = table().captains.first;
      expect(pick.count, greaterThan(0));
      expect(pick.share, greaterThan(0));
      expect(pick.player.name, isNotEmpty);
    });
  });

  group('head to head', () {
    HeadToHead h2h() => HeadToHead.fromJson(_sample('h2h'));

    test('the shared players are reported, not hidden', () {
      final h = h2h();
      expect(h.sharedCount, greaterThan(0));
      expect(h.sharedXp, greaterThan(0));
    });

    test('differentials arrive on both sides with a sentence', () {
      final h = h2h();
      expect(h.myEdge, isNotEmpty);
      expect(h.theirEdge, isNotEmpty);
      expect(h.note, isNotEmpty);
    });

    // ⭐ ADR-227's sweep found the engine's own row could not carry a status.
    test(
      'a differential carries the full player shape, so a doubt can show',
      () {
        final row = h2h().myEdge.first;
        expect(row.player.name, isNotEmpty);
        expect(row.player.status, isNotEmpty);
      },
    );

    test('a captain differential is marked as one', () {
      final all = [...h2h().myEdge, ...h2h().theirEdge];
      expect(all.where((e) => e.isCaptain), isNotEmpty);
      expect(all.where((e) => !e.isCaptain), isNotEmpty);
    });

    test('ahead is positive and behind is negative', () {
      expect(HeadToHead.fromJson(const {'gap': 2.4}).iAmAhead, isTrue);
      expect(HeadToHead.fromJson(const {'gap': -2.4}).iAmAhead, isFalse);
      // ⚠️ Dead level is not "ahead".
      expect(HeadToHead.fromJson(const {'gap': 0}).iAmAhead, isFalse);
    });

    test('an empty answer degrades rather than throwing', () {
      final h = HeadToHead.fromJson(const {});
      expect(h.myEdge, isEmpty);
      expect(h.note, isEmpty);
      expect(h.gap, 0);
    });
  });
}
