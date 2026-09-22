/// Chips — a season decision, not a weekly one (ADR-229).
///
/// ⚠️⚠️ **The window is the chip's deadline, not the app's horizon** (ADR-166). A chip expires at the end
/// of each half-season, so the question is never *"is this week good?"* but *"is this week better than the
/// weeks I have left?"* — and that is not a smaller version of the first question, it is a different one.
/// The server decides the window; this screen states it, because it is **not** what the rest of the app is
/// looking at.
///
/// ⭐ The wildcard says what it is **worth**, not only when to play it (ADR-185) — the owner found that gap
/// from a two-team A/B, where the advisor named a window while his squad already overlapped an optimal
/// rebuild by 3 of 15. *A recommendation that measures only WHEN presents itself as an answer to WHETHER.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class ChipsView extends StatefulWidget {
  const ChipsView({
    required this.client,
    required this.team,
    required this.managerId,
    super.key,
  });

  final ServiceClient client;
  final MyTeam team;

  /// ⚠️ Without it the server cannot tell which chips are spent, and says so rather than guessing.
  final int managerId;

  @override
  State<ChipsView> createState() => _ChipsViewState();
}

class _ChipsViewState extends State<ChipsView> {
  late final Future<Map<String, dynamic>> _chips = widget.client.chips(
    [
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ],
    benchIds: widget.team.analysis.bench.map((p) => p.id).toList(),
    bank: widget.team.bank ?? 0.0,
    managerId: widget.managerId,
  );

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: _chips,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Center(
                child: SelectableText(friendlyError(snapshot.error),
                    style: const TextStyle(color: Colors.white70, height: 1.55)),
              ),
            );
          }
          final answer = snapshot.data!;
          final chips = (answer['chips'] as Map<String, dynamic>?) ?? const {};
          final weeks = ((answer['gameweeks'] as List?) ?? const []).cast<int>();
          if (chips.isEmpty) {
            return const _Message('No chip advice yet — it needs a squad and some upcoming fixtures.');
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
            children: [
              // ⭐ The window, first and explicitly. Every other screen in this app is looking at one
              // gameweek; this one is not, and a reader who assumes otherwise misreads every number below.
              Text(
                weeks.isEmpty
                    ? 'Looking at the weeks you have left'
                    : 'GW${weeks.first}–${weeks.last} · the weeks you have left, '
                        'not the next one',
                style: const TextStyle(color: Colors.white54, fontSize: 12, height: 1.45),
              ),
              if (answer['expires_after'] != null)
                Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Text('These chips expire after GW${answer['expires_after']}.',
                      style: const TextStyle(color: Colors.white38, fontSize: 11)),
                ),
              if (answer['chips_checked'] != true)
                const Padding(
                  padding: EdgeInsets.only(top: 6),
                  child: Text(
                    // ⚠️ Said out loud. Silence here would read as "you have all four".
                    'Could not check which chips you have already played, so none are marked.',
                    style: TextStyle(color: Brand.warn, fontSize: 11, height: 1.45),
                  ),
                ),
              const SizedBox(height: 14),
              _Wildcard(data: chips['wildcard'] as Map<String, dynamic>?),
              _TripleCaptain(data: chips['triple_captain'] as Map<String, dynamic>?),
              _Simple(
                name: 'Bench Boost',
                data: chips['bench_boost'] as Map<String, dynamic>?,
                detail: (d) => 'Your bench is worth '
                    '${(d['bench_points'] as num?)?.toStringAsFixed(1) ?? '—'} that week — '
                    'squad total ${(d['squad_total'] as num?)?.toStringAsFixed(1) ?? '—'}.',
              ),
              _Simple(
                name: 'Free Hit',
                data: chips['free_hit'] as Map<String, dynamic>?,
                detail: (d) => 'Your XI projects '
                    '${(d['xi_total'] as num?)?.toStringAsFixed(1) ?? '—'} that week.',
              ),
              const SizedBox(height: 14),
              const Text(
                'Chips are one-offs with a deadline, so the advice compares the weeks you have left '
                'against each other — not against a good week in isolation.',
                style: TextStyle(color: Colors.white24, fontSize: 10.5, height: 1.5),
              ),
            ],
          );
        },
      );
}

/// ⭐⭐ **The only chip that answers *whether*, not just *when*.**
class _Wildcard extends StatelessWidget {
  const _Wildcard({required this.data});

  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    final d = data;
    if (d == null) return const SizedBox.shrink();
    final weeks = ((d['gameweeks'] as List?) ?? const []).cast<int>();
    final gain = (d['gain'] as num?)?.toDouble();
    final overlap = d['overlap'] as int?;
    final size = d['squad_size'] as int?;

    return _Card(
      name: '${d['name'] ?? 'Wildcard'}',
      when: weeks.isEmpty ? '—' : 'GW${weeks.first}–${weeks.last}',
      available: d['available'] as bool?,
      playedIn: d['played_in'] as int?,
      children: [
        if (gain != null && overlap != null && size != null) ...[
          Text(
            // ⚠️ The overlap is the honest headline. A wildcard that rebuilds 3 of your 15 is not a
            // wildcard worth playing, however good the window looks.
            'A rebuild would change ${size - overlap} of your $size '
            '— worth ${gain >= 0 ? '+' : ''}${gain.toStringAsFixed(1)} xP over the window.',
            style: const TextStyle(color: Colors.white70, fontSize: 12.5, height: 1.5),
          ),
          if (size - overlap <= 3)
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text(
                '⭐ That is a small rebuild. The window may be your weakest, and the chip still not '
                'be worth spending on it.',
                style: TextStyle(color: Brand.warn, fontSize: 11.5, height: 1.45),
              ),
            ),
        ] else
          const Text('The window, but not yet what it is worth.',
              style: TextStyle(color: Colors.white54, fontSize: 12.5)),
      ],
    );
  }
}

class _TripleCaptain extends StatelessWidget {
  const _TripleCaptain({required this.data});

  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    final d = data;
    if (d == null) return const SizedBox.shrink();
    final raw = d['player'] as Map<String, dynamic>?;
    final player = raw == null ? null : PlayerSummary.fromJson(raw);
    final extra = (d['extra_points'] as num?)?.toDouble();

    return _Card(
      name: '${d['name'] ?? 'Triple Captain'}',
      when: d['gameweek'] == null ? '—' : 'GW${d['gameweek']}',
      available: d['available'] as bool?,
      playedIn: d['played_in'] as int?,
      children: [
        Text(
          player == null
              ? 'No standout pick in the window.'
              : '${player.name} — ${extra == null ? '' : 'an extra ${extra.toStringAsFixed(1)} on top of '
                  'the armband you already get'}',
          style: const TextStyle(color: Colors.white70, fontSize: 12.5, height: 1.5),
        ),
        // ⭐ Availability travels with the pick (ADR-227), so a doubtful triple-captain says so — which is
        // the one chip where a 75% player is a genuinely bad idea.
        if (player != null && player.isDoubtful)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              '⚠ ${player.chance ?? '?'}% chance of playing. Tripling a doubt triples the doubt.',
              style: const TextStyle(color: Brand.warn, fontSize: 11.5, height: 1.45),
            ),
          ),
      ],
    );
  }
}

class _Simple extends StatelessWidget {
  const _Simple({required this.name, required this.data, required this.detail});

  final String name;
  final Map<String, dynamic>? data;
  final String Function(Map<String, dynamic>) detail;

  @override
  Widget build(BuildContext context) {
    final d = data;
    if (d == null) return const SizedBox.shrink();
    return _Card(
      name: '${d['name'] ?? name}',
      when: d['gameweek'] == null ? '—' : 'GW${d['gameweek']}',
      available: d['available'] as bool?,
      playedIn: d['played_in'] as int?,
      children: [
        Text(detail(d),
            style: const TextStyle(color: Colors.white70, fontSize: 12.5, height: 1.5)),
        if (d['margin'] != null)
          Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Text(
              // ⭐ The margin is how much better this week is than the next best. A thin margin is a
              // *weak recommendation*, and saying so is the difference between advice and an instruction.
              'Better than the next-best week by '
              '${(d['margin'] as num).toStringAsFixed(1)}.',
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({
    required this.name,
    required this.when,
    required this.children,
    this.available,
    this.playedIn,
  });

  final String name;
  final String when;
  final List<Widget> children;

  /// ⭐ **Three states, not two.** `true` in hand · `false` spent · `null` **we could not check** — and
  /// the third must never render as the first.
  final bool? available;
  final int? playedIn;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.fromLTRB(13, 11, 13, 13),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(name,
                      style: TextStyle(
                          // ⚠️ A spent chip is dimmed, not hidden: *when it would have been best* is still
                          // true, and removing the card leaves a manager wondering if the app knew.
                          color: available == false ? Colors.white54 : Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w700)),
                ),
                if (available != null) _StatusPill(available: available!, playedIn: playedIn),
                const SizedBox(width: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 2),
                  decoration: BoxDecoration(
                    color: Brand.purple,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: Text(when,
                      style: const TextStyle(
                          color: Colors.white, fontSize: 11.5, fontWeight: FontWeight.w600)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ...children,
          ],
        ),
      );
}

/// ⭐ The Hub's own convention, and a good one: the chip's state sits beside its name, not buried in the
/// body. *"Played GW2"* is the first thing you need to know about a chip.
class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.available, required this.playedIn});

  final bool available;
  final int? playedIn;

  @override
  Widget build(BuildContext context) {
    final spent = !available;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: spent ? Colors.white12 : Brand.goodTint,
        borderRadius: BorderRadius.circular(Brand.radiusPill),
      ),
      child: Text(
        // ⭐ Naming the gameweek matters: "unavailable" alone invites a manager to think it is a bug.
        spent ? (playedIn == null ? 'Played' : 'Played GW$playedIn') : 'Available',
        style: TextStyle(
            color: spent ? Colors.white54 : Brand.goodFg,
            fontSize: 10,
            fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Text(text,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white38, height: 1.6)),
        ),
      );
}
