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

class PitchView extends StatelessWidget {
  const PitchView({required this.team, required this.onTapPlayer, super.key});

  final MyTeam team;

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
        ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(Brand.radiusMd)),
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
                              _Card(team: team, player: p, onTap: () => onTapPlayer(p)),
                          ],
                        ),
                      ),
                ],
              ),
            ),
          ),
        ),
        _Bench(team: team, onTapPlayer: onTapPlayer),
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
              Text('Gameweek ${team.gameweek ?? '—'}',
                  style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 2),
          // ⚠️ Rendered as given: it already carries the timezone and the countdown (ADR-086).
          Text(team.deadlineLabel,
              maxLines: 2,
              style: const TextStyle(color: Colors.white70, fontSize: 11, height: 1.35)),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _Stat(value: xi.toStringAsFixed(1), label: 'Predicted'),
              // ⚠️ FPL's bank, or an em dash — ⭐ *never £0.0m*, which is a real position and would read as
              // one. `—` says "not known"; zero says "you are skint".
              _Stat(value: team.bank == null ? '—' : '£${team.bank!.toStringAsFixed(1)}m', label: 'In the bank'),
              _Stat(
                  value: team.value == null ? '—' : '£${team.value!.toStringAsFixed(1)}m',
                  label: 'Value'),
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
          Text(value,
              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700)),
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 10)),
        ],
      );
}

class _Card extends StatelessWidget {
  const _Card({required this.team, required this.player, required this.onTap});

  final MyTeam team;
  final PlayerSummary player;
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
                  Image.network(kit,
                      height: 34,
                      errorBuilder: (_, _, _) => const Text('👕', style: TextStyle(fontSize: 22))),
                if (_armband != null)
                  Positioned(top: -2, right: 6, child: _Armband(letter: _armband!)),
              ],
            ),
          ),
          const SizedBox(height: 2),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                child: Text(player.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        color: Colors.white, fontSize: 10.5, fontWeight: FontWeight.w600)),
              ),
              if (_flag != null) ...[const SizedBox(width: 3), _flag!],
            ],
          ),
          const SizedBox(height: 2),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
            decoration: BoxDecoration(
              color: Brand.surface,
              borderRadius: BorderRadius.circular(Brand.radiusPill),
            ),
            child: Text(player.xp.toStringAsFixed(1),
                style: const TextStyle(
                    fontSize: 11, fontWeight: FontWeight.w700, color: Brand.text)),
          ),
          const SizedBox(height: 2),
          Text('£${player.price.toStringAsFixed(1)}m · ${fixture?.label ?? '—'}',
              style: const TextStyle(color: Colors.white70, fontSize: 8.5)),
        ],
      ),
    ));
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
        child: Text(letter,
            style: const TextStyle(
                color: Colors.white, fontSize: 9, fontWeight: FontWeight.w700)),
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
        child: Text(text,
            style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.w600)),
      );
}

class _Bench extends StatelessWidget {
  const _Bench({required this.team, required this.onTapPlayer});

  final MyTeam team;
  final void Function(PlayerSummary) onTapPlayer;

  @override
  Widget build(BuildContext context) {
    final roleOf = {for (final e in team.benchRoles.entries) e.value: e.key};
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xEB17131F),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(Brand.radiusMd)),
      ),
      padding: const EdgeInsets.fromLTRB(4, 7, 4, 10),
      child: Column(
        children: [
          const Text('BENCH',
              style: TextStyle(color: Colors.white54, fontSize: 9, letterSpacing: 2)),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final p in team.orderedBench)
                Stack(
                  clipBehavior: Clip.none,
                  children: [
                    _Card(team: team, player: p, onTap: () => onTapPlayer(p)),
                    if (roleOf[p.id] != null)
                      Positioned(
                        left: 2,
                        top: -3,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5),
                          decoration: BoxDecoration(
                            color: Brand.purple,
                            borderRadius: BorderRadius.circular(Brand.radiusPill),
                          ),
                          child: Text(roleOf[p.id]!,
                              style: const TextStyle(color: Colors.white, fontSize: 8)),
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
