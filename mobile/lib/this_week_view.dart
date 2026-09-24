/// This week — captain, lineup, transfer and timing in one answer (ADR-223).
///
/// ⚠️ **The plan is read as a raw map, and that is deliberate.** `gameweek_plan` returns thirteen keys and
/// the screen currently uses five; modelling the other eight before anything renders them would be guessing
/// at a shape. ⭐ *The moment a second screen wants one of them, it earns a class.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'apply_plan.dart';
import 'api/models.dart';
import 'brand.dart';
import 'help_dot.dart';

class ThisWeekView extends StatefulWidget {
  const ThisWeekView({
    required this.client,
    required this.team,
    required this.onApply,
    required this.onAlternatives,
    super.key,
  });

  final ServiceClient client;
  final MyTeam team;

  /// ⭐⭐ **Act where you read the reason** (ADR-249). The owner asked whether the optimise button should
  /// be on My Team *or* in This Week; the answer is both, because they are different moments. On the
  /// pitch it is a shortcut for someone who already trusts it; here it sits directly under the
  /// **per-swap justification** — *"higher projected xP: 4.8 vs 3.3"* — for someone who wants to check
  /// first. ⚠️ *Making a reader remember a recommendation and go elsewhere to apply it is the transcription
  /// problem ADR-244 removed, reintroduced one screen along.*
  final Future<void> Function(SuggestedLineup) onApply;

  /// Open the full transfer board (ADR-283).
  ///
  /// ⭐ The card above says *"Sangaré → Groß, +2.2 xP"*. This is the question that follows it — *"and
  /// what else?"* — which is why it sits between the answer and the timing rather than a tab away.
  final VoidCallback onAlternatives;

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
            child: SelectableText(
              friendlyError(snapshot.error),
              style: const TextStyle(color: Colors.white70, height: 1.55),
            ),
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
              detail:
                  '${captain['opponent'] ?? ''} ${captain['venue'] ?? ''}'
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
              detail:
                  'Your XI is already the best legal eleven for this gameweek.',
            )
          else
            _Card(
              label: 'Lineup',
              headline:
                  '${bringIn.length} change${bringIn.length == 1 ? '' : 's'}',
              detail: [
                for (var i = 0; i < bringIn.length && i < drop.length; i++)
                  '▲ ${bringIn[i]['web_name']}   ▼ ${drop[i]['web_name']}',
                // ⭐ The engine's own sentence for each swap — *"higher projected xP: 4.8 vs 3.3"* —
                // so a reader can check the call rather than take it.
                ...lineupWhy.map((r) => '$r'),
              ].join('\n'),
            ),
          // ⚠️ Only when the server's own suggestion agrees there is something to do. A button offered
          // beside "No change" would be a button that does nothing.
          if (widget.team.suggestedLineup != null)
            ApplyPlanStrip(team: widget.team, onApply: widget.onApply),
          if (moves.isEmpty)
            const _Card(
              label: 'Transfer',
              headline: 'Hold',
              detail: 'Nothing worth doing with the transfer you hold.',
            )
          else
            for (final m in moves)
              _Card(
                label: 'Transfer',
                headline: '${m['out']['web_name']} → ${m['in']['web_name']}',
                detail: '+${(m['gain'] as num).toStringAsFixed(1)} xP',
                explanation: explanation?['transfer'] as Map<String, dynamic>?,
              ),
          // ⚠️ **Shown whether or not there is a move to make.** "Hold" is a recommendation too, and
          // ⭐ *the reader most likely to want the alternatives is the one who was just told to do
          // nothing.*
          _AlternativesButton(onTap: widget.onAlternatives),
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
            style: TextStyle(
              color: Colors.white24,
              fontSize: 10.5,
              height: 1.5,
            ),
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

    final confidence = Container(
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.fromLTRB(13, 10, 13, 12),
      decoration: BoxDecoration(
        color: Colors.white10,
        // ⭐⭐ **The whole box, not one edge** (feedback). A 3px left rule reads as decoration; a border
        // reads as a **verdict on the card it encloses** — ⚠️ *and this card's colour IS the verdict*,
        // which is why it was the one place a partial border was most misleading.
        border: Border.all(color: colour, width: 1.6),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ⭐⭐ **Top-left, like every other card** (feedback item 2: *"the rest are not aligned with the
          // style card"*). `_Card` puts its label above its headline; this one put `CONFIDENCE` in the
          // top-RIGHT corner, so the screen's first card was the one card that read differently from all
          // the others. ⚠️ *A layout that is unique for no reason reads as a mistake, whatever it looks
          // like on its own.*
          // ⭐ Beside the label, not the number: the question is *what is this?*, and the label is the
          // part a reader is already looking at when they wonder.
          Row(
            children: [
              const Text(
                'CONFIDENCE',
                style: TextStyle(
                  color: Colors.white38,
                  fontSize: 10,
                  letterSpacing: 1,
                ),
              ),
              const HelpDot('confidence', size: 12),
            ],
          ),
          const SizedBox(height: 3),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '$score',
                style: TextStyle(
                  color: colour,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const Text(
                '/100',
                style: TextStyle(color: Colors.white38, fontSize: 12),
              ),
              const SizedBox(width: 8),
              Text(
                band,
                style: TextStyle(
                  color: colour,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          if (actions.isNotEmpty) ...[
            const SizedBox(height: 8),
            // ⚠️⚠️ **A line that costs nothing must not wear a minus sign** (ADR-240). "− 0" beside
            // *"already on your bench"* read as a deduction being taken for something already handled —
            // which is precisely what the bug was, so the display would have kept reporting it after the
            // fix. ⭐ *The renderer has to stop saying it too, or the fix is invisible.*
            for (final lever in actions)
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  (lever['worth'] as num? ?? 0) > 0
                      ? '− ${lever['worth']}  ${lever['what']}'
                      : '✓  ${lever['what']}',
                  style: TextStyle(
                    color: (lever['worth'] as num? ?? 0) > 0
                        ? Brand.warn
                        : Colors.white38,
                    fontSize: 11.5,
                    height: 1.45,
                  ),
                ),
              ),
          ],
          if (levers?['fixed'] != null) ...[
            const SizedBox(height: 4),
            Text(
              'Ceiling: ${levers!['fixed']}',
              style: const TextStyle(
                color: Colors.white38,
                fontSize: 11,
                height: 1.45,
              ),
            ),
          ],
        ],
      ),
    );

    // ⭐⭐ **Three cards, not one wall.** Edge and Risk were sub-sections inside Confidence, so the top of
    // the screen was a single block of six or seven lines while everything below it — Captain, Lineup,
    // Transfer, Timing — came one idea per card. ⚠️ *They are three different questions ("how sure?",
    // "what is going for you?", "what could go wrong?") and they were sharing one box.*
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        confidence,
        if (reasons.isNotEmpty)
          _Lines(
            label: 'Edge',
            mark: '✓',
            colour: Brand.accentTeal,
            lines: reasons,
          ),
        // ⭐ **Risk is always red** (feedback), never amber. The card is the **category**, and a category
        // whose colour changes with its contents cannot be recognised at a glance — ⚠️ *severity belongs
        // in the line ("doubtful, 75%"), not in the frame around it.*
        if (risks.isNotEmpty)
          _Lines(label: 'Risk', mark: '⚠', colour: Brand.bad, lines: risks),
      ],
    );
  }
}

/// A card of one-line points — ⭐ the same shell as [_Card], for content that is a list rather than a
/// headline and a detail.
class _Lines extends StatelessWidget {
  const _Lines({
    required this.label,
    required this.mark,
    required this.colour,
    required this.lines,
  });

  final String label;
  final String mark;
  final Color colour;
  final List<dynamic> lines;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 9),
    padding: const EdgeInsets.fromLTRB(13, 10, 13, 12),
    decoration: BoxDecoration(
      color: Colors.white10,
      // ⭐ Each card bordered in what it **means**: Edge is what is going for you, Risk is what could go
      // wrong. ⚠️ *Three cards in identical grey made the reader do the sorting the colours exist to do.*
      border: Border.all(color: colour.withValues(alpha: 0.75), width: 1.4),
      borderRadius: BorderRadius.circular(Brand.radiusMd),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label.toUpperCase(),
              style: const TextStyle(
                color: Colors.white38,
                fontSize: 10,
                letterSpacing: 1,
              ),
            ),
            HelpDot(label.toLowerCase(), size: 12),
          ],
        ),
        const SizedBox(height: 4),
        for (final line in lines)
          Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Text(
              '$mark  $line',
              style: TextStyle(color: colour, fontSize: 11.5, height: 1.4),
            ),
          ),
      ],
    ),
  );
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
      // ⚠️ **A border always, not only when highlighted.** Transparent-when-not is the same as none, and
      // ⭐ *a card that only gains an outline when it is special leaves every ordinary card looking
      // unfinished beside it.* The accent still marks the highlighted one — it is a stronger colour, not
      // the only colour.
      border: Border.all(
        color: highlight
            ? Brand.purpleLight
            : Brand.accentTeal.withValues(alpha: 0.35),
        width: highlight ? 1.6 : 1.2,
      ),
      borderRadius: BorderRadius.circular(Brand.radiusMd),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label.toUpperCase(),
              style: const TextStyle(
                color: Colors.white38,
                fontSize: 10,
                letterSpacing: 1,
              ),
            ),
            // ⭐ LINEUP was the one heading on this screen with no (?) beside it — ⚠️ *a help affordance
            // that appears on three cards out of six reads as "these three are the complicated ones".*
            HelpDot(label.toLowerCase(), size: 12),
          ],
        ),
        const SizedBox(height: 3),
        Text(
          headline,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 17,
            fontWeight: FontWeight.w700,
          ),
        ),
        if (detail.isNotEmpty) ...[
          const SizedBox(height: 3),
          Text(
            detail,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 12,
              height: 1.5,
            ),
          ),
        ],
        if (explanation != null) ...[
          const SizedBox(height: 7),
          Row(
            children: [
              Text(
                '${explanation!['confidence']}/100',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '${explanation!['band']}',
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ],
          ),
          for (final r in (explanation!['reasons'] as List?) ?? const [])
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                '✓  $r',
                style: const TextStyle(
                  color: Brand.accentTeal,
                  fontSize: 11,
                  height: 1.4,
                ),
              ),
            ),
          for (final r in (explanation!['risks'] as List?) ?? const [])
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                '⚠  $r',
                style: const TextStyle(
                  color: Brand.warn,
                  fontSize: 11,
                  height: 1.4,
                ),
              ),
            ),
        ],
      ],
    ),
  );
}

/// The way into the transfer board from the recommendation that prompted it (ADR-283).
///
/// ⚠️ Deliberately quieter than `ApplyPlanStrip` above it. That strip performs an action; this one only
/// opens a screen — ⭐ *giving them the same weight would make "look at options" compete with "do the
/// thing", and the reader cannot tell which one the app is recommending.*
class _AlternativesButton extends StatelessWidget {
  const _AlternativesButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: Container(
      margin: const EdgeInsets.only(top: 2, bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
      decoration: BoxDecoration(
        border: Border.all(color: Brand.purple.withValues(alpha: 0.65)),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Row(
        children: [
          const Icon(Icons.swap_horiz, size: 16, color: Brand.purple),
          const SizedBox(width: 9),
          const Expanded(
            child: Text(
              'See transfer alternatives',
              style: TextStyle(
                color: Colors.white,
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Icon(
            Icons.chevron_right,
            size: 17,
            color: Brand.purple.withValues(alpha: 0.9),
          ),
        ],
      ),
    ),
  );
}
