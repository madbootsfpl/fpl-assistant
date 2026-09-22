/// The DNA axes as bars — ⭐ **shared by club and player fingerprints** (ADR-250).
///
/// ⭐⭐ Extracted the moment there was a second caller, not before. ⚠️ A private copy in each view is how
/// two screens that show the same eight numbers start colouring them differently — and the colours here
/// carry meaning (top quartile, middle, bottom), so a divergence would be a divergence in what the app
/// says, not just in how it looks.
///
/// ⭐ **Bars, where the web draws a radar.** A radar needs width a phone does not have; the owner's own
/// screenshot of the web page on his phone shows "FPL Output" clipped to "'PL Output" on the left edge.
library;

import 'package:flutter/material.dart';

import 'api/models.dart';
import 'brand.dart';

class DnaBars extends StatelessWidget {
  const DnaBars({required this.axes, super.key});

  final List<DnaAxis> axes;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [for (final axis in axes) _Bar(axis: axis)],
  );
}

/// ⚠️ The same four kinds the web uses (ADR-118) — good ✓ · set-piece ⚡ · info ℹ · warning ⚠. A fifth
/// mark invented for the phone would be a second vocabulary for one idea.
String dnaMark(String kind) => switch (kind) {
  'good' => '✓',
  'sp' => '⚡',
  'warn' => '⚠',
  _ => 'ℹ',
};

Color dnaColour(String kind) => switch (kind) {
  'good' => Brand.accentTeal,
  'sp' => Brand.orange,
  'warn' => Brand.warn,
  _ => Colors.white54,
};

/// One axis as a bar — ⭐ **percentile, so eight different units share one scale.**
class _Bar extends StatelessWidget {
  const _Bar({required this.axis});

  final DnaAxis axis;

  @override
  Widget build(BuildContext context) {
    final p = axis.percentile;
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Row(
        children: [
          SizedBox(
            width: 108,
            child: Text(
              axis.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.white60, fontSize: 10.5),
            ),
          ),
          Expanded(
            child: Container(
              height: 7,
              decoration: BoxDecoration(
                color: Colors.white10,
                borderRadius: BorderRadius.circular(4),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                // ⚠️ **Null is unranked, not zero.** An empty bar for "we could not rank this" reads as
                // "this club is the worst in the league at it", which is a different and wrong claim.
                widthFactor: (p ?? 0) / 100,
                child: Container(
                  decoration: BoxDecoration(
                    color: p == null
                        ? Colors.transparent
                        : p >= 75
                        ? Brand.good
                        : p >= 40
                        ? Brand.purpleLight
                        : Brand.warn,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
          ),
          SizedBox(
            width: 32,
            child: Text(
              p == null ? '—' : '$p',
              textAlign: TextAlign.right,
              style: const TextStyle(color: Colors.white70, fontSize: 10.5),
            ),
          ),
        ],
      ),
    );
  }
}
