/// This week — captain, lineup, transfer and timing in one answer (ADR-223).
///
/// ⚠️ **The plan is read as a raw map, and that is deliberate.** `gameweek_plan` returns thirteen keys and
/// the screen currently uses five; modelling the other eight before anything renders them would be guessing
/// at a shape. ⭐ *The moment a second screen wants one of them, it earns a class.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class ThisWeekView extends StatefulWidget {
  const ThisWeekView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<ThisWeekView> createState() => _ThisWeekViewState();
}

class _ThisWeekViewState extends State<ThisWeekView> {
  late final Future<Map<String, dynamic>> _plan = widget.client.gameweekPlan(
    [
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ],
    benchIds: widget.team.analysis.bench.map((p) => p.id).toList(),
    horizon: 1,
    bank: widget.team.bank ?? 0.0,
    free: widget.team.freeTransfers,
  );

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: _plan,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Center(
                child: SelectableText('${snapshot.error}',
                    style: const TextStyle(color: Colors.white70, height: 1.55)),
              ),
            );
          }
          final plan = snapshot.data!;
          final captain = plan['captain'] as Map<String, dynamic>?;
          final lineup = (plan['lineup'] as Map<String, dynamic>?) ?? const {};
          final moves = (plan['transfers'] as List?) ?? const [];
          final timing = (plan['timing'] as Map<String, dynamic>?) ?? const {};
          final bringIn = (lineup['bring_in'] as List?) ?? const [];
          final drop = (lineup['drop'] as List?) ?? const [];

          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 8, 14, 20),
            children: [
              if (captain != null)
                _Card(
                  label: 'Captain',
                  headline: '${captain['web_name']}',
                  detail: '${captain['opponent'] ?? ''} ${captain['venue'] ?? ''}'
                      ' · ${(captain['xp'] as num?)?.toStringAsFixed(1) ?? '—'} xP',
                  highlight: true,
                ),
              if (bringIn.isEmpty && drop.isEmpty)
                const _Card(
                    label: 'Lineup',
                    headline: 'No change',
                    // ⭐ Said out loud. Rendering nothing would read as "not calculated" rather than
                    // "already optimal", and those are opposite messages.
                    detail: 'Your XI is already the best legal eleven for this gameweek.')
              else
                _Card(
                  label: 'Lineup',
                  headline: '${bringIn.length} change${bringIn.length == 1 ? '' : 's'}',
                  detail: [
                    for (var i = 0; i < bringIn.length && i < drop.length; i++)
                      '▲ ${bringIn[i]['web_name']}   ▼ ${drop[i]['web_name']}',
                  ].join('\n'),
                ),
              if (moves.isEmpty)
                const _Card(
                    label: 'Transfer',
                    headline: 'Hold',
                    detail: 'Nothing worth doing with the transfer you hold.')
              else
                for (final m in moves)
                  _Card(
                    label: 'Transfer',
                    headline: '${m['out']['web_name']} → ${m['in']['web_name']}',
                    detail: '+${(m['gain'] as num).toStringAsFixed(1)} xP',
                  ),
              if (timing.isNotEmpty)
                _Card(
                  label: 'Timing',
                  headline: '${timing['action']}'.toUpperCase(),
                  // ⚠️ The engine's own sentence, not a rephrasing. It carries the arithmetic that makes
                  // the verdict checkable — "waiting costs 2.8 and saves only 1.9".
                  detail: '${timing['reason'] ?? ''}',
                ),
            ],
          );
        },
      );
}

class _Card extends StatelessWidget {
  const _Card({
    required this.label,
    required this.headline,
    required this.detail,
    this.highlight = false,
  });

  final String label;
  final String headline;
  final String detail;
  final bool highlight;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 9),
        padding: const EdgeInsets.fromLTRB(13, 10, 13, 12),
        decoration: BoxDecoration(
          color: highlight ? Brand.purple.withValues(alpha: 0.2) : Colors.white10,
          border: Border.all(
              color: highlight ? Brand.purpleLight : Colors.transparent, width: 1.2),
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label.toUpperCase(),
                style: const TextStyle(
                    color: Colors.white38, fontSize: 10, letterSpacing: 1)),
            const SizedBox(height: 3),
            Text(headline,
                style: const TextStyle(
                    color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700)),
            if (detail.isNotEmpty) ...[
              const SizedBox(height: 3),
              Text(detail,
                  style: const TextStyle(color: Colors.white60, fontSize: 12, height: 1.5)),
            ],
          ],
        ),
      );
}
