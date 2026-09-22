/// MADBOOTS brand tokens — **generated**, do not edit.
///
/// ⭐⭐ Written by `scripts/generate_brand_dart.py` from `src/web_streamlit/brand.py`, which is the single
/// source of truth for the product's identity (ADR-103/114). Editing this file by hand puts a second
/// definition of the brand in the codebase, and `tests/test_brand_dart.py` will fail on the next run.
///
/// To change a colour: change `brand.py`, then regenerate.
library;

import 'package:flutter/material.dart';

/// An FDR band's colour pair — ⭐ always a **pair**, never a background alone, because white-on-mid-tint
/// failed WCAG AA on the web app and the same contrast problem does not go away on a smaller screen.
typedef FdrStyle = ({Color background, Color foreground});

class Brand {
  Brand._();

  static const String name = 'MADBOOTS';
  static const String tagline = 'Fantasy Football, Calculated.';

  /// ⭐ Names the two halves of the system in the order they run — a description of the architecture rather
  /// than a metaphor about it, which is why it cannot drift from the truth (ADR-182).
  static const String mantra =
      'Analytics decide. Logic explains. You make the call.';
  static const String descriptor =
      'The FPL assistant where analytics decide and logic explains.';

  /// Legal hygiene (ADR-103) — a named product on official FPL data.
  static const String disclaimer =
      'MADBOOTS is not affiliated with the Premier League or the official Fantasy Premier League game.';

  /// The primary.
  static const Color purple = Color(0xFF8B2FC9);

  /// Legible on the card band's dark ground.
  static const Color purpleLight = Color(0xFFB45CF0);

  static const Color orange = Color(0xFFFF6A00);

  static const Color ink = Color(0xFF17131F);

  // Semantic state — ⚠️ each is a **triple**: a solid, a light tint for a chip background, and a foreground
  // for text on that tint. The solids clear ~4.5:1 on white; a solid used as a chip background does not.

  static const Color good = Color(0xFF1E8047);

  static const Color goodTint = Color(0xFFE6F4EC);

  static const Color goodFg = Color(0xFF0B5E30);

  static const Color warn = Color(0xFFD98C00);

  static const Color warnTint = Color(0xFFFDF1D6);

  static const Color warnFg = Color(0xFF8A5A00);

  static const Color bad = Color(0xFFC62828);

  static const Color badTint = Color(0xFFFCE8E8);

  static const Color badFg = Color(0xFFA51D1D);

  /// The single projected/winner highlight.
  static const Color accentTeal = Color(0xFF5EEAD4);

  // Neutrals.

  static const Color text = Color(0xFF1C1830);

  static const Color muted = Color(0xFF5F6472);

  static const Color line = Color(0xFFE6E6EA);

  static const Color surface = Color(0xFFFFFFFF);

  static const Color surface2 = Color(0xFFF4F2F8);

  /// Fixture difficulty 1–5 — ⭐ mirrors the official FPL app deliberately, so it reads familiarly:
  /// deep green → bright green → **grey, the neutral break** → red → maroon.
  static const Map<int, FdrStyle> fdr = {
    1: (background: Color(0xFF257D5A), foreground: Color(0xFFFFFFFF)),
    2: (background: Color(0xFF01FC7A), foreground: Color(0xFF0A3D2A)),
    3: (background: Color(0xFFE7E7E7), foreground: Color(0xFF3A3A3A)),
    4: (background: Color(0xFFFF1751), foreground: Color(0xFFFFFFFF)),
    5: (background: Color(0xFF80072D), foreground: Color(0xFFFFFFFF)),
  };

  /// Spacing rungs, so paddings stop being ad hoc.
  static const List<double> space = [4, 8, 12, 16, 20, 24];

  static const double radiusSm = 10;
  static const double radiusMd = 14;
  static const double radiusLg = 18;
  static const double radiusPill = 999;
}
