/// Spike 018 — does the mobile audit's §4.1 read path actually work?
///
/// One screen, no auth, no API: read the published xP board straight from Supabase over PostgREST and
/// render it. The question is not "does this look nice" — it is whether the architecture everything
/// downstream assumes actually holds.
///
/// Run it with your own key, which this file never contains:
///
///   flutter run -d chrome \
///     --dart-define=SUPA_URL=https://YOUR-REF.supabase.co \
///     --dart-define=SUPA_KEY=your-publishable-key
library;

import 'package:flutter/material.dart';

import 'board.dart';

const _url = String.fromEnvironment('SUPA_URL');
const _key = String.fromEnvironment('SUPA_KEY');

void main() => runApp(const SliceApp());

class SliceApp extends StatelessWidget {
  const SliceApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'MADBOOTS — read slice',
        theme: ThemeData.dark(useMaterial3: true),
        home: const BoardScreen(),
      );
}

class BoardScreen extends StatefulWidget {
  const BoardScreen({super.key});

  @override
  State<BoardScreen> createState() => _BoardScreenState();
}

class _BoardScreenState extends State<BoardScreen> {
  late Future<List<BoardRow>> _rows;
  int _horizon = 5;
  Duration? _took;
  int? _bytes;

  @override
  void initState() {
    super.initState();
    _rows = _load();
  }

  Future<List<BoardRow>> _load() async {
    if (_url.isEmpty || _key.isEmpty) {
      throw Exception(
        'Pass --dart-define=SUPA_URL=... and --dart-define=SUPA_KEY=... — the key is never in the source.',
      );
    }
    final client = BoardClient(projectUrl: _url, publishableKey: _key);
    final started = DateTime.now();
    final rows = await client.fetchBoard();
    // ⭐ The two numbers this slice exists to produce, shown on screen rather than in a log.
    setState(() {
      _took = DateTime.now().difference(started);
      _bytes = client.lastBytes;
    });
    return rows;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('xP board'),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(46),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Horizon '),
                for (final h in [1, 3, 5, 8])
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: ChoiceChip(
                      label: Text('$h'),
                      selected: _horizon == h,
                      onSelected: (_) => setState(() => _horizon = h),
                    ),
                  ),
              ],
            ),
          ),
        ),
        body: FutureBuilder<List<BoardRow>>(
          future: _rows,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return Padding(
                padding: const EdgeInsets.all(24),
                child: Text('🔴 ${snap.error}', style: const TextStyle(color: Colors.redAccent)),
              );
            }
            final rows = [...snap.data!]
              ..sort((a, b) => b.xpOver(_horizon).compareTo(a.xpOver(_horizon)));
            return Column(
              children: [
                // ⚠️ The measurement, not decoration: payload and wall-clock are the things §4.1 is being
                // judged on. A slice that renders beautifully and cannot say what it cost has not answered.
                Builder(builder: (_) {
                  // ⭐ Name the players whose totals sit exactly on a half-tenth. Those are the only rows
                  // where Dart and Python can disagree, so those are the rows worth comparing against the
                  // web app — instead of picking a few at random and learning nothing.
                  final risky = rows.where((r) => r.atRoundingBoundary(_horizon)).toList();
                  return Container(
                    width: double.infinity,
                    color: Colors.white10,
                    padding: const EdgeInsets.all(10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${rows.length} players · '
                          '${_bytes != null ? "${(_bytes! / 1024).round()} KB" : "?"} '
                          '· fetched in ${_took?.inMilliseconds ?? "?"} ms',
                          style: const TextStyle(fontFamily: 'monospace'),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          risky.isEmpty
                              ? 'no rounding-boundary players at this horizon'
                              : 'compare these against the web app — '
                                  '${risky.map((r) => "${r.name} ${r.display(_horizon)}").join(" · ")}',
                          style: TextStyle(
                            fontFamily: 'monospace',
                            color: risky.isEmpty ? Colors.white38 : Colors.amberAccent,
                          ),
                        ),
                      ],
                    ),
                  );
                }),
                Expanded(
                  child: ListView.builder(
                    itemCount: rows.length,
                    itemBuilder: (context, i) {
                      final r = rows[i];
                      return ListTile(
                        dense: true,
                        leading: SizedBox(width: 34, child: Text('${i + 1}')),
                        title: Text('${r.name}  ·  ${r.team}  ${r.position}'),
                        trailing: Text(
                          r.display(_horizon),
                          style: const TextStyle(fontFamily: 'monospace'),
                        ),
                      );
                    },
                  ),
                ),
              ],
            );
          },
        ),
      );
}
