/// What r/FantasyPL is talking about (ADR-300, on ADR-059).
///
/// ⭐⭐⭐ **The counting has existed since Sprint 067 and the phone could never ask for it.** It resolves
/// shared `web_name`s properly (ADR-152) — so a bare *"Palmer"* is not credited to two players, and
/// *"James Maddison out for two weeks"* is not credited to Reece James — and it degrades on any
/// 403 / 429 / timeout without raising.
///
/// ⚠️⚠️ **Mentions, not sentiment, and the screen says so.** Twenty-two mentions is twenty-two people
/// typing a name; it is not an opinion about whether to buy him. ⭐ *A screen that blurs those two is
/// inventing analysis it did not do* — and this app's whole claim is that it can explain its numbers.
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api/client.dart';
import 'api/models.dart';
import 'brand.dart';
import 'mugshot.dart';

class ChatterBoard extends StatefulWidget {
  const ChatterBoard({required this.client, required this.team, super.key});

  final ServiceClient client;
  final MyTeam team;

  @override
  State<ChatterBoard> createState() => _ChatterBoardState();
}

class _ChatterBoardState extends State<ChatterBoard> {
  late Future<Chatter> _future = _load();

  Future<Chatter> _load() => widget.client.chatter([
    for (final p in [...widget.team.analysis.xi, ...widget.team.analysis.bench])
      p.id,
  ]);

  @override
  Widget build(BuildContext context) => FutureBuilder<Chatter>(
    future: _future,
    builder: (context, snap) {
      if (snap.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      // ⚠️ A thrown error and a dark Reddit are **different**: the first is ours, the second is theirs
      // and is an ordinary state. ⭐ *A tab that can go dark must have something true to draw when it
      // does*, and it must not look broken while doing it.
      if (snap.hasError) {
        return _Message(
          text: 'Could not reach the service.',
          onRetry: () => setState(() => _future = _load()),
        );
      }
      final chatter = snap.data!;
      if (chatter.rows.isEmpty) {
        return _Message(
          text: chatter.note,
          onRetry: () => setState(() => _future = _load()),
        );
      }
      return ListView(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 20),
        children: [
          // ⭐⭐ **What it measures, once, at the top.** ⚠️ *The reader who does not know this is counting
          // names will read it as a ranking of who is good*, which is the one thing it is not.
          Padding(
            padding: const EdgeInsets.fromLTRB(2, 0, 2, 10),
            child: Text(
              '${chatter.note} Counted by how often a name appears — not by '
              'whether anyone rates him.',
              style: const TextStyle(
                color: Colors.white38,
                fontSize: 11.5,
                height: 1.4,
              ),
            ),
          ),
          for (final row in chatter.rows) _Row(row: row),
        ],
      );
    },
  );
}

class _Row extends StatelessWidget {
  const _Row({required this.row});

  final ChatterRow row;

  @override
  Widget build(BuildContext context) {
    final p = row.player;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.fromLTRB(10, 9, 12, 10),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusMd),
        // ⭐ Your own players outlined rather than reordered — *a list that quietly floats your squad to
        // the top is no longer telling you what the crowd is talking about.*
        border: row.owned
            ? Border.all(color: Brand.purple.withValues(alpha: 0.8))
            : null,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ⚠️ **The initials fallback is hit more here than anywhere else, and that is not a bug.**
          // The Premier League CDN 403s for players it has no photo of — new signings, mostly — and
          // *those are exactly the players a subreddit is suddenly talking about.* Measured: Brobbey,
          // Barry and Tzolakis all 403; Haaland, Palmer and Isak all 200.
          Mugshot(url: row.photo, name: p.name, size: 34),
          const SizedBox(width: 10),
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
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    if (row.owned)
                      const Padding(
                        padding: EdgeInsets.only(left: 6),
                        child: Text(
                          'yours',
                          style: TextStyle(
                            color: Brand.purple,
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                  ],
                ),
                Text(
                  '${p.position} · ${p.team} · £${p.price.toStringAsFixed(1)}m',
                  style: const TextStyle(color: Colors.white38, fontSize: 11.5),
                ),
                // ⭐⭐ **The threads behind the number.** ⚠️ *A count with nothing behind it is a claim you
                // cannot check* — and checking it is one tap, on the post that produced it.
                for (final post in row.posts)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: GestureDetector(
                      onTap: () => launchUrl(
                        Uri.parse(post.link),
                        mode: LaunchMode.externalApplication,
                      ),
                      behavior: HitTestBehavior.opaque,
                      child: Text(
                        post.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white60,
                          fontSize: 11.5,
                          height: 1.35,
                          decoration: TextDecoration.underline,
                          decorationColor: Colors.white24,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            children: [
              Text(
                '${row.mentions}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Text(
                'mentions',
                style: TextStyle(color: Colors.white38, fontSize: 9.5),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Nothing to show, and why — ⭐ *with a way out of it.*
class _Message extends StatelessWidget {
  const _Message({required this.text, required this.onRetry});

  final String text;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white38, height: 1.5),
          ),
          const SizedBox(height: 14),
          // ⚠️ Reddit rate-limits, so *"try again"* is genuinely the right advice here rather than a
          // shrug — ⭐ a minute later it usually works.
          TextButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    ),
  );
}
