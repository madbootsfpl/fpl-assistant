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
      return const Padding(
        padding: EdgeInsets.fromLTRB(14, 14, 14, 10),
        child: Text(
          '✓  Your XI is already the best eleven you own this week.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white24, fontSize: 11.5),
        ),
      );
    }

    final names = [for (final id in plan.bringIn) team.nameOf(id)]
        .where((n) => n.isNotEmpty)
        .toList();

    return Container(
      margin: const EdgeInsets.fromLTRB(10, 12, 10, 8),
      padding: const EdgeInsets.fromLTRB(13, 11, 11, 11),
      decoration: BoxDecoration(
        color: Brand.purple.withValues(alpha: 0.18),
        border: Border.all(color: Brand.purpleLight, width: 1.1),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  // ⭐ The gain first, because it is the reason. "2 changes" is a cost; "+5.5 points" is
                  // what the cost buys, and a manager decides on the second.
                  '+${plan.gain.toStringAsFixed(1)} xP from ${plan.changes} '
                  'change${plan.changes == 1 ? '' : 's'}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (names.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      // ⚠️ Names, not a count. "2 changes" is a number you have to go and look up;
                      // "Start Semenyo and Barry" is the thing itself.
                      'Start ${_list(names)}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white60,
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          TextButton(
            onPressed: () => onApply(plan),
            style: TextButton.styleFrom(
              backgroundColor: Brand.purple,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(Brand.radiusSm),
              ),
            ),
            child: const Text('Field it', style: TextStyle(fontSize: 12.5)),
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
