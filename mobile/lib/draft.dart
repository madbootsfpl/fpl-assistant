/// A draft squad that survives closing the app (ADR-225).
///
/// ⭐⭐ **Stored as what you changed, not as what you ended up with.** A saved list of fifteen players
/// cannot tell you whether it is still relevant; a draft that also records **the squad it was made
/// against** can be checked against reality the moment the app reopens.
///
/// ⚠️⚠️ **This is the failure the design exists to prevent.** You plan a transfer on Friday, actually make
/// it in the FPL app on Saturday, and reopen this on Sunday. A snapshot would show your Friday plan as
/// though it were your team — ⭐ *lying about something you can act on* — while a diff notices that the
/// base has moved and says so.
library;

import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Why a saved draft was not restored. ⭐ Each case is a different sentence to the user, because *"your
/// plan is gone"* and *"your plan already happened"* mean opposite things.
enum DraftStaleness {
  /// It still applies — same manager, same gameweek, same starting squad.
  fresh,

  /// A different manager id is loaded.
  otherManager,

  /// The gameweek moved on. A plan for GW6 is meaningless in GW7.
  gameweekPassed,

  /// ⭐ The real squad changed underneath it — usually because the manager **made the move for real**.
  squadChanged,
}

class Draft {
  const Draft({
    required this.managerId,
    required this.gameweek,
    required this.basePlayerIds,
    required this.playerIds,
    required this.benchIds,
    required this.savedAt,
  });

  factory Draft.fromJson(Map<String, dynamic> json) => Draft(
        managerId: json['manager_id'] as int,
        gameweek: json['gameweek'] as int,
        basePlayerIds: (json['base_player_ids'] as List).cast<int>(),
        playerIds: (json['player_ids'] as List).cast<int>(),
        benchIds: (json['bench_ids'] as List).cast<int>(),
        savedAt: DateTime.parse(json['saved_at'] as String),
      );

  final int managerId;

  /// ⚠️ The gameweek it was drafted for. A plan outlives its week only in the sense that the file does.
  final int gameweek;

  /// ⭐ **The squad it was drafted FROM.** Without this the draft cannot know it is stale — this single
  /// field is the difference between a plan and a lie.
  final List<int> basePlayerIds;

  final List<int> playerIds;
  final List<int> benchIds;
  final DateTime savedAt;

  Map<String, dynamic> toJson() => {
        'manager_id': managerId,
        'gameweek': gameweek,
        'base_player_ids': basePlayerIds,
        'player_ids': playerIds,
        'bench_ids': benchIds,
        'saved_at': savedAt.toIso8601String(),
      };

  /// The swaps this draft represents, as `(out, in)` ids.
  ///
  /// ⭐ Derived rather than stored: two lists and a subtraction cannot disagree with each other, where a
  /// stored list of swaps could drift from the squad it claims to describe.
  List<(int, int)> get swaps {
    final gone = basePlayerIds.where((id) => !playerIds.contains(id)).toList();
    final added = playerIds.where((id) => !basePlayerIds.contains(id)).toList();
    return [
      for (var i = 0; i < gone.length && i < added.length; i++) (gone[i], added[i]),
    ];
  }

  bool get isEmpty => swaps.isEmpty;

  /// Whether this draft still describes something the manager can act on.
  ///
  /// ⚠️ **Compared as sets, not as lists.** FPL returns picks in its own order and that order changes when
  /// a manager reorders the bench — which is not a squad change, and treating it as one would throw away a
  /// perfectly good plan for no reason.
  DraftStaleness checkAgainst({
    required int managerId,
    required int? gameweek,
    required List<int> fplPlayerIds,
  }) {
    if (this.managerId != managerId) return DraftStaleness.otherManager;
    if (gameweek != null && this.gameweek != gameweek) return DraftStaleness.gameweekPassed;
    if (!_sameSet(basePlayerIds, fplPlayerIds)) return DraftStaleness.squadChanged;
    return DraftStaleness.fresh;
  }

  static bool _sameSet(List<int> a, List<int> b) =>
      a.length == b.length && a.toSet().containsAll(b);
}

/// Where a draft lives between sessions.
///
/// ⭐ **One key, one document.** `shared_preferences` writes a string; that is the whole requirement. When
/// the app caches the board for offline use it will want a real database — and that is the moment to add
/// one, not before.
class DraftStore {
  static const String _key = 'madboots.draft.v1';

  Future<Draft?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return null;
    try {
      return Draft.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      // ⚠️ A draft written by an older build must never stop the app opening. ⭐ *A cache that can wedge
      // the product it accelerates is worse than no cache* — so an unreadable one is simply discarded.
      await prefs.remove(_key);
      return null;
    }
  }

  Future<void> save(Draft draft) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(draft.toJson()));
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
