/// The tappable **?** — a phone's answer to the web's tooltip (ADR-249).
///
/// ⭐⭐ **A hover tooltip has no phone equivalent, and pretending otherwise is the trap.** The web's `?`
/// reveals on hover, which a touch screen cannot do; a long-press would be a gesture nobody discovers.
/// So it is a **tap that opens a sheet** — bigger than a tooltip, which is the right trade: there is room
/// to say what a number *is not*, and that is usually the honest half.
///
/// ⚠️ The text comes from the generated [glossary], never from a string typed at the call site. *A second
/// copy of an explanation is how two surfaces start saying different things about one number.*
library;

import 'package:flutter/material.dart';

import 'brand.dart';
import 'glossary.dart';

class HelpDot extends StatelessWidget {
  const HelpDot(this.termKey, {this.size = 14, super.key});

  /// A key in the generated glossary. ⭐ An unknown key renders **nothing** rather than a dot that
  /// explains nothing — *a control that does not work is worse than no control.*
  final String termKey;
  final double size;

  @override
  Widget build(BuildContext context) {
    final entry = term(termKey);
    if (entry == null) return const SizedBox.shrink();
    return GestureDetector(
      onTap: () => showHelp(context, termKey),
      behavior: HitTestBehavior.opaque,
      child: Padding(
        // ⚠️ Padding, not a bigger icon: the dot stays visually small while the **tap target** grows to
        // something a thumb can hit.
        padding: const EdgeInsets.all(6),
        child: Icon(
          Icons.help_outline,
          size: size,
          color: Colors.white38,
          semanticLabel: 'What is ${entry.$1}?',
        ),
      ),
    );
  }
}

Future<void> showHelp(BuildContext context, String termKey) async {
  final entry = term(termKey);
  if (entry == null) return;
  final (label, body) = entry;

  await showModalBottomSheet<void>(
    context: context,
    backgroundColor: Brand.ink,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 36,
                height: 4,
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            // ⚠️ Scrollable: some entries carry a warning paragraph, and a sheet that clipped the limit
            // would keep the promise and lose the caveat — ⭐ *which is the half that matters.*
            Flexible(child: SingleChildScrollView(child: _Markdownish(body))),
          ],
        ),
      ),
    ),
  );
}

/// ⭐ The glossary writes `**bold**` for the words that carry the caveat, so the sheet honours it. A full
/// markdown package for one emphasis rule would be a dependency to keep current forever.
class _Markdownish extends StatelessWidget {
  const _Markdownish(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    final spans = <TextSpan>[];
    for (final (i, part) in text.split('**').indexed) {
      spans.add(
        TextSpan(
          text: part,
          style: TextStyle(
            color: i.isOdd ? Colors.white : Colors.white70,
            fontWeight: i.isOdd ? FontWeight.w700 : FontWeight.w400,
          ),
        ),
      );
    }
    return Text.rich(
      TextSpan(children: spans),
      style: const TextStyle(fontSize: 13.5, height: 1.55),
    );
  }
}
