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

  /// ⚠️⚠️ **The draft contradicts itself** — a bench id that is not in its own squad (ADR-291).
  ///
  /// ⭐ This should be impossible, and it happened: `swap()` built the XI from the draft and the bench
  /// from the team, so a second transfer resurrected a sold player onto the bench. The server refused
  /// the request and the app showed the refusal on every launch — ⚠️ *a saved plan that cannot be sent
  /// and cannot be cleared is an app that will not open.*
  ///
  /// ⭐⭐ Checked even though the bug that caused it is fixed: *the fix stops new ones being written, and
  /// says nothing about the one already on somebody's phone.*
  inconsistent,
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
    this.signalKeys = const {},
    this.name = '',
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
    // ⚠️ Absent on a plan saved before ADR-260 — which reads as "nothing was known", so every current
    // signal looks new. ⭐ That is the safe direction: *over-reporting a change invites a second look;
    // under-reporting one lets a plan be executed blind.*
    signalKeys: {
      for (final k in (json['signal_keys'] as List? ?? const [])) '$k',
    },
    name: json['name'] as String? ?? '',
  );

  final int managerId;

  /// ⭐ **What the manager called this plan**, empty for an unnamed one (ADR-272).
  ///
  /// ⚠️ It earns its place when a draft stops being *"the two moves I am considering"* and becomes a
  /// whole squad — *"Wildcard" and "Free Hit" are different plans for the same fifteen*, and a screen
  /// showing one of them with no name cannot say which.
  final String name;

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
    'signal_keys': signalKeys.toList(),
    'captain_id': captainId,
    'vice_captain_id': viceCaptainId,
    'name': name,
  };

  /// ⭐⭐⭐ **What was known about your players when this plan was made** (ADR-260).
  ///
  /// The owner: *"people like to manipulate their teams, wait till near deadline and then make the
  /// changes **if nothing else external has happened that might influence change**."* Keeping the plan was
  /// only half of that — ⚠️ *a plan you come back to is only safe to execute if you know what has changed
  /// underneath it*, and until now the app knew and never said.
  ///
  /// ⭐ Stored as keys rather than a timestamp: a signal's key is already stable (ADR-232), so "what is
  /// new" is a set difference and needs no clock. *The device compared, the server never has to know when
  /// you last looked.*
  final Set<String> signalKeys;

  /// What has happened since, given what is known now.
  Set<String> since(Iterable<String> current) => {
    for (final k in current)
      if (!signalKeys.contains(k)) k,
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
    // ⚠️⚠️ **These were being dropped, and it was live.** `copyWith` rebuilt the `Draft` without them,
    // so `_applyPlan` — the "Play Them" button — silently emptied the record of what was known when the
    // plan was made. ⭐ *The exact defect ADR-260 was written to prevent*, protected in `swap` and
    // `substitute` and then reintroduced by the one path that looked too small to matter.
    signalKeys: signalKeys,
    name: name,
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

    /// ⭐ Only used when there is **no** existing plan — an existing one already carries its own, and
    /// overwriting it would silence the warning the plan needs on its way back.
    Set<String> signalKeys = const {},
  }) {
    final current = existing?.playerIds ?? basePlayerIds;
    final next = [for (final id in current) id == outId ? inId : id];
    // ⚠️⚠️ **From the draft, exactly like the XI above** (ADR-291). This read `benchIds` — the *team's*
    // bench — while the XI came from `existing.playerIds`, so a second transfer rebuilt the bench from
    // the original squad and **resurrected the player the first transfer had sold**. The owner's phone
    // reached `draft bench ids not in the draft squad: [496]` and could not get past it.
    //
    // ⭐ *Two halves of one object derived from two sources will disagree; the only question is when.*
    // `replace()` next door has always done it this way.
    final currentBench = existing?.benchIds ?? benchIds;
    final bench = [for (final id in currentBench) id == outId ? inId : id];
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
          signalKeys: signalKeys,
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
      // ⚠️ Carried, not re-read. A transfer is a change to the *plan*, not a moment of looking at the
      // news — ⭐ *resetting it here would quietly mark everything as seen and silence the very warning
      // the plan needs on its way back.*
      signalKeys: carried.signalKeys,
    );
  }

  /// Change two players' places — ⭐ a **lineup** change, the fifteen untouched (ADR-246).
  ///
  /// ⚠️ A named function rather than lines inside a widget, for the reason ADR-241 paid for: logic in a
  /// `State` cannot be called by a test, so its test has to re-describe it, and a re-description drifts.
  ///
  /// ⭐ The incoming player takes the outgoing one's **place in the bench order**, rather than being
  /// appended. FPL substitutes in bench order, so appending would quietly demote him to last — a change
  /// the manager did not ask for, hidden inside one he did.
  static Draft substitute({
    required Draft? existing,
    required int managerId,
    required int gameweek,
    required List<int> basePlayerIds,
    required List<int> benchIds,
    required int a,
    required int b,
    required DateTime savedAt,
    int? teamCaptainId,
    int? teamViceCaptainId,
    Set<String> signalKeys = const {},
  }) {
    final bench = List<int>.from(existing?.benchIds ?? benchIds);
    // ⚠️ Exactly one of the two is on the bench — the server only offers legal partners, and a swap
    // between two starters or two subs is not a substitution.
    final leaving = bench.contains(a) ? a : b;
    final arriving = leaving == a ? b : a;
    final slot = bench.indexOf(leaving);
    if (slot < 0) {
      // ⚠️ Neither is on the bench, so this is not a substitution. Returning the plan unchanged is the
      // honest answer — ⭐ *a no-op beats inventing a lineup nobody asked for.*
      return existing ??
          _fresh(
            managerId,
            gameweek,
            basePlayerIds,
            benchIds,
            savedAt,
            teamCaptainId,
            teamViceCaptainId,
            signalKeys,
          );
    }
    bench[slot] = arriving;

    final carried =
        existing ??
        _fresh(
          managerId,
          gameweek,
          basePlayerIds,
          benchIds,
          savedAt,
          teamCaptainId,
          teamViceCaptainId,
        );
    return Draft(
      managerId: managerId,
      gameweek: gameweek,
      basePlayerIds: basePlayerIds,
      playerIds: carried.playerIds,
      benchIds: bench,
      savedAt: savedAt,
      captainId: carried.captainId,
      viceCaptainId: carried.viceCaptainId,
      signalKeys: carried.signalKeys,
    );
  }

  static Draft _fresh(
    int managerId,
    int gameweek,
    List<int> basePlayerIds,
    List<int> benchIds,
    DateTime savedAt,
    int? captainId,
    int? viceCaptainId, [
    // ⭐ Optional and last: every caller that has an existing plan takes its keys from that plan instead.
    Set<String> signalKeys = const {},
  ]) => Draft(
    managerId: managerId,
    gameweek: gameweek,
    basePlayerIds: basePlayerIds,
    playerIds: basePlayerIds,
    benchIds: benchIds,
    savedAt: savedAt,
    captainId: captainId,
    viceCaptainId: viceCaptainId,
  );

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
    // ⚠️ **First**, because a self-contradictory draft must be dropped whoever it belongs to and
    // whatever gameweek it is for — ⭐ *the other three checks ask whether it still applies; this one
    // asks whether it was ever sendable.*
    if (benchIds.any((id) => !playerIds.contains(id))) {
      return DraftStaleness.inconsistent;
    }
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
