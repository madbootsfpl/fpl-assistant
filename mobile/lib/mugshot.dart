/// A player's face, where his name already is (ADR-255).
///
/// ⚠️⚠️ **Never on the pitch.** ADR-084 chose the club kit there on purpose: FPL's photo CDN lags a
/// transfer by weeks while the kit graphic updates instantly, so a just-transferred player would sit on
/// the pitch wearing his old club's face. ⭐ *On a card his name is beside him and the staleness is a
/// curiosity; on the pitch it is the app being visibly wrong about your team.*
///
/// ⭐ Degrades to his initials rather than to a broken-image glyph — *a placeholder that looks deliberate
/// reads as "no photo"; one that looks broken reads as "this app is broken".*
library;

import 'package:flutter/material.dart';

import 'brand.dart';

class Mugshot extends StatelessWidget {
  const Mugshot({
    required this.url,
    required this.name,
    this.size = 46,
    super.key,
  });

  final String url;
  final String name;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size * 1.12,
    clipBehavior: Clip.antiAlias,
    decoration: BoxDecoration(
      color: Colors.white10,
      borderRadius: BorderRadius.circular(Brand.radiusSm),
    ),
    child: url.isEmpty
        ? _Initials(name: name, size: size)
        : Image.network(
            // ⚠️⚠️ **A cross-origin image needs a CORS header on the web, and the two servers we
            // take images from send none** (ADR-301). CanvasKit fetches the bytes in order to draw
            // them, so the fetch fails and every kit and mugshot falls back to the 👕 — measured on
            // the first desktop build, where all fifteen shirts came out identical.
            //
            // ⭐ `fallback` hands the URL to a plain `<img>` when the fetch fails, which a browser
            // displays cross-origin quite happily because it never exposes the pixels to script.
            // ⚠️ Ignored on mobile, so it costs nothing there.
            webHtmlElementStrategy: WebHtmlElementStrategy.fallback,
            url,
            fit: BoxFit.cover,
            // ⚠️ A photo is decoration and the numbers beside it are the point — a CDN miss must not take
            // the card down, and FPL's photo set genuinely has gaps for new signings.
            errorBuilder: (_, _, _) => _Initials(name: name, size: size),
            loadingBuilder: (context, child, progress) =>
                progress == null ? child : _Initials(name: name, size: size),
          ),
  );
}

class _Initials extends StatelessWidget {
  const _Initials({required this.name, required this.size});

  final String name;
  final double size;

  @override
  Widget build(BuildContext context) {
    // ⭐ The first letter of each word, capped at two — "van Dijk" gives "vD", "Haaland" gives "H".
    final letters = name
        .split(RegExp(r'[\s.]+'))
        .where((w) => w.isNotEmpty)
        .take(2)
        .map((w) => w[0])
        .join();
    return Center(
      child: Text(
        letters.isEmpty ? '·' : letters,
        style: TextStyle(
          color: Colors.white38,
          fontSize: size * 0.34,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
