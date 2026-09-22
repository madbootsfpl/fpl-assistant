/// Players — the market (ADR-230).
///
/// ⭐⭐ **Fetched once, filtered on the device.** The whole ranked market is ~110 KB and searching 481 rows
/// locally is instant; a round trip per keystroke is not. *The cheap thing sent once beats the small thing
/// sent constantly* — which is the same payload reasoning spike 017 used to make this client's whole
/// architecture.
///
/// ⚠️ **Players who cannot play are already gone** — the server excludes them, because a browse list is
/// for finding someone to buy. Doubtful players stay and are flagged: a doubt is a probability, not a
/// verdict (ADR-206).
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

const List<String> _positions = ['GK', 'DEF', 'MID', 'FWD'];

class PlayersView extends StatefulWidget {
  const PlayersView({required this.client, required this.owned, super.key});

  final ServiceClient client;

  /// ⭐ Ids you already hold, so the list can say so. A market list that does not know what you own makes
  /// you check your own pitch to read it.
  final Set<int> owned;

  @override
  State<PlayersView> createState() => _PlayersViewState();
}

class _PlayersViewState extends State<PlayersView> {
  late final Future<List<PlayerSummary>> _all = widget.client.players(horizon: 5);
  final TextEditingController _search = TextEditingController();
  String? _position;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  List<PlayerSummary> _filtered(List<PlayerSummary> all) {
    final term = _search.text.trim().toLowerCase();
    return all.where((p) {
      if (_position != null && p.position != _position) return false;
      if (term.isEmpty) return true;
      // ⭐ Name **or** club: "ars" should find Arsenal's players, which is how a manager actually looks.
      return p.name.toLowerCase().contains(term) || p.team.toLowerCase().contains(term);
    }).toList();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<PlayerSummary>>(
        future: _all,
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
          final all = snapshot.data!;
          final shown = _filtered(all);

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 8, 14, 4),
                child: TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Search a player or club',
                    hintStyle: const TextStyle(color: Colors.white38, fontSize: 13.5),
                    prefixIcon: const Icon(Icons.search, size: 18, color: Colors.white38),
                    isDense: true,
                    filled: true,
                    fillColor: Colors.white10,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(Brand.radiusSm),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
              ),
              SizedBox(
                height: 38,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  children: [
                    _Chip(
                      label: 'All',
                      on: _position == null,
                      onTap: () => setState(() => _position = null),
                    ),
                    for (final pos in _positions)
                      _Chip(
                        label: pos,
                        on: _position == pos,
                        onTap: () => setState(() => _position = pos),
                      ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 2, 16, 6),
                child: Row(
                  children: [
                    Text(
                      // ⭐ "of" matters: the list is filtered, and a bare count implies it is everyone.
                      shown.length == all.length
                          ? '${all.length} players, best first'
                          : '${shown.length} of ${all.length}',
                      style: const TextStyle(color: Colors.white38, fontSize: 11),
                    ),
                    const Spacer(),
                    const Text('xP over 5 GW',
                        style: TextStyle(color: Colors.white24, fontSize: 10.5)),
                  ],
                ),
              ),
              Expanded(
                child: shown.isEmpty
                    ? const Center(
                        child: Text('Nobody matches that.',
                            style: TextStyle(color: Colors.white38)))
                    : ListView.builder(
                        itemCount: shown.length,
                        itemBuilder: (_, i) => _Row(
                          player: shown[i],
                          owned: widget.owned.contains(shown[i].id),
                          client: widget.client,
                        ),
                      ),
              ),
            ],
          );
        },
      );
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, required this.on, required this.onTap});

  final String label;
  final bool on;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 5),
          padding: const EdgeInsets.symmetric(horizontal: 14),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: on ? Brand.purple : Colors.white10,
            borderRadius: BorderRadius.circular(Brand.radiusPill),
          ),
          child: Text(label,
              style: TextStyle(
                  color: on ? Colors.white : Colors.white54,
                  fontSize: 12.5,
                  fontWeight: on ? FontWeight.w600 : FontWeight.w400)),
        ),
      );
}

/// ⭐⭐ **The card opens where the row is.** The Hub does this and it is the right shape: a list you can
/// interrogate without leaving it beats a list that sends you somewhere and loses your place in it.
///
/// ⚠️ The detail is fetched **on expand**, never with the list.
class _Row extends StatefulWidget {
  const _Row({required this.player, required this.owned, required this.client});

  final PlayerSummary player;
  final bool owned;
  final ServiceClient client;

  @override
  State<_Row> createState() => _RowState();
}

class _RowState extends State<_Row> {
  Future<PlayerCard>? _card;

  void _toggle() => setState(() {
        _card = _card == null ? widget.client.player(widget.player.id, horizon: 5) : null;
      });

  @override
  Widget build(BuildContext context) {
    final player = widget.player;
    final owned = widget.owned;
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white10)),
      ),
      child: Column(
        children: [
          GestureDetector(
            onTap: _toggle,
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 9, 16, 9),
              child: Row(
          children: [
            SizedBox(
              width: 34,
              child: Text(player.position,
                  style: const TextStyle(color: Colors.white38, fontSize: 11)),
            ),
            Expanded(
              child: Row(
                children: [
                  Flexible(
                    child: Text(player.name,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Colors.white, fontSize: 14)),
                  ),
                  if (owned)
                    // ⭐ A market list that does not know what you own makes you check your own pitch to
                    // read it.
                    Container(
                      margin: const EdgeInsets.only(left: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 6),
                      decoration: BoxDecoration(
                        color: Brand.goodTint,
                        borderRadius: BorderRadius.circular(Brand.radiusPill),
                      ),
                      child: const Text('owned',
                          style: TextStyle(color: Brand.goodFg, fontSize: 9)),
                    ),
                  if (player.isLeaving)
                    const Padding(
                      padding: EdgeInsets.only(left: 5),
                      child: Text('✈', style: TextStyle(color: Brand.bad, fontSize: 11)),
                    )
                  else if (player.isDoubtful)
                    Padding(
                      padding: const EdgeInsets.only(left: 5),
                      child: Text('${player.chance ?? '?'}%',
                          style: const TextStyle(color: Brand.warn, fontSize: 10)),
                    ),
                ],
              ),
            ),
            SizedBox(
              width: 42,
              child: Text(player.team,
                  style: const TextStyle(color: Colors.white38, fontSize: 11)),
            ),
            SizedBox(
              width: 48,
              child: Text('£${player.price.toStringAsFixed(1)}',
                  textAlign: TextAlign.right,
                  style: const TextStyle(color: Colors.white60, fontSize: 12.5)),
            ),
            SizedBox(
              width: 52,
              child: Text(player.xp.toStringAsFixed(1),
                  textAlign: TextAlign.right,
                  style: const TextStyle(
                      color: Brand.accentTeal, fontSize: 13.5, fontWeight: FontWeight.w700)),
            ),
            Icon(_card == null ? Icons.expand_more : Icons.expand_less,
                size: 16, color: Colors.white24),
          ],
        ),
      ),
    ),
    if (_card != null) _Card(future: _card!),
  ],
  ),
);
  }
}

/// The expanded detail. ⭐ Three blocks — the season, the recent past, the projected run — because those
/// are the three different questions a reader has about a name on a list.
class _Card extends StatelessWidget {
  const _Card({required this.future});

  final Future<PlayerCard> future;

  @override
  Widget build(BuildContext context) => FutureBuilder<PlayerCard>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Center(
                child: SizedBox(
                    width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
              ),
            );
          }
          if (snapshot.hasError) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Text(friendlyError(snapshot.error),
                  style: const TextStyle(color: Colors.white54, fontSize: 11, height: 1.45)),
            );
          }
          final card = snapshot.data!;
          return Container(
            width: double.infinity,
            color: Colors.white.withValues(alpha: 0.03),
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ⭐ The run first: a reader opening a row is usually asking *"is he good, or is this an
                // easy month?"*, and the fixtures are half that answer.
                const Text('NEXT', style: TextStyle(color: Colors.white24, fontSize: 9, letterSpacing: 1)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    for (final f in card.fixtures)
                      Expanded(
                        child: Container(
                          margin: const EdgeInsets.only(right: 3),
                          padding: const EdgeInsets.symmetric(vertical: 3),
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            // ⭐ Difficulty colours the FIXTURE, not the player — which is the distinction
                            // ADR-179 protects: a hue about the opponent, beside a number about the player.
                            color: Brand.fdr[f.difficulty]?.background ?? Colors.white10,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text('${f.opponent} (${f.venue})',
                              style: TextStyle(
                                  color: Brand.fdr[f.difficulty]?.foreground ?? Colors.white54,
                                  fontSize: 9,
                                  fontWeight: FontWeight.w600)),
                        ),
                      ),
                  ],
                ),
                if (card.recent.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  const Text('LAST 5',
                      style: TextStyle(color: Colors.white24, fontSize: 9, letterSpacing: 1)),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      for (final g in card.recent)
                        Expanded(
                          child: Container(
                            margin: const EdgeInsets.only(right: 3),
                            padding: const EdgeInsets.symmetric(vertical: 3),
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: Colors.white10,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Column(
                              children: [
                                Text('${g.points}',
                                    style: const TextStyle(
                                        color: Colors.white70,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700)),
                                Text("${g.minutes}'",
                                    style:
                                        const TextStyle(color: Colors.white24, fontSize: 7.5)),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
                const SizedBox(height: 10),
                // ⭐ Two columns, because twelve stats in one list is a wall a reader scrolls past.
                Wrap(
                  spacing: 18,
                  runSpacing: 3,
                  children: [
                    for (final stat in card.stats)
                      SizedBox(
                        width: 150,
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(stat.label,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                      color: Colors.white38, fontSize: 10.5)),
                            ),
                            Text(stat.value,
                                style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600)),
                          ],
                        ),
                      ),
                  ],
                ),
              ],
            ),
          );
        },
      );
}
