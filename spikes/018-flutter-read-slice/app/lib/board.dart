/// Reading the published xP board from Supabase, the way the mobile audit §4.1 assumes.
///
/// ⭐⭐ No auth, no API, no state management. This exists to answer one question — does the read path
/// work from a Flutter client — and a slice that grows a framework stops being a slice.
library;

import 'dart:convert';
import 'package:http/http.dart' as http;

/// One row of the published board.
class BoardRow {
  BoardRow({
    required this.name,
    required this.team,
    required this.position,
    required this.byGameweek,
  });

  final String name;
  final String team;
  final String position;

  /// ⚠️ **Unrounded, deliberately.** ADR-213 publishes full precision so a prefix sums to exactly what the
  /// engine produces at that horizon. Rounding these before summing drifts — measured at up to 0.2 points
  /// across 253 of 662 players — and a phone showing a different number from the web is the
  /// two-implementations failure this codebase has three ADRs about.
  final Map<int, double> byGameweek;

  /// Expected points over the next [horizon] gameweeks, **unrounded**.
  ///
  /// ⭐ Sum first. Round only at the point of display, and see the warning below before deciding how.
  double xpOver(int horizon) {
    final weeks = byGameweek.keys.toList()..sort();
    return weeks.take(horizon).fold<double>(0, (sum, gw) => sum + byGameweek[gw]!);
  }

  /// One-decimal display value.
  ///
  /// ⚠️⚠️ **This will disagree with the web app on about 0.09% of values, and no rounding mode fixes it.**
  /// Measured on the real board: 5 of 5,272 horizon sums land exactly on a half-tenth, and Python's answer
  /// on those is neither banker's nor half-up — `0.55 → 0.6`, `1.95 → 1.9`, `5.85 → 5.8`, whichever binary
  /// float is nearest. Dart's `toStringAsFixed` is half-up and cannot reproduce that.
  ///
  /// ⭐ Left as-is on purpose. The slice exists to **measure** the divergence against the live web app; if
  /// it is the predicted handful, the fix is for the server to publish the rounded totals so the client
  /// reads rather than computes. Designing that before a client exists is the guess this project keeps
  /// making.
  String display(int horizon) => xpOver(horizon).toStringAsFixed(1);

  static BoardRow fromJson(Map<String, dynamic> json) {
    // PostgREST hands `by_gameweek` back as a JSON string, keyed by gameweek as text.
    final raw = json['by_gameweek'];
    final decoded = raw is String ? jsonDecode(raw) : raw;
    final byGw = <int, double>{};
    (decoded as Map<String, dynamic>).forEach((gw, value) {
      byGw[int.parse(gw)] = (value as num).toDouble();
    });
    return BoardRow(
      name: json['web_name'] as String? ?? '?',
      team: json['team'] as String? ?? '',
      position: json['position'] as String? ?? '',
      byGameweek: byGw,
    );
  }
}

/// The published board, straight from PostgREST.
///
/// ⚠️ The publishable key is compiled into the binary and can be extracted — which is expected, and safe
/// **only** because these tables are `SELECT`-only for `anon` (ADR-216) and hold public football data. The
/// moment this client reads anything a person typed, it needs Stage C.
class BoardClient {
  BoardClient({required this.projectUrl, required this.publishableKey});

  final String projectUrl;
  final String publishableKey;

  Future<List<BoardRow>> fetchBoard() async {
    final uri = Uri.parse(
      '$projectUrl/rest/v1/xp_board'
      '?select=web_name,team,position,by_gameweek',
    );
    final response = await http.get(uri, headers: {
      'apikey': publishableKey,
      'Accept': 'application/json',
    });
    if (response.statusCode != 200) {
      throw Exception('board read failed: ${response.statusCode} ${response.body}');
    }
    final rows = jsonDecode(response.body) as List<dynamic>;
    return rows
        .map((r) => BoardRow.fromJson(r as Map<String, dynamic>))
        .toList();
  }
}
