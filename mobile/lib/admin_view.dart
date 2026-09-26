/// The owner's usage stats, buried in Settings (ADR-305).
///
/// ⭐⭐⭐ **The client holds no credential.** Reading the `events` table needs `FPL_ADMIN_STORE_KEY` — a
/// service-role key that bypasses RLS — and ⚠️ *the web build is public JavaScript*, so a key shipped
/// here is a key published. The owner types a password, it travels per request, and the server does the
/// reading.
///
/// ⚠️⚠️ **Wide screens only, and that is convenience rather than security.** A phone is the wrong shape
/// for a table of medians, and the owner asked for it on the desktop. ⭐ *The lock is the key check on
/// the server; hiding the door is only tidiness*, and pretending otherwise would be the kind of
/// reasoning that puts a secret in a binary.
library;

import 'package:flutter/material.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';

/// The width at which a stats table is worth showing — the same threshold the pitch uses for a tablet.
const double kAdminMinWidth = 600;

class AdminView extends StatefulWidget {
  const AdminView({
    required this.client,
    required this.onKey,
    this.savedKey,
    super.key,
  });

  final ServiceClient client;

  /// ⭐ Persisted by the caller, so a reload does not ask again. ⚠️ On the device only — it is a
  /// password, and *the server never stores one on a client's behalf.*
  final ValueChanged<String> onKey;
  final String? savedKey;

  @override
  State<AdminView> createState() => _AdminViewState();
}

class _AdminViewState extends State<AdminView> {
  late final TextEditingController _key = TextEditingController(
    text: widget.savedKey ?? '',
  );
  Future<AdminUsage>? _usage;
  int _days = 7;

  @override
  void dispose() {
    _key.dispose();
    super.dispose();
  }

  void _load() {
    final key = _key.text.trim();
    if (key.isEmpty) return;
    widget.onKey(key);
    final pending = widget.client.adminUsage(key, days: _days);
    // ⚠️ The same fast-failure guard as Ask: `FutureBuilder` subscribes a frame late, and a 401 arrives
    // immediately — ⭐ *a rejection nobody was listening to is an unhandled error, and the app dies while
    // the screen renders the message correctly.*
    pending.then((_) {}, onError: (Object _, StackTrace _) {});
    setState(() {
      _usage = pending;
    });
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
    children: [
      const Text(
        'Counts, medians and a slow tail across every surface. No manager ids, '
        'no names — the pipeline was built not to store them.',
        style: TextStyle(color: Colors.white38, fontSize: 12, height: 1.5),
      ),
      const SizedBox(height: 14),
      Row(
        children: [
          Expanded(
            child: TextField(
              controller: _key,
              obscureText: true,
              onSubmitted: (_) => _load(),
              style: const TextStyle(color: Colors.white, fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Admin key',
                hintStyle: const TextStyle(color: Colors.white38),
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
          const SizedBox(width: 8),
          for (final days in const [1, 7, 30])
            Padding(
              padding: const EdgeInsets.only(left: 4),
              child: GestureDetector(
                onTap: () {
                  setState(() => _days = days);
                  _load();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: _days == days ? Brand.purple : Colors.white10,
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                  ),
                  child: Text(
                    '${days}d',
                    style: TextStyle(
                      color: _days == days ? Colors.white : Colors.white54,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      const SizedBox(height: 16),
      if (_usage == null)
        const Text(
          'Enter the key to load.',
          style: TextStyle(color: Colors.white38, fontSize: 12.5),
        )
      else
        FutureBuilder<AdminUsage>(
          future: _usage,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snap.hasError) {
              // ⭐ Shown as-is: a 401 and a 404 are both *"that did not work"*, and the endpoint is
              // deliberately silent about which.
              return Text(
                '${snap.error}',
                style: const TextStyle(
                  color: Brand.warn,
                  fontSize: 12.5,
                  height: 1.5,
                ),
              );
            }
            return _Stats(usage: snap.data!);
          },
        ),
    ],
  );
}

class _Stats extends StatelessWidget {
  const _Stats({required this.usage});

  final AdminUsage usage;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      // ⚠️ A store that could not be read says so, and still draws its (empty) shape — ⭐ *a stats page
      // that errors is indistinguishable from a product that is broken*, and it is read at exactly the
      // moment somebody is checking whether the product is broken.
      if (!usage.ok)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text(
            usage.reason,
            style: const TextStyle(color: Brand.warn, fontSize: 12.5),
          ),
        ),
      Wrap(
        spacing: 22,
        runSpacing: 14,
        children: [
          _Figure(label: 'Requests', value: '${usage.events}'),
          // ⚠️ **Installs, not people.** An install id is tied to nothing.
          _Figure(label: 'Installs', value: '${usage.installs}'),
          _Figure(label: 'Failed', value: '${usage.failures}'),
          _Figure(
            label: 'Median',
            value: usage.medianMs == null ? '—' : '${usage.medianMs}ms',
          ),
          // ⭐ The slow tail, because *a median hides the request that made someone give up.*
          _Figure(
            label: 'P95',
            value: usage.p95Ms == null ? '—' : '${usage.p95Ms}ms',
          ),
          _Figure(
            label: 'Slowest',
            value: usage.slowestMs == null ? '—' : '${usage.slowestMs}ms',
          ),
        ],
      ),
      const SizedBox(height: 18),
      _Breakdown(title: 'Platforms', counts: usage.platforms),
      _Breakdown(title: 'Versions', counts: usage.versions),
      _Breakdown(title: 'Most used', counts: usage.pages),
    ],
  );
}

class _Figure extends StatelessWidget {
  const _Figure({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    mainAxisSize: MainAxisSize.min,
    children: [
      Text(
        value,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 19,
          fontWeight: FontWeight.w700,
        ),
      ),
      Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
    ],
  );
}

class _Breakdown extends StatelessWidget {
  const _Breakdown({required this.title, required this.counts});

  final String title;
  final Map<String, int> counts;

  @override
  Widget build(BuildContext context) {
    if (counts.isEmpty) return const SizedBox.shrink();
    final total = counts.values.fold<int>(0, (a, b) => a + b);
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            title.toUpperCase(),
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 9.5,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 6),
          for (final entry in counts.entries)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      entry.key,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12.5,
                      ),
                    ),
                  ),
                  // ⭐ A share, because *a count with no denominator is a number you cannot act on.*
                  Text(
                    '${entry.value}  ·  ${total == 0 ? 0 : (entry.value * 100 / total).round()}%',
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
