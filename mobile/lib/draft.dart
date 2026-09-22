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
    this.captainId,
    this.viceCaptainId,
  });

  factory Draft.fromJson(Map<String, dynamic> json) => Draft(
    managerId: json['manager_id'] as int,
    gameweek: json['gameweek'] as int,
    basePlayerIds: (json['base_player_ids'] as List).cast<int>(),
    playerIds: (json['player_ids'] as List).cast<int>(),
    benchIds: (json['bench_ids'] as List).cast<int>(),
    savedAt: DateTime.parse(json['saved_at'] as String),
    captainId: json['captain_id'] as int?,
    viceCaptainId: json['vice_captain_id'] as int?,
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

  /// ⭐⭐ **Armbands live in the draft and nowhere else, because they change no number we compute.**
  /// FPL doubles the captain's points; our projections are the XI's own xP and do not. So setting a
  /// captain is a *display* decision — which is exactly why it can be a tap on the pitch rather than a
  /// screen of its own, and why it needs no server round trip.
  ///
  /// ⚠️ Null means *"use FPL's"*, not *"nobody"*.
  final int? captainId;
  final int? viceCaptainId;

  Map<String, dynamic> toJson() => {
    'manager_id': managerId,
    'gameweek': gameweek,
    'base_player_ids': basePlayerIds,
    'player_ids': playerIds,
    'bench_ids': benchIds,
    'saved_at': savedAt.toIso8601String(),
    'captain_id': captainId,
    'vice_captain_id': viceCaptainId,
  };

  /// The swaps this draft represents, as `(out, in)` ids.
  ///
  /// ⭐ Derived rather than stored: two lists and a subtraction cannot disagree with each other, where a
  /// stored list of swaps could drift from the squad it claims to describe.
  List<(int, int)> get swaps {
    final gone = basePlayerIds.where((id) => !playerIds.contains(id)).toList();
    final added = playerIds.where((id) => !basePlayerIds.contains(id)).toList();
    return [
      for (var i = 0; i < gone.length && i < added.length; i++)
        (gone[i], added[i]),
    ];
  }

  bool get isEmpty =>
      swaps.isEmpty && captainId == null && viceCaptainId == null;

  /// How many changes this plan represents, armbands included — what the banner counts.
  int get changeCount =>
      swaps.length +
      (captainId == null ? 0 : 1) +
      (viceCaptainId == null ? 0 : 1);

  /// ⚠️⚠️ **`clearCaptain` / `clearViceCaptain` exist because `null` could not mean "clear"** (ADR-241).
  /// With `captainId ?? this.captainId`, passing null means *leave it alone* — so the caller that tried to
  /// empty the vice slot silently kept it, and one player ended up wearing **C and V at once**, which FPL
  /// would reject. ⭐ *An optional argument cannot say "unset" and "no opinion" with the same value.*
  Draft copyWith({
    List<int>? playerIds,
    List<int>? benchIds,
    int? captainId,
    int? viceCaptainId,
    bool clearCaptain = false,
    bool clearViceCaptain = false,
  }) => Draft(
    managerId: managerId,
    gameweek: gameweek,
    basePlayerIds: basePlayerIds,
    playerIds: playerIds ?? this.playerIds,
    benchIds: benchIds ?? this.benchIds,
    savedAt: savedAt,
    captainId: clearCaptain ? null : (captainId ?? this.captainId),
    viceCaptainId: clearViceCaptain
        ? null
        : (viceCaptainId ?? this.viceCaptainId),
  );

  /// A plan after swapping one player for another — ⭐⭐ **a named function rather than ten lines inside
  /// a widget's private method, which is how the armband bug got in** (ADR-241).
  ///
  /// ⚠️ Logic that lives in a `State` cannot be called by a test, so its test has to *re-describe* it —
  /// and a re-description drifts from the thing it describes without either side going red. The armband
  /// was dropped here for exactly as long as nothing could reach this code but the app itself.
  static Draft swap({
    required Draft? existing,
    required int managerId,
    required int gameweek,
    required List<int> basePlayerIds,
    required List<int> benchIds,
    required int outId,
    required int inId,
    required DateTime savedAt,
    int? teamCaptainId,
    int? teamViceCaptainId,
  }) {
    final current = existing?.playerIds ?? basePlayerIds;
    final next = [for (final id in current) id == outId ? inId : id];
    final bench = [for (final id in benchIds) id == outId ? inId : id];
    final carried =
        existing ??
        Draft(
          managerId: managerId,
          gameweek: gameweek,
          basePlayerIds: basePlayerIds,
          playerIds: basePlayerIds,
          benchIds: benchIds,
          savedAt: savedAt,
          captainId: teamCaptainId,
          viceCaptainId: teamViceCaptainId,
        );
    final armbands = carried.armbandsWithin(next);
    return Draft(
      managerId: managerId,
      gameweek: gameweek,
      basePlayerIds: basePlayerIds,
      playerIds: next,
      benchIds: bench,
      savedAt: savedAt,
      captainId: armbands.captain,
      viceCaptainId: armbands.vice,
    );
  }

  /// The armbands after a squad change — ⭐ **an armband is only valid while the player is still yours.**
  ///
  /// ⚠️ A C left on a player you have transferred away is worse than no C: it survives into the pitch, the
  /// plan and the next reload, describing a squad that no longer exists.
  ({int? captain, int? vice}) armbandsWithin(List<int> squad) => (
    captain: squad.contains(captainId) ? captainId : null,
    vice: squad.contains(viceCaptainId) ? viceCaptainId : null,
  );

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
    if (gameweek != null && this.gameweek != gameweek) {
      return DraftStaleness.gameweekPassed;
    }
    if (!_sameSet(basePlayerIds, fplPlayerIds)) {
      return DraftStaleness.squadChanged;
    }
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
