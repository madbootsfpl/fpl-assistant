/// MADBOOTS — My Team, as a pitch (ADR-222).
///
/// ⭐ **Still one screen and no state management.** Riverpod and Drift are on the audit's Phase 4 list;
/// adding them before a screen asks for anything is a foundation built to a guess. `http` remains the only
/// dependency.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'pitch.dart';

/// ⚠️ **Reaches the dev server from macOS desktop, the iOS simulator and Chrome** — all three share the
/// host's network. A **physical device** cannot, and that is the point at which the API needs hosting.
const String kBaseUrl = 'http://localhost:8078';

/// The owner's own team, so the app opens on something real rather than a stranger's squad.
const int kDefaultManagerId = 2885974;

void main() => runApp(const MadbootsApp());

class MadbootsApp extends StatelessWidget {
  const MadbootsApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: Brand.name,
        debugShowCheckedModeBanner: false,
        // ⭐ Seeded from the brand's own purple, generated from `brand.py` — the web app's single source of
        // truth (ADR-103/114). A hex typed here would be a second definition of the brand.
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Brand.purple),
          scaffoldBackgroundColor: Brand.ink,
          useMaterial3: true,
        ),
        home: const MyTeamScreen(),
      );
}

class MyTeamScreen extends StatefulWidget {
  const MyTeamScreen({super.key});

  @override
  State<MyTeamScreen> createState() => _MyTeamScreenState();
}

class _MyTeamScreenState extends State<MyTeamScreen> {
  final ServiceClient _client = ServiceClient(baseUrl: kBaseUrl);
  late final TextEditingController _id =
      TextEditingController(text: '$kDefaultManagerId');
  late Future<MyTeam> _team = _load(kDefaultManagerId);

  /// ⭐ The health check first, because *"the service is not running"* and *"that team is not public yet"*
  /// are different problems, and only one of them is the manager's to fix.
  Future<MyTeam> _load(int managerId) async {
    if (!await _client.healthy()) {
      throw StateError(
        'The service is not answering on $kBaseUrl.\n\n'
        'Start it with:\n'
        '  venv/bin/python -m uvicorn src.service.http:app --port 8078',
      );
    }
    return _client.myTeam(managerId, horizon: 1);
  }

  void _reload() {
    final id = int.tryParse(_id.text.trim());
    if (id == null || id < 1) return;
    setState(() => _team = _load(id));
  }

  @override
  void dispose() {
    _client.close();
    _id.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              _TitleBar(controller: _id, onSubmit: _reload),
              Expanded(
                child: FutureBuilder<MyTeam>(
                  future: _team,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError) {
                      // ⚠️ Shown, not swallowed. An app that renders an empty pitch on failure looks like a
                      // squad with no players — and the message is usually the whole diagnosis.
                      return Padding(
                        padding: const EdgeInsets.all(22),
                        child: Center(
                          child: SelectableText(_reason(snapshot.error),
                              style: const TextStyle(color: Colors.white70, height: 1.55)),
                        ),
                      );
                    }
                    return SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(8, 0, 8, 16),
                      child: PitchView(team: snapshot.data!),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      );

  static String _reason(Object? error) =>
      error is ApiException ? error.detail : '$error';
}

class _TitleBar extends StatelessWidget {
  const _TitleBar({required this.controller, required this.onSubmit});

  final TextEditingController controller;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
        child: Row(
          children: [
            const Text.rich(
              TextSpan(children: [
                TextSpan(
                    text: 'MAD',
                    style: TextStyle(color: Brand.purpleLight, fontWeight: FontWeight.w700)),
                TextSpan(text: 'BOOTS', style: TextStyle(color: Colors.white)),
              ]),
              style: TextStyle(fontSize: 15, letterSpacing: .5),
            ),
            const Spacer(),
            SizedBox(
              width: 108,
              height: 30,
              child: TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.end,
                onSubmitted: (_) => onSubmit(),
                style: const TextStyle(color: Colors.white, fontSize: 12.5),
                decoration: InputDecoration(
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  hintText: 'manager id',
                  hintStyle: const TextStyle(color: Colors.white38, fontSize: 12),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 6),
            IconButton(
              onPressed: onSubmit,
              icon: const Icon(Icons.refresh, size: 18, color: Colors.white70),
              tooltip: 'Load this team',
            ),
          ],
        ),
      );
}
