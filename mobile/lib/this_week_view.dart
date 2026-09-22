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
                child: SelectableText(friendlyError(snapshot.error),
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

          final explanation = plan['explanation'] as Map<String, dynamic>?;
          final overall = explanation?['overall'] as Map<String, dynamic>?;
          final levers = explanation?['levers'] as Map<String, dynamic>?;
          final lineupWhy = (explanation?['lineup'] as List?) ?? const [];

          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 8, 14, 20),
            children: [
              if (overall != null) _Confidence(overall: overall, levers: levers),
              if (captain != null)
                _Card(
                  label: 'Captain',
                  headline: '${captain['web_name']}',
                  detail: '${captain['opponent'] ?? ''} ${captain['venue'] ?? ''}'
                      ' · ${(captain['xp'] as num?)?.toStringAsFixed(1) ?? '—'} xP',
                  highlight: true,
                  explanation: explanation?['captain'] as Map<String, dynamic>?,
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
                    // ⭐ The engine's own sentence for each swap — *"higher projected xP: 4.8 vs 3.3"* —
                    // so a reader can check the call rather than take it.
                    ...lineupWhy.map((r) => '$r'),
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
                    explanation: explanation?['transfer'] as Map<String, dynamic>?,
                  ),
              if (timing.isNotEmpty)
                _Card(
                  label: 'Timing',
                  headline: '${timing['action']}'.toUpperCase(),
                  // ⚠️ The engine's own sentence, not a rephrasing. It carries the arithmetic that makes
                  // the verdict checkable — "waiting costs 2.8 and saves only 1.9".
                  detail: '${timing['reason'] ?? ''}',
                ),
              const SizedBox(height: 10),
              // ⭐ The model note, carried over verbatim from the web app (ADR-089/182). It says what the
              // confidence IS — a heuristic over the signals, not a probability — and an app that shows a
              // score out of 100 without that line is inviting it to be read as one.
              const Text(
                'Analytics decide the recommendation; logic explains it. '
                'Confidence is a heuristic from the signals, not a probability.',
                style: TextStyle(color: Colors.white24, fontSize: 10.5, height: 1.5),
              ),
            ],
          );
        },
      );
}

/// The week's Confidence · Edge · Risk, and **what would move it** (ADR-089).
///
/// ⭐⭐ `fixed` is the part most confidence displays leave out: the ceiling, and *why it is the ceiling*.
/// A score with no stated limit invites a manager to chase it — and the honest answer is often that the
/// number cannot rise this week without a different captain, which is not a thing to fix, it is a fact.
class _Confidence extends StatelessWidget {
  const _Confidence({required this.overall, required this.levers});

  final Map<String, dynamic> overall;
  final Map<String, dynamic>? levers;

  @override
  Widget build(BuildContext context) {
    final score = overall['confidence'] as int? ?? 0;
    final band = '${overall['band'] ?? ''}';
    final reasons = (overall['reasons'] as List?) ?? const [];
    final risks = (overall['risks'] as List?) ?? const [];
    final actions = (levers?['levers'] as List?) ?? const [];
    // ⭐ Colour by the engine's own band, never by an arbitrary threshold typed here — two definitions of
    // "high" is one more than this app should have.
    final colour = switch (band) {
      'High' => Brand.good,
      'Medium' => Brand.warn,
      _ => Brand.bad,
    };

    return Container(
      margin: const EdgeInsets.only(bottom: 11),
      padding: const EdgeInsets.fromLTRB(13, 11, 13, 13),
      decoration: BoxDecoration(
        color: Colors.white10,
        border: Border(left: BorderSide(color: colour, width: 3)),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text('$score',
                  style: TextStyle(color: colour, fontSize: 26, fontWeight: FontWeight.w800)),
              const Text('/100',
                  style: TextStyle(color: Colors.white38, fontSize: 12)),
              const SizedBox(width: 8),
              Text(band, style: TextStyle(color: colour, fontSize: 13, fontWeight: FontWeight.w600)),
              const Spacer(),
              const Text('CONFIDENCE',
                  style: TextStyle(color: Colors.white24, fontSize: 9.5, letterSpacing: 1)),
            ],
          ),
          if (actions.isNotEmpty) ...[
            const SizedBox(height: 8),
            for (final lever in actions)
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text('− ${lever['worth']}  ${lever['what']}',
                    style: const TextStyle(color: Brand.warn, fontSize: 11.5, height: 1.45)),
              ),
          ],
          if (levers?['fixed'] != null) ...[
            const SizedBox(height: 4),
            Text('Ceiling: ${levers!['fixed']}',
                style: const TextStyle(color: Colors.white38, fontSize: 11, height: 1.45)),
          ],
          if (reasons.isNotEmpty) ...[
            const SizedBox(height: 10),
            const Text('EDGE', style: TextStyle(color: Colors.white24, fontSize: 9.5, letterSpacing: 1)),
            for (final r in reasons)
              Padding(
                padding: const EdgeInsets.only(top: 3),
                child: Text('✓  $r',
                    style: const TextStyle(color: Brand.accentTeal, fontSize: 11.5, height: 1.4)),
              ),
          ],
          if (risks.isNotEmpty) ...[
            const SizedBox(height: 9),
            const Text('RISK', style: TextStyle(color: Colors.white24, fontSize: 9.5, letterSpacing: 1)),
            for (final r in risks)
              Padding(
                padding: const EdgeInsets.only(top: 3),
                child: Text('⚠  $r',
                    style: const TextStyle(color: Brand.warn, fontSize: 11.5, height: 1.4)),
              ),
          ],
        ],
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({
    required this.label,
    required this.headline,
    required this.detail,
    this.highlight = false,
    this.explanation,
  });

  final String label;
  final String headline;
  final String detail;
  final bool highlight;

  /// ⭐ The per-recommendation reasons (ADR-089). A confidence with no reasons is a number to be trusted;
  /// with them it is a number to be checked, which is the product this is supposed to be.
  final Map<String, dynamic>? explanation;

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
            if (explanation != null) ...[
              const SizedBox(height: 7),
              Row(
                children: [
                  Text('${explanation!['confidence']}/100',
                      style: const TextStyle(
                          color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w700)),
                  const SizedBox(width: 6),
                  Text('${explanation!['band']}',
                      style: const TextStyle(color: Colors.white38, fontSize: 11)),
                ],
              ),
              for (final r in (explanation!['reasons'] as List?) ?? const [])
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text('✓  $r',
                      style: const TextStyle(color: Brand.accentTeal, fontSize: 11, height: 1.4)),
                ),
              for (final r in (explanation!['risks'] as List?) ?? const [])
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text('⚠  $r',
                      style: const TextStyle(color: Brand.warn, fontSize: 11, height: 1.4)),
                ),
            ],
          ],
        ),
      );
}
