/// One wordmark, and one place that draws it (ADR-312).
///
/// ⚠️⚠️⚠️ **`wordmark.dart` has cited this test since ADR-312 and it did not exist.** That is how a
/// seventh hand-built MADBOOTS got onto the pitch hoardings (ADR-332) — painted with a `TextPainter`
/// in one flat purple, upright, with tracking in pixels instead of em.
///
/// ⭐⭐ *A guard a file's own documentation claims is protecting it is worse than no guard*, because
/// everyone who reads the file believes the rule is enforced.
library;

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Where the brand may legitimately be spelled out.
const allowed = {'lib/brand.dart', 'lib/wordmark.dart'};

void main() {
  test('nothing but Wordmark draws the brand', () {
    final offenders = <String>[];
    for (final f in Directory(
      'lib',
    ).listSync(recursive: true).whereType<File>()) {
      final path = f.path;
      if (!path.endsWith('.dart') || allowed.contains(path)) continue;
      final text = f.readAsStringSync();
      // A literal MAD/BOOTS pair, or the whole word, in something that draws it.
      for (final needle in ["'MADBOOTS'", '"MADBOOTS"', "'BOOTS'", '"BOOTS"']) {
        if (text.contains(needle)) offenders.add('$path contains $needle');
      }
    }
    expect(
      offenders,
      isEmpty,
      reason:
          'the brand is spelled out outside Wordmark — use the widget, which carries the colours, '
          'the italic and the em tracking that six hand-built copies disagreed about:\n'
          '${offenders.join('\n')}',
    );
  });

  test('the pitch asks for the wordmark rather than drawing one', () {
    // ⭐ The hoardings are a widget layer for exactly this reason (ADR-332).
    final pitch = File('lib/pitch.dart').readAsStringSync();
    expect(pitch.contains('Wordmark('), isTrue);
    // ⚠️ The call, not the word: this file's own comment explains why the `TextPainter` went, and
    // an earlier version of this test failed on that sentence. ⭐ *A guard that reads prose is a
    // guard that fires on the note explaining it.*
    final painter = File('lib/pitch_3d.dart')
        .readAsStringSync()
        .split('\n')
        .where(
          (l) =>
              !l.trimLeft().startsWith('//') && !l.trimLeft().startsWith('///'),
        )
        .join('\n');
    expect(
      painter.contains('TextPainter('),
      isFalse,
      reason: 'the pitch painter is drawing text again — the brand belongs to Wordmark',
    );
  });
}
