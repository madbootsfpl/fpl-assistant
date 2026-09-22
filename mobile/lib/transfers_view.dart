/// Transfers — what a swap is worth (ADR-223).
///
/// ⭐ **Reads the squad the pitch already loaded.** Re-fetching it here would make the two screens capable
/// of disagreeing about who you own, which is the whole failure this app's contract work exists to prevent.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

class TransfersView extends StatefulWidget {
  const TransfersView({
    required this.client,
    required this.team,
    required this.onPlan,
    super.key,
  });

  final ServiceClient client;
  final MyTeam team;

  /// ⚠️ **Plans a swap; it does not make one.** FPL publishes no way to change a team from outside, so the
  /// only honest thing a tap can do is show you the consequence. The real move happens in the FPL app.
  final void Function(int outId, int inId) onPlan;

  @override
  State<TransfersView> createState() => _TransfersViewState();
}

class _TransfersViewState extends State<TransfersView> {
  late int _count = widget.team.freeTransfers.clamp(1, 3);
  late Future<TransfersAnswer> _answer = _load();

  Future<TransfersAnswer> _load() => widget.client.transfers(
        widget.team.analysis.xi.map((p) => p.id).toList()
          ..addAll(widget.team.analysis.bench.map((p) => p.id)),
        benchIds: widget.team.analysis.bench.map((p) => p.id).toList(),
        horizon: 1,
        // ⚠️ The manager's real money, from FPL — not a zero default. ADR-191 is the record of an app
        // advising a position its user was not in.
        bank: widget.team.bank ?? 0.0,
        count: _count,
        limit: 5,
      );

  void _setCount(int n) => setState(() {
        _count = n;
        _answer = _load();
      });

  @override
  Widget build(BuildContext context) => FutureBuilder<TransfersAnswer>(
        future: _answer,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _Message(text: friendlyError(snapshot.error));
          }
          final answer = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 6, 14, 20),
            children: [
              _CountPicker(count: _count, onChanged: _setCount),
              const SizedBox(height: 4),
              Text(
                answer.coordinated
                    // ⭐ The distinction matters and is invisible otherwise: a plan's gains add up because
                    // the moves share a bank; a menu's do not, and adding two double-counts the money.
                    ? 'A plan — these ${answer.moves.length} moves share your bank, so the gains add up.'
                    : 'Alternatives — each priced on its own. Taking two is not worth the sum.',
                style: const TextStyle(color: Colors.white54, fontSize: 11.5, height: 1.45),
              ),
              const SizedBox(height: 12),
              if (answer.moves.isEmpty)
                const _Message(text: 'No transfer improves this squad at the moment.')
              else
                for (final (i, m) in answer.moves.indexed)
                  _Move(
                    move: m,
                    lead: i == 0,
                    onPlan: () => widget.onPlan(m.out.id, m.incoming.id),
                  ),
              const SizedBox(height: 14),
              Text(
                'Ranked over ${answer.horizon} gameweek'
                '${answer.horizon == 1 ? '' : 's'}'
                '${answer.longerWindow == null ? '' : '; near-ties broken on the ${answer.longerWindow}-gameweek view'}.',
                style: const TextStyle(color: Colors.white38, fontSize: 10.5, height: 1.5),
              ),
            ],
          );
        },
      );
}

class _CountPicker extends StatelessWidget {
  const _CountPicker({required this.count, required this.onChanged});

  final int count;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          for (var n = 1; n <= 3; n++)
            Expanded(
              child: GestureDetector(
                onTap: () => onChanged(n),
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 6),
                  padding: const EdgeInsets.symmetric(vertical: 7),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: n == count ? Brand.purple : Colors.white10,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: Text(n == 1 ? '1 move' : '$n moves',
                      style: TextStyle(
                          color: n == count ? Colors.white : Colors.white54,
                          fontSize: 12.5,
                          fontWeight: n == count ? FontWeight.w600 : FontWeight.w400)),
                ),
              ),
            ),
        ],
      );
}

class _Move extends StatelessWidget {
  const _Move({required this.move, required this.lead, required this.onPlan});

  final TransferMove move;
  final VoidCallback onPlan;

  /// ⭐ The first move is the recommendation; the rest are context. Styling them identically would make a
  /// ranked list look like a menu of equals.
  final bool lead;

  @override
  Widget build(BuildContext context) => GestureDetector(
        onTap: onPlan,
        behavior: HitTestBehavior.opaque,
        child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 11),
        decoration: BoxDecoration(
          color: lead ? Brand.purple.withValues(alpha: 0.16) : Colors.white10,
          border: Border.all(color: lead ? Brand.purpleLight : Colors.transparent, width: 1.2),
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(move.out.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: Colors.white54,
                          fontSize: 14,
                          decoration: TextDecoration.lineThrough)),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 7),
                  child: Icon(Icons.arrow_forward, size: 15, color: Brand.purpleLight),
                ),
                Expanded(
                  child: Text(move.incoming.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${move.out.team} £${move.out.price.toStringAsFixed(1)}m'
                    '  →  ${move.incoming.team} £${move.incoming.price.toStringAsFixed(1)}m',
                    style: const TextStyle(color: Colors.white38, fontSize: 11),
                  ),
                ),
                Text('+${move.gain.toStringAsFixed(1)} xP',
                    style: const TextStyle(
                        color: Brand.accentTeal, fontSize: 12.5, fontWeight: FontWeight.w700)),
              ],
            ),
            if (move.outOnBench)
              const Padding(
                padding: EdgeInsets.only(top: 5),
                child: Text(
                  // ⚠️ Selling a benched player lifts the XI by nothing this week — the gain here means
                  // something different, and saying so is cheaper than letting the number mislead.
                  'He is on your bench, so this changes the XI only if someone ahead of him misses.',
                  style: TextStyle(color: Brand.warn, fontSize: 10.5, height: 1.4),
                ),
              ),
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text('Tap to see your pitch with this move',
                  style: TextStyle(color: Colors.white38, fontSize: 10)),
            ),
          ],
        ),
      ));
}

class _Message extends StatelessWidget {
  const _Message({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Center(
          child: SelectableText(text,
              style: const TextStyle(color: Colors.white70, height: 1.55)),
        ),
      );
}
