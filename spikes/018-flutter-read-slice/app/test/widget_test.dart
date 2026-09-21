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
}
