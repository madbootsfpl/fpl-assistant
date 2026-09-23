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
}
