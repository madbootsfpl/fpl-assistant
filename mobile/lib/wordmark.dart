/// The MADBOOTS wordmark — **one widget** (ADR-312).
///
/// ⚠️⚠️⚠️ **It was hand-built in four places in this app and two on the web, and no two agreed.** Measured:
/// `brand.py` and the landing page set it **italic 900 at −.01em**; `main`, `welcome_view`, `pitch` and
/// `boot_battle` set it **upright 700/800 at +.3 to +1.2**. ⭐⭐ *The web tightened the word and the app
/// loosened it — opposite directions from the same brand* — and upright against italic is the difference a
/// reader actually notices.
///
/// ⭐ Every value here comes from `Brand`, which is generated from `brand.py` and pinned by
/// `tests/test_brand_dart.py`. ⚠️ *A sixth hand-built wordmark is how this happened; `test_one_wordmark.dart`
/// is what stops a seventh.*
library;

import 'package:flutter/material.dart';

import 'brand.dart';

class Wordmark extends StatelessWidget {
  const Wordmark({
    this.size = 15,
    this.onDark = true,
    this.weight,
    super.key,
  });

  /// Font size in logical pixels.
  final double size;

  /// ⭐ Which purple carries MAD — *legibility is a property of the ground* (ADR-312 §1).
  final bool onDark;

  /// ⚠️ An override only for places the brand weight will not fit; the default is the brand's.
  final FontWeight? weight;

  static FontWeight get _brandWeight => switch (Brand.wordmarkWeight) {
    >= 900 => FontWeight.w900,
    >= 800 => FontWeight.w800,
    _ => FontWeight.w700,
  };

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontSize: size,
      fontWeight: weight ?? _brandWeight,
      fontStyle: Brand.wordmarkItalic ? FontStyle.italic : FontStyle.normal,
      // ⭐ Tracking is declared in **em** so it scales with the size, the way the CSS does. A fixed
      // letter-spacing is why the app's six copies read differently at 10.5 and at 24.
      letterSpacing: Brand.wordmarkTrackingEm * size,
      height: 1.1,
    );
    return Text.rich(
      TextSpan(
        children: [
          TextSpan(
            text: 'MAD',
            style: TextStyle(color: onDark ? Brand.madOnDark : Brand.madOnLight),
          ),
          const TextSpan(text: 'BOOTS', style: TextStyle(color: Brand.orange)),
        ],
      ),
      style: style,
      // ⭐ One accessible name for the whole lockup, so a screen reader says the product once rather than
      // spelling two coloured fragments.
      semanticsLabel: Brand.name,
    );
  }
}
