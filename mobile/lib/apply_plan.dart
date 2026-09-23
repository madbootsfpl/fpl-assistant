/// "Field the best XI you already own" — the strip at the foot of My Team (ADR-244).
///
/// ⭐⭐⭐ **Two pieces of feedback that turned out to be one thing.** The owner asked to *"optimise My Squad
/// based on This Week"*, and separately noted that the bottom of the pitch was dead space. This is both:
/// the most useful action on the screen, put where the screen had nothing.
///
/// ⚠️⚠️ **It never transfers.** Starting a player you already own is free and reversible; a transfer costs
/// points and cannot be undone. ⭐ *One button must not do both, whatever the xP says* — the Transfers tab
/// is a deliberate second decision, not friction to be smoothed away.
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'brand.dart';

class ApplyPlanStrip extends StatelessWidget {
  const ApplyPlanStrip({required this.team, required this.onApply, super.key});

  final MyTeam team;
  final Future<void> Function(SuggestedLineup) onApply;

  @override
  Widget build(BuildContext context) {
    final plan = team.suggestedLineup;

    // ⭐ **Nothing to do is worth saying once, quietly.** A strip that shouted "your lineup is optimal"
    // every visit would be noise; one that vanished entirely would leave a reader wondering whether the
    // app had checked. ⚠️ *Silence and reassurance are different answers and both are sometimes right.*
    if (plan == null || plan.changes == 0) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 5),
        decoration: BoxDecoration(
          color: Brand.ink.withValues(alpha: 0.55),
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: const Text(
          '✓  Your XI is already the best eleven you own',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white54, fontSize: 11),
        ),
      );
    }

    final names = [for (final id in plan.bringIn) team.nameOf(id)]
        .where((n) => n.isNotEmpty)
        .toList();

    // ⭐⭐ **One line, where three were** (ADR-253). The information stays — *what it is worth* and *who
    // comes in* — because that is the reason to press it, and the competitor's equivalent button says
    // nothing at all. ⚠️ What went is the **height**: a three-line card at the foot of the pitch cost
    // ~100pt, and the pitch is the screen.
    return Container(
      padding: const EdgeInsets.fromLTRB(11, 6, 6, 6),
      decoration: BoxDecoration(
        color: Brand.purple.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text.rich(
              TextSpan(
                children: [
                  TextSpan(
                    // ⭐ The gain first, because it is the reason. "2 changes" is a cost; "+1.6 xP" is
                    // what the cost buys, and a manager decides on the second.
                    text: '+${plan.gain.toStringAsFixed(1)} xP',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  TextSpan(
                    // ⚠️ Names, not a count — "2 changes" is a number you then have to go and look up.
                    text: names.isEmpty
                        ? '  from ${plan.changes} change'
                              '${plan.changes == 1 ? '' : 's'}'
                        : '  ·  start ${_list(names)}',
                    style: const TextStyle(color: Colors.white70),
                  ),
                ],
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
          ),
          const SizedBox(width: 6),
          TextButton(
            onPressed: () => onApply(plan),
            style: TextButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Brand.purple,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
              minimumSize: const Size(0, 30),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(Brand.radiusSm),
              ),
            ),
            child: Text(
              // ⭐ **"Play Him", asked for by name** (feedback) — ⚠️ but the plan can start more than one,
              // and the strip beside it literally reads *"start Salah and Saka"*. A flat rename would
              // have read *"Play Him"* over a two-player change. ⭐ *A label is part of the sentence the
              // screen is saying, not a word on its own.*
              plan.bringIn.length == 1 ? 'Play Him' : 'Play Them',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }

  /// `a`, `a and b`, `a, b and c` — ⭐ an Oxford-free list, because it is read aloud in someone's head.
  static String _list(List<String> names) {
    if (names.length == 1) return names.single;
    return '${names.sublist(0, names.length - 1).join(', ')} and ${names.last}';
  }
}
