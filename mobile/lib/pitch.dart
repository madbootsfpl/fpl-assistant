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
    super.key,
  });

  final MyTeam team;
  final PitchMode mode;
  final ValueChanged<PitchMode> onMode;

  /// ⭐ The pitch is the right surface for editing a squad — it is where a manager already looks to decide
  /// anything, and a tab called "Captain" would be a second place to do a thing that belongs here.
  final void Function(PlayerSummary) onTapPlayer;

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
        ClipRRect(
          borderRadius: const BorderRadius.vertical(
            top: Radius.circular(Brand.radiusMd),
          ),
          child: PitchMarkings(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(4, 12, 4, 8),
              child: Column(
                children: [
                  for (final row in _rows)
                    if (byRow[row]!.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          crossAxisAlignment: CrossAxisAlignment.start,
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
        ),
        _Bench(team: team, mode: mode, onTapPlayer: onTapPlayer),
      ],
    );
  }
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
      padding: const EdgeInsets.fromLTRB(14, 2, 14, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'Gameweek ${team.gameweek ?? '—'}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          // ⚠️ Rendered as given: it already carries the timezone and the countdown (ADR-086).
          Text(
            team.deadlineLabel,
            maxLines: 2,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 10),
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
          fontSize: 18,
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
                player: player,
              ),
              PitchMode.price => _Price(
                move: team.priceFor(player),
                player: player,
              ),
            },
          ],
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
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
        decoration: BoxDecoration(
          color: Brand.surface,
          borderRadius: BorderRadius.circular(Brand.radiusPill),
        ),
        child: Text(
          player.xp.toStringAsFixed(1),
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: Brand.text,
          ),
        ),
      ),
      const SizedBox(height: 2),
      Text(
        '£${player.price.toStringAsFixed(1)}m · ${fixture?.label ?? '—'}',
        style: const TextStyle(color: Colors.white70, fontSize: 8.5),
      ),
    ],
  );
}

/// **Next 3** — ⭐ *a manager deciding whether to HOLD a player is asking about his run, not his Saturday.*
///
/// ⚠️ The per-gameweek xP comes from `by_gameweek`, which the app has published since ADR-213 and threw
/// away on this card until now.
class _Run extends StatelessWidget {
  const _Run({required this.fixtures, required this.player});

  final List<Fixture> fixtures;
  final PlayerSummary player;

  @override
  Widget build(BuildContext context) {
    final weeks = player.byGameweek.keys.toList()..sort();
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (var i = 0; i < fixtures.length; i++)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 1),
                  child: Column(
                    children: [
                      Text(
                        // ⭐ Matched by **gameweek**, not by position in the list: a blank gameweek means
                        // a club's third fixture is not the third week, and lining them up by index would
                        // quietly show the wrong number against the wrong opponent.
                        _xpFor(weeks, fixtures[i].gameweek),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Text(
                        fixtures[i].opponent.toLowerCase(),
                        maxLines: 1,
                        overflow: TextOverflow.clip,
                        style: const TextStyle(
                          color: Colors.white60,
                          fontSize: 7.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }

  String _xpFor(List<int> weeks, int? gameweek) {
    if (gameweek == null) return '—';
    final value = player.byGameweek[gameweek];
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
      decoration: const BoxDecoration(
        color: Color(0xEB17131F),
        borderRadius: BorderRadius.vertical(
          bottom: Radius.circular(Brand.radiusMd),
        ),
      ),
      padding: const EdgeInsets.fromLTRB(4, 7, 4, 10),
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
