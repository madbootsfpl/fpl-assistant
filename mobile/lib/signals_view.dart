/// Signals — what should I know, about my fifteen (ADR-232).
///
/// ⭐⭐ **The ordering is the design** (ADR-150). These sources are not equally reliable, and rendering them
/// as one undifferentiated list would present a Reddit rumour beside an injury FPL confirmed. So they
/// descend by evidentiary strength and **each says what it is**.
///
/// ⭐ **And the phone can do something the web cannot: remember what you had already seen.** The server has
/// no idea when you last looked — but every signal carries a stable key, so the device does. That is the
/// *what-changed* view the start checklist asked for, and it needed no new data at all.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

/// How much the source behind a signal actually knows.
enum SignalKind { official, departure, exodus, headline, unknown }

SignalKind _kindOf(String raw) => switch (raw) {
      'official' => SignalKind.official,
      'departure' => SignalKind.departure,
      'exodus' => SignalKind.exodus,
      'headline' => SignalKind.headline,
      _ => SignalKind.unknown,
    };

extension on SignalKind {
  /// ⚠️ The label says **what kind of claim it is**, not how alarming it is. *"Unexplained"* is a statement
  /// about our own data, which is the honest thing an inference can say about itself.
  String get label => switch (this) {
        SignalKind.official => 'FPL',
        SignalKind.departure => 'Reported move',
        SignalKind.exodus => 'Unexplained',
        SignalKind.headline => 'Headline',
        SignalKind.unknown => 'Signal',
      };

  Color get colour => switch (this) {
        SignalKind.official => Brand.bad,
        SignalKind.departure => Brand.bad,
        SignalKind.exodus => Brand.warn,
        SignalKind.headline => Brand.purpleLight,
        SignalKind.unknown => Brand.muted,
      };
}

/// Remembers which signals have already been shown. ⭐ One key, like the draft store — the app needs a
/// memory, not a database.
class _SeenStore {
  static const String _key = 'madboots.signals.seen.v1';

  Future<Set<String>> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return {};
    try {
      return (jsonDecode(raw) as List).cast<String>().toSet();
    } catch (_) {
      return {};
    }
  }

  Future<void> save(Set<String> keys) async {
    final prefs = await SharedPreferences.getInstance();
    // ⚠️ Replaced, not merged: a key that no longer comes back is a signal that has passed, and keeping it
    // forever would grow a list nobody reads until it slowed the thing it was meant to speed up.
    await prefs.setString(_key, jsonEncode(keys.toList()));
  }
}

class SignalsView extends StatefulWidget {
  const SignalsView({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<SignalsView> createState() => _SignalsViewState();
}

class _SignalsViewState extends State<SignalsView> {
  final _SeenStore _store = _SeenStore();
  late final Future<(List<Map<String, dynamic>>, int, Set<String>)> _load = _fetch();

  Future<(List<Map<String, dynamic>>, int, Set<String>)> _fetch() async {
    final seen = await _store.load();
    final body = await widget.client.signals([
      ...widget.team.analysis.xi.map((p) => p.id),
      ...widget.team.analysis.bench.map((p) => p.id),
    ]);
    final signals = ((body['signals'] as List?) ?? const [])
        .cast<Map<String, dynamic>>();

    // ⭐ Marked seen on *this* render, so the badge survives exactly one visit — which is what "new since
    // you last looked" means. Saving before rendering would make it never show.
    await _store.save(signals.map((s) => '${s['key']}').toSet());
    return (signals, body['checked'] as int? ?? 0, seen);
  }

  @override
  Widget build(BuildContext context) =>
      FutureBuilder<(List<Map<String, dynamic>>, int, Set<String>)>(
        future: _load,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Center(
                child: SelectableText('${snapshot.error}',
                    style: const TextStyle(color: Colors.white70, height: 1.55)),
              ),
            );
          }
          final (signals, checked, seen) = snapshot.data!;
          final fresh = signals.where((s) => !seen.contains('${s['key']}')).length;

          if (signals.isEmpty) {
            // ⭐ A quiet week is news. An empty screen reads as a failure to load.
            return _Empty(checked: checked);
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 22),
            children: [
              Text(
                fresh == 0
                    ? '${signals.length} across your $checked players — nothing new since you last looked.'
                    : '$fresh new · ${signals.length} across your $checked players',
                style: const TextStyle(color: Colors.white54, fontSize: 12, height: 1.45),
              ),
              const SizedBox(height: 12),
              for (final signal in signals)
                _Signal(
                  data: signal,
                  isNew: !seen.contains('${signal['key']}'),
                ),
              const SizedBox(height: 12),
              const Text(
                'Ordered by how much the source actually knows: FPL first, then a reported move, then a '
                'sell-off nothing in the data explains, then headlines.',
                style: TextStyle(color: Colors.white24, fontSize: 10.5, height: 1.5),
              ),
            ],
          );
        },
      );
}

class _Signal extends StatelessWidget {
  const _Signal({required this.data, required this.isNew});

  final Map<String, dynamic> data;
  final bool isNew;

  @override
  Widget build(BuildContext context) {
    final kind = _kindOf('${data['kind']}');
    final player = PlayerSummary.fromJson(data['player'] as Map<String, dynamic>);

    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 11),
      decoration: BoxDecoration(
        color: Colors.white10,
        border: Border(left: BorderSide(color: kind.colour, width: 3)),
        borderRadius: BorderRadius.circular(Brand.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(player.name,
                  style: const TextStyle(
                      color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(width: 6),
              Text('${player.team} · ${player.position}',
                  style: const TextStyle(color: Colors.white38, fontSize: 11)),
              const Spacer(),
              if (isNew)
                Container(
                  margin: const EdgeInsets.only(right: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                  decoration: BoxDecoration(
                    color: Brand.accentTeal,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: const Text('new',
                      style: TextStyle(
                          color: Brand.ink, fontSize: 9, fontWeight: FontWeight.w700)),
                ),
              Text(kind.label,
                  style: TextStyle(color: kind.colour, fontSize: 10, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 5),
          Text('${data['headline']}',
              style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.45)),
          const SizedBox(height: 3),
          Text('${data['detail']}',
              style: const TextStyle(color: Colors.white38, fontSize: 11, height: 1.45)),
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({required this.checked});

  final int checked;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(30),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle_outline, size: 30, color: Colors.white24),
              const SizedBox(height: 10),
              Text('Nothing to report across your $checked players.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white54, fontSize: 13.5)),
              const SizedBox(height: 6),
              const Text(
                'No FPL news, no reported moves, no sell-off the data cannot explain.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white24, fontSize: 11.5, height: 1.5),
              ),
            ],
          ),
        ),
      );
}
