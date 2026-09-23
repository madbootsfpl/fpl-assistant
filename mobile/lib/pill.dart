/// The selectable pill — one widget, everywhere a row of choices appears (ADR-269).
///
/// ⚠️⚠️ **This exists because `ChoiceChip` shipped unreadable.** Material 3 ignores `backgroundColor` for
/// the *unselected* state and paints its own near-white surface, so a `white54` label sat on white and
/// four rows of choices rendered as **blank blocks**. ⭐ *A widget that ignores the colour you set is
/// worse than one that has none* — it fails only in the state you are least likely to screenshot.
///
/// ⭐ The rest of the app had always hand-built these, and those rows were the ones that looked right.
/// This is that pill, named, so the next row of choices cannot reintroduce the bug.
library;

import 'package:flutter/material.dart';

import 'brand.dart';

class Pill extends StatelessWidget {
  const Pill({
    required this.label,
    required this.selected,
    required this.onTap,
    this.expand = false,
    super.key,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  /// ⭐ True inside a `Row` that divides its width; false in a horizontal scroller, where a pill is as
  /// wide as its word.
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final pill = GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 2),
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 14),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          // ⚠️ Explicit on both states. The unselected one is the whole reason this widget exists.
          color: selected ? Brand.purple : Colors.white10,
          borderRadius: BorderRadius.circular(Brand.radiusPill),
        ),
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : Colors.white60,
              fontSize: 12.5,
              fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ),
      ),
    );
    return expand ? Expanded(child: pill) : pill;
  }
}

/// A horizontally scrolling row of pills — ⚠️ *a row that overflows silently is a row whose last option
/// nobody knows about*, so it scrolls rather than squeezing.
class PillRow extends StatelessWidget {
  const PillRow({required this.children, this.height = 40, super.key});

  final List<Widget> children;
  final double height;

  @override
  Widget build(BuildContext context) => SizedBox(
    height: height,
    child: ListView(scrollDirection: Axis.horizontal, children: children),
  );
}

/// A small two-option switch — ⭐ **for a choice that modifies the thing above it**, where a full row of
/// pills would claim equal billing with the mode itself.
///
/// ⚠️ The owner, on the Lab: *"can the Strong XI & Strong 15 be a toggle, doesn't need to be a large
/// tab."* He is right — ⭐ *a control's size is a claim about its importance*, and two rows of identical
/// pills said the build style mattered as much as choosing a wildcard.
class MiniToggle extends StatelessWidget {
  const MiniToggle({
    required this.label,
    required this.options,
    required this.selected,
    required this.onPick,
    super.key,
  });

  /// What the choice is *about*, set beside it rather than above — ⚠️ *a toggle with no subject is two
  /// words a reader has to infer a question from.*
  final String label;
  final List<String> options;
  final String selected;
  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Text(
        label,
        style: const TextStyle(color: Colors.white38, fontSize: 11.5),
      ),
      const SizedBox(width: 8),
      Container(
        padding: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(Brand.radiusPill),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final option in options)
              GestureDetector(
                onTap: () => onPick(option),
                behavior: HitTestBehavior.opaque,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    // ⚠️ Explicit on both states, for the reason `Pill` exists (ADR-269).
                    color: selected == option
                        ? Brand.purple
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(Brand.radiusPill),
                  ),
                  child: Text(
                    option,
                    style: TextStyle(
                      color: selected == option ? Colors.white : Colors.white54,
                      fontSize: 11.5,
                      fontWeight: selected == option
                          ? FontWeight.w600
                          : FontWeight.w400,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    ],
  );
}
