/// Transfers — what a swap is worth (ADR-223).
///
/// ⭐ **Reads the squad the pitch already loaded.** Re-fetching it here would make the two screens capable
/// of disagreeing about who you own, which is the whole failure this app's contract work exists to prevent.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'boot_battle.dart';
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
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 11.5,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 12),
          if (answer.moves.isEmpty)
            const _Message(
              text: 'No transfer improves this squad at the moment.',
            )
          else
            for (final (i, m) in answer.moves.indexed)
              _Move(
                move: m,
                lead: i == 0,
                client: widget.client,
                onPlan: () => widget.onPlan(m.out.id, m.incoming.id),
              ),
          const SizedBox(height: 14),
          Text(
            'Ranked over ${answer.horizon} gameweek'
            '${answer.horizon == 1 ? '' : 's'}'
            '${answer.longerWindow == null ? '' : '; near-ties broken on the ${answer.longerWindow}-gameweek view'}.',
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 10.5,
              height: 1.5,
            ),
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
              // ⚠️ `FittedBox` because "3 transfers" is materially wider than "3 moves" in a third of
              // a phone's width — ⭐ *a rename can overflow a layout that fitted the old word*.
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  // ⭐ FPL's own word (feedback), matching "Transfer" on the player sheet.
                  n == 1 ? '1 transfer' : '$n transfers',
                  style: TextStyle(
                    color: n == count ? Colors.white : Colors.white54,
                    fontSize: 12.5,
                    fontWeight: n == count ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
              ),
            ),
          ),
        ),
    ],
  );
}

/// ⭐⭐ A move **and the working behind it**. Expanding is lazy: a comparison is fetched only when someone
/// asks for one, so a list of five suggestions costs five requests it never makes.
class _Move extends StatefulWidget {
  const _Move({
    required this.move,
    required this.lead,
    required this.client,
    required this.onPlan,
  });

  final TransferMove move;
  final ServiceClient client;
  final VoidCallback onPlan;

  /// ⭐ The first move is the recommendation; the rest are context. Styling them identically would make a
  /// ranked list look like a menu of equals.
  final bool lead;

  @override
  State<_Move> createState() => _MoveState();
}

class _MoveState extends State<_Move> {
  Future<BootBattle>? _battle;

  void _toggle() {
    setState(() {
      _battle = _battle == null
          ? widget.client.compare(
              widget.move.out.id,
              widget.move.incoming.id,
              horizon: 5,
            )
          : null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final move = widget.move;
    final lead = widget.lead;
    return GestureDetector(
      onTap: widget.onPlan,
      behavior: HitTestBehavior.opaque,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 11),
        decoration: BoxDecoration(
          color: lead ? Brand.purple.withValues(alpha: 0.16) : Colors.white10,
          border: Border.all(
            color: lead ? Brand.purpleLight : Colors.transparent,
            width: 1.2,
          ),
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    move.out.name,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white54,
                      fontSize: 14,
                      decoration: TextDecoration.lineThrough,
                    ),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 7),
                  child: Icon(
                    Icons.arrow_forward,
                    size: 15,
                    color: Brand.purpleLight,
                  ),
                ),
                Expanded(
                  child: Text(
                    move.incoming.name,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
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
                Text(
                  '+${move.gain.toStringAsFixed(1)} xP',
                  style: const TextStyle(
                    color: Brand.accentTeal,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            // ⚠️⚠️ **What the gain assumes you will also do** (ADR-273). The owner: *"Leno to Tzolakis
            // won't provide a +2.2 xP as I will be playing Pickford."* He is right, and so is the
            // number — the gain is measured on the **best legal XI**, so it is real only if the new
            // player actually starts. ⭐ *A conditional gain stated unconditionally is not a number, it
            // is a promise.*
            //
            // ⚠️ This replaced a **guess** that was wrong here: the old note said a benched player
            // changes the XI *"only if someone ahead of him misses"* — false when the incoming player is
            // better than the one starting. ⭐ *A hedge in place of a calculation is not caution; it is a
            // different wrong answer.*
            if (move.needsLineupChange)
              Padding(
                padding: const EdgeInsets.only(top: 5),
                child: Text(
                  'Worth +${move.gain.toStringAsFixed(1)} only if you also start '
                  '${move.incoming.name} ahead of ${move.displaces!.name}. '
                  'Keep ${move.displaces!.name} and this move gains you nothing this week.',
                  style: const TextStyle(
                    color: Brand.warn,
                    fontSize: 10.5,
                    height: 1.4,
                  ),
                ),
              )
            else if (move.outOnBench)
              const Padding(
                padding: EdgeInsets.only(top: 5),
                child: Text(
                  // ⭐ Still true when nothing in the lineup moves: the man leaving was not starting.
                  'He is on your bench, so this changes the XI only if someone ahead of him misses.',
                  style: TextStyle(
                    color: Brand.warn,
                    fontSize: 10.5,
                    height: 1.4,
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Tap to see your pitch with this move',
                      style: TextStyle(color: Colors.white38, fontSize: 10),
                    ),
                  ),
                  GestureDetector(
                    // ⚠️ Its own target, because the card's tap already *plans* the move. Two actions on
                    // one surface need two places to put a thumb.
                    onTap: _toggle,
                    behavior: HitTestBehavior.opaque,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 4,
                        vertical: 2,
                      ),
                      child: Row(
                        children: [
                          Text(
                            _battle == null ? 'Compare' : 'Hide',
                            style: const TextStyle(
                              color: Brand.purpleLight,
                              fontSize: 10.5,
                            ),
                          ),
                          Icon(
                            _battle == null
                                ? Icons.expand_more
                                : Icons.expand_less,
                            size: 14,
                            color: Brand.purpleLight,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            if (_battle != null) BootBattleView(future: _battle!),
          ],
        ),
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(20),
    child: Center(
      child: SelectableText(
        text,
        style: const TextStyle(color: Colors.white70, height: 1.55),
      ),
    ),
  );
}
