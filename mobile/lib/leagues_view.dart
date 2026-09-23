/// Mini-leagues — the table, what everyone captained, and you against one rival (ADR-267).
///
/// ⭐⭐ **The head-to-head is the reason this screen exists.** A table tells you who is ahead, which you
/// already knew; ⚠️ *it cannot tell you whether that is about to change.* The comparison can: it strips
/// out the players you both own — usually most of both squads — and prices only what actually separates
/// you.
///
/// ⚠️⚠️ **The captain split costs one FPL request per manager**, so it is fetched only when that tab is
/// opened. ⭐ *A screen that quietly spends fifty requests to draw a panel nobody looked at is a screen
/// that will be blamed for being slow.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'mugshot.dart';

class LeaguesView extends StatefulWidget {
  const LeaguesView({required this.client, required this.managerId, super.key});

  final ServiceClient client;
  final int managerId;

  @override
  State<LeaguesView> createState() => _LeaguesViewState();
}

class _LeaguesViewState extends State<LeaguesView> {
  late Future<List<LeagueSummary>> _leagues = widget.client.leagues(
    widget.managerId,
  );
  LeagueSummary? _picked;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<LeagueSummary>>(
    future: _leagues,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return _Problem(
          message: friendlyError(snapshot.error),
          onRetry: () => setState(
            () => _leagues = widget.client.leagues(widget.managerId),
          ),
        );
      }
      final leagues = snapshot.data!;
      if (leagues.isEmpty) {
        return const _Problem(
          message: 'No classic leagues on this manager id. Join one in the FPL app and it will appear here.',
        );
      }
      final chosen = _picked ?? leagues.first;
      return Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
            child: _LeaguePicker(
              leagues: leagues,
              chosen: chosen,
              onPick: (l) => setState(() => _picked = l),
            ),
          ),
          Expanded(
            child: _OneLeague(
              // ⭐ Keyed by league, so switching rebuilds the tabs rather than showing the previous
              // league's table under the new league's name.
              key: ValueKey(chosen.id),
              client: widget.client,
              league: chosen,
              managerId: widget.managerId,
            ),
          ),
        ],
      );
    },
  );
}

class _LeaguePicker extends StatelessWidget {
  const _LeaguePicker({
    required this.leagues,
    required this.chosen,
    required this.onPick,
  });

  final List<LeagueSummary> leagues;
  final LeagueSummary chosen;
  final ValueChanged<LeagueSummary> onPick;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
    decoration: BoxDecoration(
      color: Colors.white10,
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: DropdownButtonHideUnderline(
      child: DropdownButton<LeagueSummary>(
        value: chosen,
        isExpanded: true,
        dropdownColor: const Color(0xFF241E30),
        iconEnabledColor: Colors.white54,
        style: const TextStyle(color: Colors.white, fontSize: 13.5),
        items: [
          for (final l in leagues)
            DropdownMenuItem(
              value: l,
              child: Row(
                children: [
                  Flexible(
                    child: Text(l.name, overflow: TextOverflow.ellipsis),
                  ),
                  // ⭐ Size beside the name, because "Overall" and a twelve-player league are the same
                  // word to a dropdown and completely different things to a reader.
                  Text(
                    '  ${_short(l.size)}',
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
        ],
        onChanged: (l) => l == null ? null : onPick(l),
      ),
    ),
  );
}

/// `12`, `1.3k`, `10.8m` — ⚠️ *a league size is a scale, not a count you read digit by digit.*
String _short(int n) {
  if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}m';
  if (n >= 1000) return '${(n / 1000).toStringAsFixed(n >= 10000 ? 0 : 1)}k';
  return '$n';
}

class _OneLeague extends StatefulWidget {
  const _OneLeague({
    required this.client,
    required this.league,
    required this.managerId,
    super.key,
  });

  final ServiceClient client;
  final LeagueSummary league;
  final int managerId;

  @override
  State<_OneLeague> createState() => _OneLeagueState();
}

class _OneLeagueState extends State<_OneLeague> {
  int _tab = 0;

  /// ⭐ The table is cheap and always fetched; the captain split is the same call **asking for more**, so
  /// it replaces this future rather than adding a second one.
  late Future<LeagueTable> _table = widget.client.league(widget.league.id);
  bool _askedCaptains = false;

  void _pickTab(int tab) {
    setState(() {
      _tab = tab;
      // ⚠️ Fetched on first open only. ⭐ *A panel that re-spends twenty requests every time you tab back
      // to it is a panel that punishes browsing.*
      if (tab == 1 && !_askedCaptains) {
        _askedCaptains = true;
        _table = widget.client.league(widget.league.id, withCaptains: true);
      }
    });
  }

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(14, 2, 14, 6),
        child: Row(
          children: [
            for (final (i, label) in const [
              (0, 'Table'),
              (1, 'Captains'),
              (2, 'Head to head'),
            ])
              Expanded(
                child: GestureDetector(
                  onTap: () => _pickTab(i),
                  behavior: HitTestBehavior.opaque,
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: _tab == i ? Brand.purple : Colors.white10,
                      borderRadius: BorderRadius.circular(Brand.radiusPill),
                    ),
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        label,
                        style: TextStyle(
                          color: _tab == i ? Colors.white : Colors.white54,
                          fontSize: 12.5,
                          fontWeight: _tab == i
                              ? FontWeight.w600
                              : FontWeight.w400,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
      Expanded(
        child: FutureBuilder<LeagueTable>(
          future: _table,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    if (_tab == 1)
                      const Padding(
                        padding: EdgeInsets.only(top: 14),
                        child: Text(
                          // ⚠️ Says why it is slow, because it is — one read per manager.
                          'Reading each manager’s squad…',
                          style: TextStyle(
                            color: Colors.white38,
                            fontSize: 11.5,
                          ),
                        ),
                      ),
                  ],
                ),
              );
            }
            if (snapshot.hasError) {
              return _Problem(message: friendlyError(snapshot.error));
            }
            final table = snapshot.data!;
            return switch (_tab) {
              1 => _Captains(table: table),
              2 => _HeadToHead(
                client: widget.client,
                table: table,
                managerId: widget.managerId,
              ),
              _ => _Table(table: table),
            };
          },
        ),
      ),
    ],
  );
}

class _Table extends StatelessWidget {
  const _Table({required this.table});

  final LeagueTable table;

  @override
  Widget build(BuildContext context) => ListView.builder(
    padding: const EdgeInsets.fromLTRB(14, 4, 14, 20),
    itemCount: table.rows.length,
    itemBuilder: (_, i) {
      final row = table.rows[i];
      return Container(
        margin: const EdgeInsets.only(bottom: 5),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(Brand.radiusSm),
        ),
        child: Row(
          children: [
            SizedBox(
              width: 26,
              child: Text(
                '${row.rank}',
                style: const TextStyle(color: Colors.white54, fontSize: 12),
              ),
            ),
            SizedBox(width: 30, child: _Movement(movement: row.movement)),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    row.team,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    row.manager,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 10.5,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${row.total}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  'GW ${row.gwPoints}',
                  style: const TextStyle(color: Colors.white38, fontSize: 10.5),
                ),
              ],
            ),
          ],
        ),
      );
    },
  );
}

/// ⚠️ **Null is "new", not "level".** A manager with no previous rank has not fallen four hundred places,
/// and showing a dash for both would hide the distinction the server went to trouble to keep.
class _Movement extends StatelessWidget {
  const _Movement({required this.movement});

  final int? movement;

  @override
  Widget build(BuildContext context) {
    final m = movement;
    if (m == null) {
      return const Text(
        'new',
        style: TextStyle(color: Colors.white24, fontSize: 9.5),
      );
    }
    if (m == 0) {
      return const Text(
        '–',
        style: TextStyle(color: Colors.white24, fontSize: 11),
      );
    }
    final up = m > 0;
    return Row(
      children: [
        Icon(
          up ? Icons.arrow_upward : Icons.arrow_downward,
          size: 10,
          color: up ? Brand.good : Brand.warn,
        ),
        Text(
          '${m.abs()}',
          style: TextStyle(color: up ? Brand.good : Brand.warn, fontSize: 10.5),
        ),
      ],
    );
  }
}

class _Captains extends StatelessWidget {
  const _Captains({required this.table});

  final LeagueTable table;

  @override
  Widget build(BuildContext context) {
    if (table.captains.isEmpty) {
      return const _Problem(
        message:
            'No captain data yet — this needs a finished gameweek, because picks only become public '
            'after a deadline.',
      );
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 4, 14, 20),
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Text(
            // ⚠️ **Says what it stands on.** A partial read must never present itself as the whole
            // league (ADR-215's rule), and "5 of 12" is the difference between a fact and an impression.
            'From ${table.captainsFrom} squads'
            '${table.gameweek == null ? '' : ', GW${table.gameweek}'}.',
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 11,
              height: 1.5,
            ),
          ),
        ),
        for (final c in table.captains) _CaptainRow(pick: c),
      ],
    );
  }
}

class _CaptainRow extends StatelessWidget {
  const _CaptainRow({required this.pick});

  final LeagueCaptain pick;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
    decoration: BoxDecoration(
      color: Colors.white10,
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                pick.player.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: LinearProgressIndicator(
                    value: (pick.share / 100).clamp(0.0, 1.0),
                    minHeight: 5,
                    backgroundColor: Colors.white12,
                    valueColor: const AlwaysStoppedAnimation(Brand.purple),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 10),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${pick.share.toStringAsFixed(0)}%',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              '${pick.count} of them',
              style: const TextStyle(color: Colors.white38, fontSize: 10),
            ),
          ],
        ),
      ],
    ),
  );
}

class _HeadToHead extends StatefulWidget {
  const _HeadToHead({
    required this.client,
    required this.table,
    required this.managerId,
  });

  final ServiceClient client;
  final LeagueTable table;
  final int managerId;

  @override
  State<_HeadToHead> createState() => _HeadToHeadState();
}

class _HeadToHeadState extends State<_HeadToHead> {
  LeagueStanding? _rival;
  Future<HeadToHead>? _future;

  void _pick(LeagueStanding rival) {
    setState(() {
      _rival = rival;
      _future = widget.client.headToHead(widget.managerId, rival.entry);
    });
  }

  @override
  Widget build(BuildContext context) {
    // ⚠️ You cannot play yourself, and the server refuses it — so the list never offers it.
    final rivals = widget.table.rows
        .where((r) => r.entry != widget.managerId)
        .toList();

    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 4, 14, 20),
      children: [
        // ⭐⭐ **A dropdown, not a swipe row** (feedback). A league can hold fifty managers, and a
        // horizontal strip shows four — ⚠️ *an option you have to swipe to discover is an option most
        // people never learn is there*, which made the comparison look like it only worked against the
        // top of the table.
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.white10,
            borderRadius: BorderRadius.circular(Brand.radiusSm),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<LeagueStanding>(
              value: _rival,
              isExpanded: true,
              dropdownColor: const Color(0xFF241E30),
              iconEnabledColor: Colors.white54,
              style: const TextStyle(color: Colors.white, fontSize: 13.5),
              hint: const Text(
                'Compare against…',
                style: TextStyle(color: Colors.white54, fontSize: 13.5),
              ),
              items: [
                for (final r in rivals)
                  DropdownMenuItem(
                    value: r,
                    child: Row(
                      children: [
                        // ⭐ Rank first, so the list reads as the table you just looked at.
                        SizedBox(
                          width: 28,
                          child: Text(
                            '${r.rank}',
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 12,
                            ),
                          ),
                        ),
                        Flexible(
                          child: Text(r.team, overflow: TextOverflow.ellipsis),
                        ),
                      ],
                    ),
                  ),
              ],
              onChanged: (r) => r == null ? null : _pick(r),
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (_future != null)
          FutureBuilder<HeadToHead>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return _Problem(message: friendlyError(snapshot.error));
              }
              return _Decomposition(h2h: snapshot.data!, rival: _rival!);
            },
          ),
      ],
    );
  }
}

class _Decomposition extends StatelessWidget {
  const _Decomposition({required this.h2h, required this.rival});

  final HeadToHead h2h;
  final LeagueStanding rival;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: (h2h.iAmAhead ? Brand.good : Brand.warn).withValues(
            alpha: 0.16,
          ),
          borderRadius: BorderRadius.circular(Brand.radiusMd),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              // ⭐ The gap first, signed and named. *"+2.4 xP ahead"* is the answer; the sentence below
              // is the explanation.
              '${h2h.gap > 0 ? '+' : ''}${h2h.gap.toStringAsFixed(1)} xP '
              '${h2h.iAmAhead ? 'ahead' : 'behind'}',
              style: TextStyle(
                color: h2h.iAmAhead ? Brand.good : Brand.warn,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              h2h.note,
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 12,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 10),
      Text(
        // ⚠️⚠️ **The shared total, stated and then set aside.** It is usually most of both squads and the
        // part you cannot act on — ⭐ *printing it is what makes a 2 xP gap believable rather than looking
        // like a rounding error on two big numbers.*
        '${h2h.sharedCount} players you both start cancel out '
        '(${h2h.sharedXp.toStringAsFixed(1)} xP each way). '
        'What is left is what can separate you:',
        style: const TextStyle(
          color: Colors.white38,
          fontSize: 11,
          height: 1.55,
        ),
      ),
      const SizedBox(height: 10),
      _EdgeList(title: 'Only you', rows: h2h.myEdge, good: true),
      const SizedBox(height: 8),
      _EdgeList(title: 'Only ${rival.team}', rows: h2h.theirEdge, good: false),
    ],
  );
}

class _EdgeList extends StatelessWidget {
  const _EdgeList({
    required this.title,
    required this.rows,
    required this.good,
  });

  final String title;
  final List<EdgePlayer> rows;
  final bool good;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsets.only(bottom: 5),
        child: Text(
          title,
          style: TextStyle(
            color: good ? Brand.good : Brand.warn,
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      if (rows.isEmpty)
        const Text(
          'Nobody — identical on this side.',
          style: TextStyle(color: Colors.white24, fontSize: 11),
        ),
      for (final row in rows)
        Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            children: [
              Mugshot(url: '', name: row.player.name, size: 22),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  row.player.name,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontSize: 12.5),
                ),
              ),
              if (row.isCaptain)
                Container(
                  margin: const EdgeInsets.only(right: 6),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 5,
                    vertical: 1,
                  ),
                  decoration: BoxDecoration(
                    color: Brand.purple,
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: const Text(
                    'C',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              // ⭐ A doubt shown on the differential — ⚠️ *these are the players the screen is about, and
              // the engine's own row could not carry a status at all* (ADR-227's sweep found it).
              if (row.player.chance != null && row.player.chance! < 100)
                Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: Text(
                    '${row.player.chance}%',
                    style: const TextStyle(color: Brand.warn, fontSize: 10),
                  ),
                ),
              Text(
                row.xp.toStringAsFixed(1),
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
    ],
  );
}

class _Problem extends StatelessWidget {
  const _Problem({required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(20),
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        SelectableText(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 12.5,
            height: 1.55,
          ),
        ),
        if (onRetry != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: TextButton(
              onPressed: onRetry,
              child: const Text('Try again'),
            ),
          ),
      ],
    ),
  );
}
