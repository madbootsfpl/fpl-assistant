/// Whether a newer build exists (ADR-282).
///
/// ⭐⭐ **The problem distribution actually has to solve is not the first install, it is the fifth.**
/// Nine testers can each be sent an APK once; asking them to go and re-download it after every fix is a
/// request that quietly stops being honoured — and then a bug report arrives about something fixed last
/// week, from someone whose phone never said anything was wrong.
///
/// ⚠️ **The manifest lives beside the APK it describes** (`madboots.com/app/version.json`), so the two
/// cannot disagree. ⭐ *A manifest kept somewhere else is a manifest that will eventually describe a
/// different build.*
///
/// ⚠️⚠️ **It never blocks anything.** No await on start-up, no modal, no forced update — a failed check
/// is silent and the app behaves exactly as it did before. ⭐ *An update prompt that can stop you using
/// the app is worse than the stale build it is warning about.*
library;

import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

/// Where the current build is published. ⚠️ Not the API: the API knows about squads, not about which
/// APK is on the website — ⭐ *asking it would make it the authority on something it cannot see.*
/// ⭐ Overridable via `--dart-define=MADBOOTS_MANIFEST=…`, the same way the API url already is. Not for
/// configuration — there is one website — but so the banner can be **seen to fire** against a local
/// manifest. ⚠️ *A notice that only appears when a real release exists is a notice first tested in front
/// of testers.*
const String kManifestUrl = String.fromEnvironment(
  'MADBOOTS_MANIFEST',
  defaultValue: 'https://madboots.com/app/version.json',
);

class Available {
  const Available({
    required this.version,
    required this.build,
    required this.url,
    this.notes = const [],
  });

  factory Available.fromJson(Map<String, dynamic> json) => Available(
    version: json['version'] as String? ?? '',
    build: (json['build'] as num?)?.toInt() ?? 0,
    url: json['url'] as String? ?? '',
    // ⚠️ **A list, and a string is accepted too.** The field shipped as `""` in ADR-282 and the
    // manifests already published still carry that shape — ⭐ *a reader that only understands the new
    // format makes every older release unreadable, which is the opposite of what a version check is
    // for.* Blank entries are dropped, so `""` simply means no notes.
    notes: _notes(json['notes']),
  );

  final String version;
  final int build;
  final String url;

  /// What changed, in the words of the release that changed it (ADR-296).
  ///
  /// ⭐⭐ **Empty is the normal case and must read as one.** A release with nothing worth saying is not a
  /// broken release — ⚠️ *a banner that insists on filling this field will get "various fixes" forever,
  /// which is worse than silence because it looks like information.*
  final List<String> notes;
}

/// What changed, cleaned and capped — ⭐⭐ **in one place.**
///
/// ⚠️ The cap lived in three: here, the generator, and the banner's `take(3)`. Mutating any one of them
/// left the other two passing, which is ⭐ *a cap enforced in several places being a cap that moves* —
/// the banner now renders whatever this returns and trusts it.
///
/// ⚠️ **A bare string is accepted**, because `"notes": ""` is the shape ADR-282 shipped and manifests
/// carrying it are already published: *a reader that only understands the new format makes every older
/// release unreadable.*
List<String> _notes(Object? raw) => switch (raw) {
  final List list => [
    for (final n in list)
      if ('$n'.trim().isNotEmpty) '$n'.trim(),
  ].take(kMaxNotes).toList(),
  final String s when s.trim().isNotEmpty => [s.trim()],
  _ => const [],
};

/// ⚠️ **Three.** A release with eleven commits has eleven things to say and the reader has a banner —
/// ⭐ *a notice that grows with the work is a notice that stops being read on the busiest week.*
const int kMaxNotes = 3;

/// Whether this build can install its own updates.
///
/// ⚠️⚠️⚠️ **Android only, and the first version checked nothing** (owner's report from his iPhone:
/// *"the build 14 is out, asks me to download the .apk which doesn't seem correct"*). The manifest at
/// `madboots.com/app/version.json` describes an **APK** — the one artefact an iPhone cannot do anything
/// with. iOS builds are installed from Xcode today and from TestFlight when that is paid for, and in
/// neither case can the app update itself.
///
/// ⭐ *A notice is a promise that tapping it will help*, and this one offered an iPhone a file it cannot
/// open, from a page it cannot install from. Silence is the correct behaviour, not a smaller banner.
///
/// ⚠️ `kIsWeb` first: `Platform` throws in a browser, so the order of these two is load-bearing.
bool get selfHostedUpdates => !kIsWeb && Platform.isAndroid;

/// The published build, or `null` if it could not be read.
///
/// ⭐ Null on **every** failure — offline, a typo'd URL, a half-deployed site serving HTML. ⚠️ *A
/// distribution check that can throw is a distribution check that crashes the app it is updating.*
Future<Available?> published({
  http.Client? client,
  Duration timeout = const Duration(seconds: 4),
  bool? selfHosted,
}) async {
  // ⚠️⚠️ **The platform gate lives here, not at the call site.** Every future caller of this function
  // inherits it — ⭐ *a rule enforced where the decision is made cannot be forgotten by the next person
  // who needs the answer.*
  //
  // ⭐ Overridable so it can be **tested on either platform**: the bug shipped precisely because the
  // iOS path could not be exercised from a Mac test run. *A guard no test can reach is a guard that is
  // not there.*
  if (!(selfHosted ?? selfHostedUpdates)) return null;
  final own = client == null;
  final c = client ?? http.Client();
  try {
    final response = await c.get(Uri.parse(kManifestUrl)).timeout(timeout);
    if (response.statusCode != 200) return null;
    // ⚠️ No shape check before this. A body that is not an object throws inside `fromJson` and lands
    // in the `catch` below with the identical result — ⭐ *a guard no test can tell is missing is a
    // guard that will one day be deleted by someone who cannot tell either.* The `catch` is the net.
    final available = Available.fromJson(jsonDecode(response.body));
    return available.build > 0 ? available : null;
  } catch (_) {
    return null;
  } finally {
    if (own) c.close();
  }
}

/// Is `available` newer than the build running?
///
/// ⚠️ **Compared on the build number, never on the version name.** `1.0.0` ships many times during a
/// beta, and ⭐ *a comparison on a label that does not change cannot tell two builds apart* — which is
/// exactly the mistake Android itself refuses to make when it ignores `versionName`.
bool isNewer({required Available? available, required int runningBuild}) {
  if (available == null) return false;
  return available.build > runningBuild;
}
