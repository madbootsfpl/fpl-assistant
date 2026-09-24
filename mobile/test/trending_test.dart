// The crowd's boards (ADR-266), parsed from the committed sample the server produced.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/trending_view.dart';

TrendingBoard sample() => TrendingBoard.fromJson(
  jsonDecode(
    File('../spikes/018-flutter-read-slice/api-samples/trending.json')
        .readAsStringSync(),
  ) as Map<String, dynamic>,
);

void main() {
  group('parsing', () {
    test('the board names itself and its column', () {
      final board = sample();
      expect(board.by, 'in');
      expect(board.label, isNotEmpty);
      expect(board.column, isNotEmpty);
    });

    // ⚠️⚠️ The weakest evidence in the app has to say so, and the words come from the server.
    test('the caveat arrives with the numbers', () {
      expect(sample().caveat, contains('other managers'));
    });

    test('rows carry a player, a face and ownership', () {
      final board = sample();
      expect(board.rows, isNotEmpty);
      for (final row in board.rows) {
        expect(row.player.name, isNotEmpty);
        expect(row.photo, isNotEmpty);
        expect(row.ownedBy, isNotNull);
      }
    });

    test('nothing is flagged as owned when no squad was sent', () {
      expect(sample().rows.any((r) => r.owned), isFalse);
    });

    test('a missing board degrades to empty rather than throwing', () {
      final board = TrendingBoard.fromJson(const {});
      expect(board.rows, isEmpty);
      expect(board.by, 'in');
    });
  });

  // ⭐ Net transfers are *people*: a raw six-digit count is a number you have to parse before you can
  // compare two of them.
  group('trendValue', () {
    test('thousands read as k', () {
      expect(trendValue(660754, 'Net in'), '661k');
      expect(trendValue(1500, 'Net in'), '2k');
    });

    test('millions read as m', () {
      expect(trendValue(2400000, 'Net in'), '2.4m');
    });

    // ⚠️ The most-sold board carries negative values, and a minus sign is the whole meaning.
    test('a sale keeps its sign', () {
      expect(trendValue(-281131, 'Net out'), startsWith('−'));
      expect(trendValue(-281131, 'Net out'), contains('281k'));
    });

    test('small counts are not rounded away to 0k', () {
      expect(trendValue(412, 'Net in'), '412');
    });

    test('ownership reads as a percentage', () {
      expect(trendValue(27.6, 'Own%'), '27.6%');
    });

    test('form keeps a decimal and gains no suffix', () {
      expect(trendValue(6.2, 'Form'), '6.2');
    });
  });

  group('which board leads', () {
    /// ⚠️⚠️ **Nothing pinned this, and it has now been changed twice on feedback.** Both times the whole
    /// suite stayed green — ⭐ *an order no test names is an order the next edit can reverse by accident,
    /// and the only reader who notices is the owner.*
    final source = File('lib/trending_view.dart').readAsStringSync();

    /// The pill list, in the order it is written.
    List<String> pills() =>
        RegExp(r"\('(\w+)', '([^']+)'\)")
            .allMatches(source)
            .map((m) => m[2]!)
            .toList();

    test('Worth noticing is the first pill', () {
      expect(pills().first, 'Worth noticing');
    });

    test('Worth a look is second', () {
      // ⭐ The two player-centred boards stay at the front; the four about other managers stay behind
      // them, because *leading with the crowd teaches the screen to be read as a popularity chart.*
      expect(pills()[1], 'Worth a look');
      expect(pills().sublist(2), [
        'Most bought',
        'Most sold',
        'Most owned',
        'In form',
      ]);
    });

    test('the screen opens on the pill that leads', () {
      // ⚠️ Order and default are one decision. A first pill that is not the selected one is a row that
      // opens mid-way along itself.
      expect(source, contains("String _by = 'watch';"));
    });
  });
}
