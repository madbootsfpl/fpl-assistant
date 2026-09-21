// The slice's own guard: the sums must match the engine's, or the phone and the web disagree.
import 'package:board_slice/board.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a horizon total is the sum of the first N gameweeks, unrounded', () {
    final row = BoardRow(
      name: 'Saka', team: 'ARS', position: 'MID',
      byGameweek: {6: 6.747, 7: 6.1336, 8: 6.1336, 9: 5.5202, 10: 6.747},
    );
    // ⭐ Sum the EXACT values. Summing rounded ones drifts — ADR-213 measured that at up to 0.2 points
    // across 253 of 662 players, which is why the board publishes full precision.
    expect(row.xpOver(1), closeTo(6.747, 1e-9));
    expect(row.xpOver(3), closeTo(6.747 + 6.1336 + 6.1336, 1e-9));
    expect(row.xpOver(5), closeTo(31.2814, 1e-9));
  });

  test('a shorter horizon takes the earliest gameweeks, not the largest', () {
    final row = BoardRow(
      name: 'X', team: 'Y', position: 'MID',
      byGameweek: {10: 9.0, 6: 1.0, 8: 5.0},
    );
    // ⚠️ Keys arrive in whatever order PostgREST sent them. "The next N gameweeks" means sorted by
    // gameweek, never by value — a client that took the biggest would flatter every player.
    expect(row.xpOver(1), closeTo(1.0, 1e-9));
    expect(row.xpOver(2), closeTo(6.0, 1e-9));
  });

  test('by_gameweek parses whether PostgREST sends JSON or a JSON string', () {
    final asString = BoardRow.fromJson({
      'web_name': 'A', 'team': 'ARS', 'position': 'FWD',
      'by_gameweek': '{"6": 1.5, "7": 2.5}',
    });
    final asMap = BoardRow.fromJson({
      'web_name': 'A', 'team': 'ARS', 'position': 'FWD',
      'by_gameweek': {'6': 1.5, '7': 2.5},
    });
    expect(asString.byGameweek, asMap.byGameweek);
    expect(asString.xpOver(2), closeTo(4.0, 1e-9));
  });

  test('a total sitting exactly on a half-tenth is flagged', () {
    // ⭐ The only place Dart and Python can disagree. Python's answer on these is neither banker's nor
    // half-up — 0.55 → 0.6, 1.95 → 1.9, 5.85 → 5.8, whichever binary float is nearest — so no Dart
    // rounding mode reproduces it and the client has to find the cases instead of hoping to miss them.
    final onBoundary = BoardRow(
      name: 'A', team: 'X', position: 'MID', byGameweek: {6: 0.30, 7: 0.25},
    );
    expect(onBoundary.xpOver(2), closeTo(0.55, 1e-9));
    expect(onBoundary.atRoundingBoundary(2), isTrue);

    final safe = BoardRow(
      name: 'B', team: 'X', position: 'MID', byGameweek: {6: 0.30, 7: 0.22},
    );
    expect(safe.atRoundingBoundary(2), isFalse);
  });

  test('a long decimal is not mistaken for a boundary', () {
    // ⚠️ Real board values have many decimals (6.747, 5.5202). Only an exact half-hundredth counts;
    // treating anything near one as risky would flag most of the board and mean nothing.
    final row = BoardRow(
      name: 'C', team: 'X', position: 'MID', byGameweek: {6: 6.747, 7: 6.1336},
    );
    expect(row.atRoundingBoundary(2), isFalse);
  });

  test('a near-boundary value is not flagged', () {
    // ⚠️ The bug in the first detector. 7.249999999999998 is not ambiguous — both platforms round it to
    // 7.2 — but a 1e-6 tolerance called it a boundary and turned 5 real cases into 16 reported ones.
    final near = BoardRow(
      name: 'Gomes', team: 'X', position: 'MID',
      byGameweek: {6: 3.624999999999999, 7: 3.624999999999999},
    );
    expect(near.xpOver(2), closeTo(7.25, 1e-10));
    expect(near.atRoundingBoundary(2), isFalse,
        reason: 'a value whose shortest form is not exactly two decimals is not a boundary');
  });
}
