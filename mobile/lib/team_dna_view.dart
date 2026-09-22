/// Team DNA — what kind of side is this? (ADR-247)
///
/// ⭐⭐ **A club's fingerprint, not a player's**, and that is the choice. *What kind of player is he?* is
/// already answered twice — the expanding card (ADR-237) and Boot Battle (ADR-236). *Is this attack
/// actually any good?* decides between two players from different sides, and the app could not answer it.
///
/// ⭐ **Bars, where the web draws a radar.** A radar needs width a phone does not have, and eight labels
/// around a circle on a 390pt screen are unreadable. The numbers are identical; the shape is the one that
/// survives the screen. ⚠️ *Porting a layout is not the same as porting a view.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class TeamDnaView extends StatefulWidget {
  const TeamDnaView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<TeamDnaView> createState() => _TeamDnaViewState();
}

class _TeamDnaViewState extends State<TeamDnaView> {
  late final Future<List<ClubDna>> _clubs = widget.client.teamDna(
    playerIds: [
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ],
  );

  /// ⭐ Off by default. *A default that narrows the answer is a default that hides something* — the table
  /// is the league, and yours is a lens over it.
  bool _mineOnly = false;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<ClubDna>>(
    future: _clubs,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Center(
            child: SelectableText(
              friendlyError(snapshot.error),
              style: const TextStyle(color: Colors.white70, height: 1.55),
            ),
          ),
        );
      }
      final all = snapshot.data!;
      final shown = _mineOnly ? all.where((c) => c.yours).toList() : all;

      return ListView(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${all.length} clubs, best first · '
                  '${all.where((c) => c.yours).length} you hold players from',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _mineOnly = !_mineOnly),
                behavior: HitTestBehavior.opaque,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: _mineOnly ? Brand.purple : Colors.white10,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: Text(
                    'Mine',
                    style: TextStyle(
                      color: _mineOnly ? Colors.white : Colors.white54,
                      fontSize: 11.5,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          for (final club in shown) _Club(club: club),
        ],
      );
    },
  );
}

class _Club extends StatefulWidget {
  const _Club({required this.club});

  final ClubDna club;

  @override
  State<_Club> createState() => _ClubState();
}

class _ClubState extends State<_Club> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final c = widget.club;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: () => setState(() => _open = !_open),
            borderRadius: BorderRadius.circular(Brand.radiusMd),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 10, 10),
              child: Row(
                children: [
                  _Grade(grade: c.grade),
                  const SizedBox(width: 11),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              c.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            if (c.yours) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 1,
                                ),
                                decoration: BoxDecoration(
                                  border: Border.all(
                                    color: Brand.purpleLight,
                                    width: 1,
                                  ),
                                  borderRadius: BorderRadius.circular(
                                    Brand.radiusPill,
                                  ),
                                ),
                                child: const Text(
                                  'yours',
                                  style: TextStyle(
                                    color: Brand.purpleLight,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        if (c.insights.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              // ⭐ The strongest one, closed. The rest are behind the tap — a list of four
                              // observations per club, twenty times over, is a wall.
                              c.insights.first.text,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: Colors.white38,
                                fontSize: 11,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Icon(
                    _open ? Icons.expand_less : Icons.expand_more,
                    size: 19,
                    color: Colors.white24,
                  ),
                ],
              ),
            ),
          ),
          if (_open)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final axis in c.axes) _Bar(axis: axis),
                  if (c.insights.length > 1) const SizedBox(height: 6),
                  for (final insight in c.insights.skip(1))
                    Padding(
                      padding: const EdgeInsets.only(top: 3),
                      child: Text(
                        '${_mark(insight.kind)}  ${insight.text}',
                        style: TextStyle(
                          color: _colour(insight.kind),
                          fontSize: 11.5,
                          height: 1.4,
                        ),
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// ⚠️ The same four kinds the web uses (ADR-118) — good ✓ · set-piece ⚡ · info ℹ · warning ⚠. A fifth
  /// mark invented here would be a second vocabulary for one idea.
  static String _mark(String kind) => switch (kind) {
    'good' => '✓',
    'sp' => '⚡',
    'warn' => '⚠',
    _ => 'ℹ',
  };

  static Color _colour(String kind) => switch (kind) {
    'good' => Brand.accentTeal,
    'sp' => Brand.orange,
    'warn' => Brand.warn,
    _ => Colors.white54,
  };
}

/// A letter in a box — ⭐ the grade FPL managers already speak in, not a number they would have to learn.
class _Grade extends StatelessWidget {
  const _Grade({required this.grade});

  final String grade;

  @override
  Widget build(BuildContext context) => Container(
    width: 34,
    height: 30,
    alignment: Alignment.center,
    decoration: BoxDecoration(
      color: switch (grade) {
        'A+' || 'A' => Brand.good,
        'B' => Brand.purple,
        'C' => Brand.warn,
        _ => Brand.bad,
      },
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: Text(
      grade,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 13,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

/// One axis as a bar — ⭐ **percentile, so eight different units share one scale.**
class _Bar extends StatelessWidget {
  const _Bar({required this.axis});

  final DnaAxis axis;

  @override
  Widget build(BuildContext context) {
    final p = axis.percentile;
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Row(
        children: [
          SizedBox(
            width: 108,
            child: Text(
              axis.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.white60, fontSize: 10.5),
            ),
          ),
          Expanded(
            child: Container(
              height: 7,
              decoration: BoxDecoration(
                color: Colors.white10,
                borderRadius: BorderRadius.circular(4),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                // ⚠️ **Null is unranked, not zero.** An empty bar for "we could not rank this" reads as
                // "this club is the worst in the league at it", which is a different and wrong claim.
                widthFactor: (p ?? 0) / 100,
                child: Container(
                  decoration: BoxDecoration(
                    color: p == null
                        ? Colors.transparent
                        : p >= 75
                        ? Brand.good
                        : p >= 40
                        ? Brand.purpleLight
                        : Brand.warn,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
          ),
          SizedBox(
            width: 32,
            child: Text(
              p == null ? '—' : '$p',
              textAlign: TextAlign.right,
              style: const TextStyle(color: Colors.white70, fontSize: 10.5),
            ),
          ),
        ],
      ),
    );
  }
}
