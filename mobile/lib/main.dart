/// MADBOOTS — the first slice: prove the app can ask the engine a question and render the answer.
///
/// ⭐ **Deliberately one screen and no state management.** The audit's Phase 4 lists Riverpod, Drift,
/// navigation and a theme; adding them before a screen asks for anything is a foundation built to a guess.
/// This renders a real squad analysis from the real service, and everything else earns its place after.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

/// ⚠️ **Reaches the dev server from macOS desktop, the iOS simulator and Chrome** — all three share the
/// host's network. A **physical device** cannot, and that is the point at which the API needs hosting.
const String kBaseUrl = 'http://localhost:8078';

/// ⚠️ **A placeholder until there is a squad picker.** The same fifteen the committed API samples use, so
/// what this screen shows can be checked against `api-samples/analysis.json` by eye.
const List<int> kSampleSquad = [1, 8, 12, 40, 68, 94, 115, 124, 165, 229, 330, 379, 391, 411, 572];

void main() => runApp(const MadbootsApp());

class MadbootsApp extends StatelessWidget {
  const MadbootsApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: Brand.name,
        debugShowCheckedModeBanner: false,
        // ⭐ Seeded from the brand's own purple, which is generated from `brand.py` — the web app's single
        // source of truth (ADR-103/114). A hex typed here would be a second definition of the brand.
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Brand.purple),
          scaffoldBackgroundColor: Brand.surface,
          useMaterial3: true,
        ),
        home: const SquadScreen(),
      );
}

class SquadScreen extends StatefulWidget {
  const SquadScreen({super.key});

  @override
  State<SquadScreen> createState() => _SquadScreenState();
}

class _SquadScreenState extends State<SquadScreen> {
  final ServiceClient _client = ServiceClient(baseUrl: kBaseUrl);
  late Future<SquadAnalysis> _analysis;

  @override
  void initState() {
    super.initState();
    _analysis = _load();
  }

  /// ⭐ The health check first, because *"the service is not running"* and *"the request was refused"* are
  /// different problems and only one of them is worth reading a stack trace over.
  Future<SquadAnalysis> _load() async {
    if (!await _client.healthy()) {
      throw StateError(
        'The service is not answering on $kBaseUrl.\n\n'
        'Start it with:\n'
        '  venv/bin/python -m uvicorn src.service.http:app --port 8078',
      );
    }
    return _client.analysis(kSampleSquad, horizon: 5);
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text(Brand.name),
          backgroundColor: Brand.ink,
          foregroundColor: Brand.surface,
        ),
        body: FutureBuilder<SquadAnalysis>(
          future: _analysis,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              // ⚠️ The error is shown, not swallowed into an empty list. An app that renders nothing when a
              // call fails looks like a squad with no players.
              return Padding(
                padding: const EdgeInsets.all(24),
                child: Center(
                  child: SelectableText(
                    '${snapshot.error}',
                    style: const TextStyle(fontFamily: 'monospace', height: 1.5),
                  ),
                ),
              );
            }
            return _Analysis(analysis: snapshot.data!);
          },
        ),
      );
}

class _Analysis extends StatelessWidget {
  const _Analysis({required this.analysis});

  final SquadAnalysis analysis;

  @override
  Widget build(BuildContext context) {
    final weeks = analysis.gameweeks;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          'GW${weeks.first}–${weeks.last} · ${analysis.projectedXp.toStringAsFixed(1)} xP',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        Text(
          'bench ${analysis.benchXp.toStringAsFixed(1)} · squad value £${analysis.value.toStringAsFixed(1)}m',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Brand.muted),
        ),
        if (analysis.topPick != null) ...[
          const SizedBox(height: 16),
          Text('Captain: ${analysis.topPick!.name} · ${analysis.topPick!.xp.toStringAsFixed(1)} xP',
              style: Theme.of(context).textTheme.titleMedium),
        ],
        if (analysis.issues.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Worth a look', style: Theme.of(context).textTheme.titleMedium),
          for (final p in analysis.issues)
            Text('  ${p.name} — ${_why(p)}',
                style: const TextStyle(color: Brand.warnFg)),
        ],
        const SizedBox(height: 24),
        Text('Starting XI', style: Theme.of(context).textTheme.titleMedium),
        for (final p in analysis.xi) _PlayerRow(player: p),
        const SizedBox(height: 16),
        Text('Bench', style: Theme.of(context).textTheme.titleMedium),
        for (final p in analysis.bench) _PlayerRow(player: p),
        const SizedBox(height: 24),
        Text(Brand.mantra,
            style: TextStyle(color: Brand.muted, fontSize: 12, fontStyle: FontStyle.italic)),
      ],
    );
  }

  /// ⭐ **Availability is three separate facts and none implies the others.** A reported departure is not a
  /// status — FPL still calls an agreed transfer `a` (ADR-155) — and a doubt is a probability, not a
  /// verdict (ADR-206), so the percentage is shown rather than collapsed into "doubtful".
  static String _why(PlayerSummary p) {
    if (p.isLeaving) return 'reported to be leaving';
    if (p.isDoubtful) return p.chance == null ? 'doubtful' : '${p.chance}% chance of playing';
    if (p.isUnavailable) return 'unavailable';
    return 'flagged';
  }
}

class _PlayerRow extends StatelessWidget {
  const _PlayerRow({required this.player});

  final PlayerSummary player;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          children: [
            SizedBox(width: 44, child: Text(player.position,
                style: const TextStyle(color: Brand.muted, fontSize: 12))),
            Expanded(child: Text(player.name)),
            SizedBox(width: 52, child: Text(player.team,
                style: const TextStyle(color: Brand.muted, fontSize: 12))),
            SizedBox(
              width: 56,
              child: Text(player.xp.toStringAsFixed(1), textAlign: TextAlign.right),
            ),
          ],
        ),
      );
}
