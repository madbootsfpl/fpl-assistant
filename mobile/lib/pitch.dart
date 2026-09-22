/// The My Team pitch — the landing screen (ADR-222).
///
/// ⭐⭐ **The card is the one the web app already draws**: kit, name, white xP pill, price · fixture, with
/// the manager's own C and V. Keeping it identical is not deference to the old surface — it is the same
/// rule the API contract is pinned by. Two surfaces that draw a squad differently will eventually disagree
/// about it, and the manager has no way to tell which one is lying.
///
/// ⚠️ **Deliberately not colour-by-points.** ADR-179 declined whole-card colour on the web on the grounds
/// that it *trades a readable number for a hue*. A phone is a smaller screen and may deserve the opposite
/// answer — but that is a decision to take, not to drift into, so the card keeps the readable number.
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'brand.dart';
import 'pitch_markings.dart';

/// Formation order, so the rows come out keeper-first the way a pitch reads.
const List<String> _rows = ['GK', 'DEF', 'MID', 'FWD'];

/// What the strip under each name is showing.
///
/// ⭐⭐ **One card, three readings** (ADR-235). A manager asks three different questions of the same
/// eleven — *what will he score this week?*, *what is his run like?*, *is his price about to move?* — and
/// each used to need a different screen, or no screen at all.
enum PitchMode { nextGw, run, price }

extension on PitchMode {
  String get label => switch (this) {
    PitchMode.nextGw => 'Next GW',
    PitchMode.run => 'Next 3',
    PitchMode.price => 'Price',
  };
}

class PitchView extends StatelessWidget {
  const PitchView({
    required this.team,
    required this.onTapPlayer,
    required this.mode,
    required this.onMode,
    this.footer,
    super.key,
  });

  final MyTeam team;
  final PitchMode mode;
  final ValueChanged<PitchMode> onMode;

  /// ⭐ The pitch is the right surface for editing a squad — it is where a manager already looks to decide
  /// anything, and a tab called "Captain" would be a second place to do a thing that belongs here.
  final void Function(PlayerSummary) onTapPlayer;

  /// ⭐ Anything that belongs **on the pitch** below the bench — today, the apply-the-plan strip. It is a
  /// slot rather than a hard-coded child so the pitch does not have to know what a lineup plan is.
  final Widget? footer;

  @override
  Widget build(BuildContext context) {
    final byRow = <String, List<PlayerSummary>>{for (final r in _rows) r: []};
    for (final p in team.analysis.xi) {
      byRow[p.position]?.add(p);
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Header(team: team),
        _ModeBar(mode: mode, onMode: onMode),
        // ⭐⭐⭐ **One green area, from the mode bar to the bottom** (ADR-253). The pitch was 747px of a
        // 1932px screen with the bench floating on the dark background below it and 140px of dead space
        // under that. The competitor gives its pitch **twice** the room by letting the green run behind
        // everything — ⚠️ *a pitch that stops two thirds of the way down reads as a web page with a
        // picture on it.*
        Expanded(
          child: ClipRRect(
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(Brand.radiusMd),
            ),
            child: PitchMarkings(
              child: Column(
                children: [
                  // ⭐ The wordmark, inside the pitch. It used to have a row of its own above the header
                  // — 60px to say a name the reader already knows. On the green it is present and costs
                  // nothing, which is the trick the competitor's corner chip is playing.
                  const _PitchMark(),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(4, 0, 4, 4),
                      child: Column(
                        children: [
                          // ⚠️⚠️ **Each row `Expanded`, so the four divide whatever height there is.**
                          // With `spaceEvenly` the rows demanded their intrinsic height and overflowed by
                          // 4px on a 760pt screen once the footer was added — and a smaller phone, or a
                          // stale-data banner, would clip a whole row of shirts. ⭐ *A pitch that must be
                          // given enough room is not a pitch that fills the room it is given.*
                          for (final row in _rows)
                            if (byRow[row]!.isNotEmpty)
                              Expanded(
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceEvenly,
                                  crossAxisAlignment: CrossAxisAlignment.center,
                                  children: [
                                    for (final p in byRow[row]!)
                                      _Card(
                                        team: team,
                                        player: p,
                                        mode: mode,
                                        onTap: () => onTapPlayer(p),
                                      ),
                                  ],
                                ),
                              ),
                        ],
                      ),
                    ),
                  ),
                  // ⭐ On the green, not under it: a dark panel **sitting on** the pitch is integrated
                  // and still plainly separate, which is what the bench is.
                  Padding(
                    padding: const EdgeInsets.fromLTRB(6, 0, 6, 6),
                    child: _Bench(
                      team: team,
                      mode: mode,
                      onTapPlayer: onTapPlayer,
                    ),
                  ),
                  if (footer != null)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(6, 0, 6, 6),
                      child: footer!,
                    ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// The badge and wordmark, inside the pitch — ⭐ **present, and costing no row of its own** (ADR-253).
class _PitchMark extends StatelessWidget {
  const _PitchMark();

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(10, 7, 10, 0),
    child: Row(
      children: [
        Container(
          padding: const EdgeInsets.fromLTRB(6, 3, 9, 3),
          decoration: BoxDecoration(
            // ⚠️ A dark chip, because a wordmark straight onto grass is unreadable at this size however
            // it is coloured.
            color: Brand.ink.withValues(alpha: 0.55),
            borderRadius: BorderRadius.circular(Brand.radiusPill),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Image(
                image: AssetImage('assets/madboots-badge.png'),
                width: 15,
                height: 15,
                filterQuality: FilterQuality.medium,
              ),
              SizedBox(width: 5),
              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(
                      text: 'MAD',
                      style: TextStyle(
                        color: Brand.purpleLight,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    TextSpan(
                      text: 'BOOTS',
                      style: TextStyle(color: Brand.orange),
                    ),
                  ],
                ),
                style: TextStyle(fontSize: 10.5, letterSpacing: .3),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _Header extends StatelessWidget {
  const _Header({required this.team});

  final MyTeam team;

  @override
  Widget build(BuildContext context) {
    final a = team.analysis;
    // ⭐ The XI's own total, not the squad's. A landing number that silently included the bench would
    // flatter every team by four players who are not playing.
    final xi = a.xi.fold<double>(0, (sum, p) => sum + p.xp);
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ⭐⭐ **One line, where three were** (ADR-253). The web's banner is 96 characters and wrapped
          // to three lines here — ~40pt of the screen's most valuable space spent on a match count and a
          // first kick-off time that nobody acts on from the pitch.
          //
          // ⚠️ The **countdown stays**: near a deadline it is the only part of this line anyone reads.
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                'GW${team.gameweek ?? '—'}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  team.deadlineWhen.isEmpty
                      // ⚠️ Falls back to the prose line if the parts are absent — an older server must
                      // not leave the header blank.
                      ? team.deadlineLabel
                      : '${team.deadlineWhen} · ${team.deadlineCountdown}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white54, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _Stat(value: xi.toStringAsFixed(1), label: 'Predicted'),
              // ⚠️ FPL's bank, or an em dash — ⭐ *never £0.0m*, which is a real position and would read as
              // one. `—` says "not known"; zero says "you are skint".
              _Stat(
                value: team.bank == null
                    ? '—'
                    : '£${team.bank!.toStringAsFixed(1)}m',
                label: 'In the bank',
              ),
              _Stat(
                value: team.value == null
                    ? '—'
                    : '£${team.value!.toStringAsFixed(1)}m',
                label: 'Value',
              ),
              // ⭐ Shown as "n free" because the number is one the manager set, not one FPL published —
              // the label is the honest bit.
              _Stat(value: '${team.freeTransfers}', label: 'Transfers'),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        value,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 17,
          fontWeight: FontWeight.w700,
        ),
      ),
      Text(label, style: const TextStyle(color: Colors.white54, fontSize: 10)),
    ],
  );
}

class _Card extends StatelessWidget {
  const _Card({
    required this.team,
    required this.player,
    required this.mode,
    required this.onTap,
  });

  final MyTeam team;
  final PlayerSummary player;
  final PitchMode mode;
  final VoidCallback onTap;

  /// ⚠️ Fixed, not flexible. A five-DEF row and a one-FWD row must draw the same card, or the eye reads
  /// the wider one as more important.
  static const double width = 70;

  @override
  Widget build(BuildContext context) {
    final kit = team.kitFor(player);
    final fixture = team.fixtureFor(player);
    return GestureDetector(
      onTap: onTap,
      // ⚠️ `opaque` so the whole card is the target — the kit alone is well under a thumb's width.
      behavior: HitTestBehavior.opaque,
      // ⚠️⚠️ **`scaleDown`, so a short screen shrinks the card instead of clipping it.** With the rows
      // dividing the pitch's height, a card on a small phone can be given less than its intrinsic height,
      // and the overflow lands on the fixture strip — the part the whole redesign was about making
      // readable. ⭐ *Never up, only down: on a tall screen the card stays the size it was designed at.*
      //
      // ⚠️ The width box is **inside** the FittedBox, not outside it. A `FittedBox` hands its child
      // unbounded width, and the run's `Expanded` cells cannot lay out against that — *a box that scales
      // its child must still give it something to be a fraction of.*
      child: FittedBox(
        fit: BoxFit.scaleDown,
        child: SizedBox(
          width: width,
          child: Column(
            children: [
              SizedBox(
                height: 34,
                child: Stack(
                  alignment: Alignment.bottomCenter,
                  clipBehavior: Clip.none,
                  children: [
                    if (kit.isEmpty)
                      const Text('👕', style: TextStyle(fontSize: 22))
                    else
                      // ⚠️ A kit that fails to load must not take the pitch down — a shirt is decoration and the
                      // number beside it is the point.
                      Image.network(
                        kit,
                        height: 34,
                        errorBuilder: (_, _, _) =>
                            const Text('👕', style: TextStyle(fontSize: 22)),
                      ),
                    if (_armband != null)
                      Positioned(
                        top: -2,
                        right: 6,
                        child: _Armband(letter: _armband!),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 2),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Flexible(
                    child: Text(
                      player.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  if (_flag != null) ...[const SizedBox(width: 3), _flag!],
                ],
              ),
              const SizedBox(height: 2),
              switch (mode) {
                PitchMode.nextGw => _NextGw(player: player, fixture: fixture),
                PitchMode.run => _Run(
                  fixtures: team.runFor(player),
                  xpByGameweek: team.runXpFor(player),
                ),
                PitchMode.price => _Price(
                  move: team.priceFor(player),
                  player: player,
                ),
              },
            ],
          ),
        ),
      ),
    );
  }

  /// ⚠️ The **manager's** armband, never the engine's recommendation.
  String? get _armband {
    if (player.id == team.captainId) return 'C';
    if (player.id == team.viceCaptainId) return 'V';
    return null;
  }

  /// ⭐ Availability is three separate facts and none implies the others — a doubt is a probability
  /// (ADR-206), and a reported departure is not a status at all (ADR-155).
  Widget? get _flag {
    if (player.isLeaving) return const _Flag(text: '✈', colour: Brand.bad);
    if (player.isDoubtful) {
      return _Flag(text: '${player.chance ?? '?'}%', colour: Brand.warn);
    }
    if (player.isUnavailable) return const _Flag(text: '✚', colour: Brand.bad);
    return null;
  }
}

/// **Next GW** — the reading the app opened with: what he is projected to score, and against whom.
class _NextGw extends StatelessWidget {
  const _NextGw({required this.player, required this.fixture});

  final PlayerSummary player;
  final Fixture? fixture;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      // ⭐ The same difficulty tint as the run, so a reader learns one colour language rather than two.
      // ⚠️ White pill kept where the fixture is unknown — the neutral case should not borrow the look of
      // an average fixture, because "we do not know" and "it is a three" are different facts.
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 1.5),
        decoration: BoxDecoration(
          color: fixture?.difficulty == null
              ? Brand.surface
              : difficultyTint(fixture!.difficulty),
          borderRadius: BorderRadius.circular(Brand.radiusPill),
        ),
        child: Text(
          player.xp.toStringAsFixed(1),
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w700,
            color: fixture?.difficulty == null ? Brand.text : Colors.white,
          ),
        ),
      ),
      const SizedBox(height: 2),
      // ⚠️⚠️ **One line, always** (feedback). `£12.0m · TOT (H)` under a long name wrapped onto a second
      // line, which made that one card taller than its neighbours and pushed the whole row out of
      // alignment. ⭐ *A card that changes height with its contents stops being a grid.*
      //
      // ⭐ Shrunk to fit rather than clipped: the price and the opponent are both the point of the line,
      // and truncating either would answer a different question. `FittedBox` keeps the row's rhythm and
      // loses nothing but a fraction of a point size on the longest names.
      FittedBox(
        fit: BoxFit.scaleDown,
        child: Text(
          '£${player.price.toStringAsFixed(1)}m · ${fixture?.label ?? '—'}',
          maxLines: 1,
          softWrap: false,
          style: const TextStyle(color: Colors.white70, fontSize: 8.5),
        ),
      ),
    ],
  );
}

/// FDR as a colour — ⭐ **the app already knew this and was drawing the run in monochrome.**
///
/// ⚠️ **Null is neutral, never easy.** An unknown fixture is not a good one, and tinting it green would be
/// the app making a claim the data did not.
///
/// ⭐ Muted on purpose: these sit on a green pitch behind white text, so the tint has to say *easier* or
/// *harder* without competing with the number it is behind.
Color difficultyTint(int? difficulty) => switch (difficulty) {
  1 => Brand.good.withValues(alpha: 0.85),
  2 => Brand.good.withValues(alpha: 0.55),
  3 => Colors.black.withValues(alpha: 0.28),
  4 => Brand.warn.withValues(alpha: 0.62),
  5 => Brand.bad.withValues(alpha: 0.72),
  _ => Colors.black.withValues(alpha: 0.28),
};

/// **Next 3** — ⭐ *a manager deciding whether to HOLD a player is asking about his run, not his Saturday.*
///
/// ⚠️ The per-gameweek xP comes from `by_gameweek`, which the app has published since ADR-213 and threw
/// away on this card until now.
class _Run extends StatelessWidget {
  const _Run({required this.fixtures, required this.xpByGameweek});

  final List<Fixture> fixtures;

  /// ⭐ Handed the map rather than the player, so the card cannot silently read the wrong window again.
  final Map<int, double> xpByGameweek;

  @override
  Widget build(BuildContext context) {
    final weeks = xpByGameweek.keys.toList()..sort();
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        for (var i = 0; i < fixtures.length; i++)
          Expanded(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 1),
              padding: const EdgeInsets.symmetric(vertical: 1),
              decoration: BoxDecoration(
                // ⭐⭐⭐ **Tinted by fixture difficulty**, which the app already knew and was throwing
                // away. The run was drawn in monochrome, so reading it meant reading three numbers and
                // three club abbreviations and holding all six in your head. ⚠️ *A colour is read before
                // a number is*, and the whole point of the run is to be taken in at a glance.
                color: difficultyTint(fixtures[i].difficulty),
                borderRadius: BorderRadius.circular(3),
              ),
              child: Column(
                children: [
                  Text(
                    // ⭐ Matched by **gameweek**, not by position in the list: a blank gameweek means
                    // a club's third fixture is not the third week, and lining them up by index would
                    // quietly show the wrong number against the wrong opponent.
                    _xpFor(weeks, fixtures[i].gameweek),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    // ⚠️ Upper case home, lower case away — the convention every other run in the app
                    // uses, so a reader who has learned one has learned them all.
                    fixtures[i].venue == 'H'
                        ? fixtures[i].opponent.toUpperCase()
                        : fixtures[i].opponent.toLowerCase(),
                    maxLines: 1,
                    overflow: TextOverflow.clip,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 7.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  String _xpFor(List<int> weeks, int? gameweek) {
    if (gameweek == null) return '—';
    final value = xpByGameweek[gameweek];
    return value == null ? '—' : value.toStringAsFixed(1);
  }
}

/// **Price** — ⚠️ the direction, and the crowd movement behind it. *No "Tonight", no percentage:* the
/// engine answers rise/fall/stable against a live percentile and does not estimate *when*.
class _Price extends StatelessWidget {
  const _Price({required this.move, required this.player});

  final PriceMove? move;
  final PlayerSummary player;

  @override
  Widget build(BuildContext context) {
    final m = move;
    final colour = m == null
        ? Colors.white54
        : m.rising
        ? Brand.good
        : m.falling
        ? Brand.bad
        : Colors.white54;
    final arrow = m == null
        ? '·'
        : (m.rising
              ? '↗'
              : m.falling
              ? '↘'
              : '–');
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
          decoration: BoxDecoration(
            color: colour,
            borderRadius: BorderRadius.circular(Brand.radiusPill),
          ),
          child: Text(
            '$arrow £${player.price.toStringAsFixed(1)}',
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          // ⭐ The evidence, not a forecast: what the crowd actually did this week.
          m == null
              ? '—'
              : '${m.netTransfers >= 0 ? '+' : ''}${_compact(m.netTransfers)}',
          style: const TextStyle(color: Colors.white60, fontSize: 8.5),
        ),
      ],
    );
  }

  static String _compact(int n) {
    final abs = n.abs();
    if (abs >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}m';
    if (abs >= 1000) return '${(n / 1000).toStringAsFixed(1)}k';
    return '$n';
  }
}

/// ⭐ The switch the Hub puts behind a menu, out in the open — it changes what every card means, which is
/// not a thing to hide two taps deep.
class _ModeBar extends StatelessWidget {
  const _ModeBar({required this.mode, required this.onMode});

  final PitchMode mode;
  final ValueChanged<PitchMode> onMode;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
    child: Row(
      children: [
        for (final option in PitchMode.values)
          Expanded(
            child: GestureDetector(
              onTap: () => onMode(option),
              behavior: HitTestBehavior.opaque,
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 2),
                padding: const EdgeInsets.symmetric(vertical: 5),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: option == mode ? Brand.purple : Colors.white10,
                  borderRadius: BorderRadius.circular(Brand.radiusPill),
                ),
                child: Text(
                  option.label,
                  style: TextStyle(
                    color: option == mode ? Colors.white : Colors.white54,
                    fontSize: 11.5,
                    fontWeight: option == mode
                        ? FontWeight.w600
                        : FontWeight.w400,
                  ),
                ),
              ),
            ),
          ),
      ],
    ),
  );
}

class _Armband extends StatelessWidget {
  const _Armband({required this.letter});

  final String letter;

  @override
  Widget build(BuildContext context) => Container(
    width: 15,
    height: 15,
    alignment: Alignment.center,
    decoration: BoxDecoration(
      color: letter == 'C' ? Brand.orange : Brand.muted,
      shape: BoxShape.circle,
    ),
    child: Text(
      letter,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 9,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

class _Flag extends StatelessWidget {
  const _Flag({required this.text, required this.colour});

  final String text;
  final Color colour;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 4),
    decoration: BoxDecoration(
      color: colour,
      borderRadius: BorderRadius.circular(Brand.radiusPill),
    ),
    child: Text(
      text,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 8,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}

class _Bench extends StatelessWidget {
  const _Bench({
    required this.team,
    required this.mode,
    required this.onTapPlayer,
  });

  final MyTeam team;
  final PitchMode mode;
  final void Function(PlayerSummary) onTapPlayer;

  @override
  Widget build(BuildContext context) {
    final roleOf = {for (final e in team.benchRoles.entries) e.value: e.key};
    return Container(
      decoration: BoxDecoration(
        color: Brand.ink.withValues(alpha: 0.82),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      padding: const EdgeInsets.fromLTRB(4, 5, 4, 7),
      child: Column(
        children: [
          const Text(
            'BENCH',
            style: TextStyle(
              color: Colors.white54,
              fontSize: 9,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final p in team.orderedBench)
                Stack(
                  clipBehavior: Clip.none,
                  children: [
                    _Card(
                      team: team,
                      player: p,
                      mode: mode,
                      onTap: () => onTapPlayer(p),
                    ),
                    if (roleOf[p.id] != null)
                      Positioned(
                        left: 2,
                        top: -3,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5),
                          decoration: BoxDecoration(
                            color: Brand.purple,
                            borderRadius: BorderRadius.circular(
                              Brand.radiusPill,
                            ),
                          ),
                          child: Text(
                            roleOf[p.id]!,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 8,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }
}
