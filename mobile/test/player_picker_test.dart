// Sifting a long list of players (ADR-264).
//
// ⭐ The picker's chrome is layout; `siftPlayers` is the behaviour, so that is what is pinned here.
import 'package:flutter_test/flutter_test.dart';
import 'package:madboots/api/models.dart';
import 'package:madboots/player_picker.dart';

PlayerSummary p(String name, String team, double price, double xp) =>
    PlayerSummary(
      id: name.hashCode,
      name: name,
      team: team,
      position: 'MID',
      price: price,
      xp: xp,
      status: 'a',
      chance: null,
      minutesWeight: 1,
      leaving: null,
      byGameweek: const {},
    );

final squad = [
  p('Salah', 'LIV', 12.5, 6.2),
  p('Saka', 'ARS', 10.0, 5.1),
  p('Palmer', 'CHE', 10.5, 5.8),
  p('Rice', 'ARS', 6.5, 3.4),
];

void main() {
  PlayerSummary of(PlayerSummary x) => x;

  group('siftPlayers', () {
    test('defaults to xP order, best first — the reason to be here', () {
      final out = siftPlayers(squad, of);
      expect(out.map((x) => x.name), ['Salah', 'Palmer', 'Saka', 'Rice']);
    });

    test('price sorts cheapest first, because it answers "what can I afford?"', () {
      final out = siftPlayers(squad, of, sort: PickerSort.price);
      expect(out.first.name, 'Rice');
      expect(out.last.name, 'Salah');
    });

    test('name and club each sort alphabetically', () {
      expect(siftPlayers(squad, of, sort: PickerSort.name).first.name, 'Palmer');
      expect(siftPlayers(squad, of, sort: PickerSort.club).first.team, 'ARS');
    });

    test('search matches a name', () {
      final out = siftPlayers(squad, of, query: 'sal');
      expect(out.single.name, 'Salah');
    });

    // ⚠️ "spurs" is how someone looks for a player whose name they cannot spell.
    test('search matches a club too, not just a name', () {
      final out = siftPlayers(squad, of, query: 'ars');
      expect(out.map((x) => x.name), containsAll(['Saka', 'Rice']));
      expect(out.length, 2);
    });

    test('search ignores case and surrounding space', () {
      expect(siftPlayers(squad, of, query: '  SALAH ').single.name, 'Salah');
    });

    test('a club filter narrows to that club', () {
      final out = siftPlayers(squad, of, club: 'ARS');
      expect(out.every((x) => x.team == 'ARS'), isTrue);
      expect(out.length, 2);
    });

    test('club and search combine rather than replace each other', () {
      expect(siftPlayers(squad, of, club: 'ARS', query: 'saka').single.name, 'Saka');
      expect(siftPlayers(squad, of, club: 'LIV', query: 'saka'), isEmpty);
    });

    test('no query and no club keeps everyone', () {
      expect(siftPlayers(squad, of).length, squad.length);
    });

    // ⚠️ The picker is handed lists it does not own.
    test('the input list is not reordered underneath the caller', () {
      final original = [...squad];
      siftPlayers(squad, of, sort: PickerSort.name);
      expect(squad.map((x) => x.name), original.map((x) => x.name));
    });

    test('it works on a wrapper type, which is why it is generic', () {
      final wrapped = squad.map((x) => (player: x, tag: 'x')).toList();
      final out = siftPlayers(wrapped, (w) => w.player, query: 'liv');
      expect(out.single.player.name, 'Salah');
    });
  });

  group('clubsIn', () {
    test('lists each club once, sorted — so it can never offer an empty one', () {
      expect(clubsIn(squad, of), ['ARS', 'CHE', 'LIV']);
    });

    test('an empty list has no clubs rather than throwing', () {
      expect(clubsIn(<PlayerSummary>[], of), isEmpty);
    });
  });
}
