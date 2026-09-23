/// The crowd's leaderboards — most bought, most sold, most owned, in form (ADR-266).
///
/// ⭐⭐ **Trending returns as a tab, not as the screen ADR-245 removed.** That ADR folded the old Trending
/// page into the market scope and was right to: *"what is notable?"* was being asked twice. This is the
/// other question — **the charts** — ordered by how many managers moved, where the market scope orders by
/// **how strong the evidence is** (ADR-150). ⚠️ *Same data, genuinely different ordering, which is why
/// one cannot serve the other.*
///
/// ⚠️⚠️ **This is the weakest evidence in the app and the screen says so.** ⭐ *"Lots of people did this"
/// is a fact about other managers, not about the player* — the reason a template forms, and not on its
/// own a reason to join one. The caveat travels **with the numbers** from the server, so it cannot drift
/// from what it is warning about.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'mugshot.dart';

class TrendingBoards extends StatefulWidget {
  const TrendingBoards({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<TrendingBoards> createState() => _TrendingBoardsState();
}

class _TrendingBoardsState extends State<TrendingBoards> {
  /// ⭐ **Opens on "most bought"**, because that is the board people come for — *who is everyone buying?*
  /// is the question that sends someone here, and "most owned" is the one that changes slowest.
  String _by = 'in';

  late Future<TrendingBoard> _future = _fetch();

  List<int> get _squadIds => [
    ...widget.team.analysis.xi.map((p) => p.id),
    ...widget.team.analysis.bench.map((p) => p.id),
  ];

  Future<TrendingBoard> _fetch() =>
      widget.client.trending(by: _by, playerIds: _squadIds);

  void _pick(String by) {
    if (by == _by) return;
    setState(() {
      _by = by;
      _future = _fetch();
    });
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
        child: SizedBox(
          height: 34,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              for (final (value, label) in const [
                ('in', 'Most bought'),
                ('out', 'Most sold'),
                ('owned', 'Most owned'),
                ('form', 'In form'),
              ])
                Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: ChoiceChip(
                    label: Text(label),
                    labelStyle: TextStyle(
                      fontSize: 11.5,
                      color: _by == value ? Colors.white : Colors.white54,
                    ),
                    selected: _by == value,
                    showCheckmark: false,
                    backgroundColor: Colors.white10,
                    selectedColor: Brand.purple,
                    side: BorderSide.none,
                    onSelected: (_) => _pick(value),
                  ),
                ),
            ],
          ),
        ),
      ),
      Expanded(
        child: FutureBuilder<TrendingBoard>(
          future: _future,
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
            final board = snapshot.data!;
            return ListView(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 22),
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text(
                    // ⭐ The server's own words for the board and its warning — ⚠️ *a caveat written into
                    // the app can drift from the numbers it is about; one that arrives with them cannot.*
                    board.caveat,
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 11,
                      height: 1.5,
                    ),
                  ),
                ),
                if (board.rows.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(24),
                    child: Text(
                      'Nothing on this board yet — these numbers fill up across a gameweek.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white38, fontSize: 12.5),
                    ),
                  ),
                for (final row in board.rows)
                  _BoardRow(row: row, column: board.column),
              ],
            );
          },
        ),
      ),
    ],
  );
}

/// How a board's number reads. ⭐ **Net transfers are people**, so 660754 becomes `661k` — ⚠️ *a raw
/// six-digit count is a number you have to parse before you can compare two of them.*
String trendValue(double value, String column) {
  if (column == 'Own%') return '${value.toStringAsFixed(1)}%';
  if (column == 'Form') return value.toStringAsFixed(1);
  final n = value.abs();
  final sign = value < 0 ? '−' : '';
  if (n >= 1000000) return '$sign${(n / 1000000).toStringAsFixed(1)}m';
  if (n >= 1000) return '$sign${(n / 1000).round()}k';
  return '$sign${n.round()}';
}

class _BoardRow extends StatelessWidget {
  const _BoardRow({required this.row, required this.column});

  final TrendingRow row;
  final String column;

  @override
  Widget build(BuildContext context) {
    final p = row.player;
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusSm),
        // ⭐ One of yours is outlined rather than badged — *the crowd's charts are worth reading
        // differently when you are already in the trade.*
        border: row.owned
            ? Border.all(color: Brand.purple.withValues(alpha: 0.8))
            : null,
      ),
      child: Row(
        children: [
          Mugshot(url: row.photo, name: p.name, size: 28),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        p.name,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    if (row.owned)
                      const Padding(
                        padding: EdgeInsets.only(left: 6),
                        child: Text(
                          'yours',
                          style: TextStyle(color: Colors.white54, fontSize: 10),
                        ),
                      ),
                  ],
                ),
                Text(
                  // ⭐ Ownership on every board, because *"661k bought him"* means something different at
                  // 4% than at 40% — the number that makes the others readable.
                  '${p.team} · £${p.price.toStringAsFixed(1)}m'
                  '${row.ownedBy == null ? '' : ' · ${row.ownedBy!.toStringAsFixed(1)}% owned'}'
                  '${row.tier.isEmpty ? '' : ' · ${row.tier}'}',
                  style: const TextStyle(color: Colors.white38, fontSize: 10.5),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                trendValue(row.value, column),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                // ⚠️ The column names the unit. Four boards share `value`, and ⭐ *a number with no unit
                // is not information.*
                column,
                style: const TextStyle(color: Colors.white30, fontSize: 9.5),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
