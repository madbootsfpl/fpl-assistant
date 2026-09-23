/// The fixture-difficulty ticker — every club, their next six, easiest run first (ADR-265).
///
/// ⭐⭐ **A grid, because the question is comparative.** *"Are Arsenal's fixtures good?"* has no answer on
/// its own; *"whose run turns good in three weeks?"* does, and only a shape that puts twenty clubs beside
/// each other can show it. ⚠️ *A per-club fixture list is the same data arranged so the comparison cannot
/// be made.*
///
/// ⭐ **The colours are FPL's 1-5 scale** so it reads the way the official app has trained everyone to
/// read it — ⚠️ *a familiar scale with unfamiliar colours is a scale you have to learn twice.*
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';

/// Green for easy, red for hard — ⚠️ **the FPL app's direction**, and the one place a reversal would be
/// silently catastrophic: a reader does not check a colour legend, they act on it.
Color difficultyColour(int difficulty) => switch (difficulty) {
  1 => const Color(0xFF1B8A4B),
  2 => const Color(0xFF4CC46A),
  3 => const Color(0xFF6B6B7B),
  4 => const Color(0xFFE05A4E),
  _ => const Color(0xFF9B1C2E),
};

/// Text that stays legible on each of those — ⚠️ the mid grey is dark enough that white wins, but the
/// bright green is not.
Color difficultyInk(int difficulty) =>
    difficulty == 2 ? const Color(0xFF07240F) : Colors.white;

class TickerView extends StatefulWidget {
  const TickerView({required this.client, super.key});

  final ServiceClient client;

  @override
  State<TickerView> createState() => _TickerViewState();
}

class _TickerViewState extends State<TickerView> {
  late Future<FixtureTicker> _future = widget.client.ticker();

  @override
  Widget build(BuildContext context) => FutureBuilder<FixtureTicker>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SelectableText(
                friendlyError(snapshot.error),
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () =>
                    setState(() => _future = widget.client.ticker()),
                child: const Text('Try again'),
              ),
            ],
          ),
        );
      }
      final grid = snapshot.data!;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(14, 10, 14, 4),
            // ⚠️⚠️ **This line promised a tap that did not exist.** It read *"Tap a club to see the run in
            // full"* and nothing happened — the same species as ADR-263's *"screen and version travel with
            // it"*: ⭐ *a UI claim that is wrong is worse than a missing feature, because it sends the
            // reader looking for something.* The tap is built now, and the line says what the grid means
            // instead of advertising it.
            child: Text(
              'Easiest run first. An asterisk means away. Tap any club for its run in full.',
              style: TextStyle(
                color: Colors.white38,
                fontSize: 11.5,
                height: 1.4,
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(14, 0, 14, 6),
            child: _Legend(),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(10, 6, 10, 20),
              // ⭐ One for the header row of gameweek numbers, then a row per club.
              itemCount: grid.rows.length + 1,
              itemBuilder: (_, i) => i == 0
                  ? _HeaderRow(gameweeks: grid.gameweeks)
                  : _ClubRow(
                      row: grid.rows[i - 1],
                      gameweeks: grid.gameweeks,
                      onTap: () => showClubRun(context, grid.rows[i - 1]),
                    ),
            ),
          ),
        ],
      );
    },
  );
}

class _HeaderRow extends StatelessWidget {
  const _HeaderRow({required this.gameweeks});

  final List<int> gameweeks;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4, left: 2, right: 2),
    child: Row(
      children: [
        const SizedBox(width: 52),
        for (final gw in gameweeks)
          Expanded(
            child: Center(
              child: Text(
                'GW$gw',
                style: const TextStyle(color: Colors.white38, fontSize: 10),
              ),
            ),
          ),
        const SizedBox(width: 30),
      ],
    ),
  );
}

class _ClubRow extends StatelessWidget {
  const _ClubRow({
    required this.row,
    required this.gameweeks,
    required this.onTap,
  });

  final TickerRow row;
  final List<int> gameweeks;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 52,
            child: Text(
              row.team,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          for (final gw in gameweeks)
            Expanded(
              child: _Cell(cell: row.cells[gw], club: row.team, gw: gw),
            ),
          SizedBox(
            width: 30,
            child: Text(
              // ⭐ The number the rows are sorted on, shown — ⚠️ *an order with no visible key asks the
              // reader to take the ranking on trust.*
              row.avgDifficulty?.toStringAsFixed(1) ?? '–',
              textAlign: TextAlign.right,
              style: const TextStyle(color: Colors.white38, fontSize: 10.5),
            ),
          ),
        ],
      ),
    ),
  );
}

/// ⭐ **The key to the colours and the asterisk.** ⚠️ A five-band scale with no legend is a scale every
/// reader has to infer, and the asterisk was a mark nobody could look up — *"What does the * mean?"* was
/// the first thing asked about this screen.
class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (final (band, word) in const [
        (1, 'easiest'),
        (2, ''),
        (3, ''),
        (4, ''),
        (5, 'hardest'),
      ]) ...[
        Container(
          width: word.isEmpty ? 14 : 18,
          height: 12,
          margin: const EdgeInsets.only(right: 3),
          decoration: BoxDecoration(
            color: difficultyColour(band),
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        if (word.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Text(
              word,
              style: const TextStyle(color: Colors.white38, fontSize: 9.5),
            ),
          ),
      ],
      const Spacer(),
      const Text(
        'CHE* = away',
        style: TextStyle(color: Colors.white38, fontSize: 9.5),
      ),
    ],
  );
}

/// One club's run, in full — the sheet the header line promises.
Future<void> showClubRun(
  BuildContext context,
  TickerRow row,
) => showModalBottomSheet<void>(
  context: context,
  backgroundColor: const Color(0xFF17131F),
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
  ),
  builder: (sheet) => SafeArea(
    child: Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            row.team,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 2, bottom: 10),
            child: Text(
              row.avgDifficulty == null
                  ? 'No rated fixtures in this window.'
                  : 'Average difficulty ${row.avgDifficulty!.toStringAsFixed(1)} over '
                        '${row.cells.length} gameweeks.',
              style: const TextStyle(color: Colors.white38, fontSize: 11.5),
            ),
          ),
          // ⚠️ Sorted by gameweek NUMBER. The map's keys are ints here, but they arrived as strings —
          // ⭐ *the one place "10" sorting before "6" would put a run in the wrong order* (ADR-219).
          for (final gw in row.cells.keys.toList()..sort())
            _RunRow(gameweek: gw, cell: row.cells[gw]),
        ],
      ),
    ),
  ),
);

class _RunRow extends StatelessWidget {
  const _RunRow({required this.gameweek, required this.cell});

  final int gameweek;
  final TickerCell? cell;

  @override
  Widget build(BuildContext context) {
    final c = cell;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(
            width: 46,
            child: Text(
              'GW$gameweek',
              style: const TextStyle(color: Colors.white38, fontSize: 11.5),
            ),
          ),
          if (c == null)
            const Text(
              // ⭐ Said in words here, where there is room for them.
              'Blank — they do not play',
              style: TextStyle(color: Colors.white38, fontSize: 12.5),
            )
          else ...[
            Container(
              width: 10,
              height: 10,
              margin: const EdgeInsets.only(right: 8),
              decoration: BoxDecoration(
                color: difficultyColour(c.difficulty),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Expanded(
              child: Text(
                c.label,
                style: const TextStyle(color: Colors.white, fontSize: 12.5),
              ),
            ),
            Text(
              c.isDouble ? 'double · ${c.difficulty}' : '${c.difficulty}',
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ],
        ],
      ),
    );
  }
}

class _Cell extends StatelessWidget {
  const _Cell({required this.cell, required this.club, required this.gw});

  final TickerCell? cell;
  final String club;
  final int gw;

  @override
  Widget build(BuildContext context) {
    final c = cell;
    // ⭐⭐ **A blank gameweek is drawn, not skipped.** An empty slot is the single most actionable thing
    // this grid says — ⚠️ *a club that does not play cannot be captained*, and a gap that looked like a
    // rendering fault would be read as one.
    if (c == null) {
      return Container(
        height: 26,
        margin: const EdgeInsets.symmetric(horizontal: 1.5),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(4),
        ),
        alignment: Alignment.center,
        child: const Text(
          '–',
          style: TextStyle(color: Colors.white24, fontSize: 11),
        ),
      );
    }
    return Tooltip(
      message: '$club, GW$gw: ${c.label}',
      child: Container(
        height: 26,
        margin: const EdgeInsets.symmetric(horizontal: 1.5),
        decoration: BoxDecoration(
          color: difficultyColour(c.difficulty),
          borderRadius: BorderRadius.circular(4),
        ),
        alignment: Alignment.center,
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3),
            child: Text(
              // ⚠️ A double shows both — the ticker is the view built for spotting them, and showing
              // only the first would hide the half that makes it a double.
              c.isDouble
                  ? c.label
                  : '${c.opponent}${c.venue == "H" ? "" : "*"}',
              style: TextStyle(
                color: difficultyInk(c.difficulty),
                fontSize: 10.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
