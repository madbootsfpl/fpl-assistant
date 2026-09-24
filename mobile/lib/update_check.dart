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
  });

  factory Available.fromJson(Map<String, dynamic> json) => Available(
    version: json['version'] as String? ?? '',
    build: (json['build'] as num?)?.toInt() ?? 0,
    url: json['url'] as String? ?? '',
  );

  final String version;
  final int build;
  final String url;
}

/// The published build, or `null` if it could not be read.
///
/// ⭐ Null on **every** failure — offline, a typo'd URL, a half-deployed site serving HTML. ⚠️ *A
/// distribution check that can throw is a distribution check that crashes the app it is updating.*
Future<Available?> published({
  http.Client? client,
  Duration timeout = const Duration(seconds: 4),
}) async {
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
