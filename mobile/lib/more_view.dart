/// More — a **directory**, not a drawer (ADR-228, restructured ADR-238).
///
/// ⭐⭐ **Not a drawer for everything the web app can do.** The mobile audit §6 is explicit: *the mobile app
/// is the decision layer; the web app stays the exploration layer.* A "More" list that grew to eight items
/// would undo that positioning on the smaller screen — and this project already learned it the other way
/// round, when ADR-166 cut the web sidebar from twelve to nine **ordered by frequency** and ADR-167/170
/// answered "we need another board" with a reader instead.
///
/// ⭐⭐⭐ **What makes a directory hold more than a menu is the one-line description.** Every row here says
/// what is behind it, so the screen can grow without becoming a junk drawer: you read four descriptions
/// instead of guessing four nouns. That is the whole trick, and it costs nothing but the sentences.
///
/// ⚠️ **So the controls left.** This screen used to mix destinations with a text field, a stepper and a
/// feedback box — and a row you *change* reads nothing like a row you *enter*. They are in
/// [SettingsView] and [FeedbackView] now, each one tap deeper. ⭐ *Frequency decides depth* (ADR-230): free
/// transfers change weekly at most, and the screens they affect are opened daily.
library;

import 'package:flutter/material.dart';

import 'brand.dart';

class MoreView extends StatelessWidget {
  const MoreView({
    required this.managerId,
    required this.freeTransfers,
    required this.onOpenChips,
    required this.onOpenSignals,
    required this.onOpenSettings,
    required this.onOpenFeedback,
    super.key,
  });

  final int managerId;
  final int freeTransfers;

  /// ⭐ Signals is time-sensitive and squad-scoped — decision layer, not research. It is here rather than
  /// in the bar because the audit's first release does not include it, and *frequency earns a slot*
  /// (ADR-230). ⚠️ The better answer is probably a badge on the pitch: **being told beats going to look**,
  /// which is the whole reason a phone suits this.
  final VoidCallback onOpenSignals;

  /// ⭐ Chips lives here rather than in the bar — it works, and it is a handful of decisions per season.
  /// *Working earns a place; frequency earns a slot.*
  final VoidCallback onOpenChips;

  final VoidCallback onOpenSettings;
  final VoidCallback onOpenFeedback;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
        children: [
          _Row(
            icon: Icons.campaign_outlined,
            name: 'Signals',
            why: 'FPL news, reported moves, and sell-offs the data cannot explain — about your fifteen, '
                'strongest evidence first. Marks what is new since you last looked.',
            onTap: onOpenSignals,
          ),
          _Row(
            icon: Icons.style_outlined,
            name: 'Chips',
            why: 'Wildcard, Bench Boost, Triple Captain and Free Hit — judged over the weeks you have '
                'left, not the next one.',
            onTap: onOpenChips,
          ),
          _Row(
            icon: Icons.chat_bubble_outline,
            name: 'Tell us something',
            why: 'What worked, what broke, what you would add. It reaches us from here — you do not have '
                'to go and find a laptop.',
            onTap: onOpenFeedback,
          ),
          _Row(
            icon: Icons.tune,
            name: 'Settings',
            // ⭐⭐ **The row states its own current value**, the same idea as the filter chips: a directory
            // entry that says `Manager 2885974 · 2 free transfers` has already answered the question most
            // people open it to check. *Showing the state beats offering the options.*
            why: 'Manager $managerId · $freeTransfers free transfer${freeTransfers == 1 ? '' : 's'} · '
                'this gameweek’s numbers, and where they come from.',
            onTap: onOpenSettings,
          ),

          const _Heading('On the web'),
          const _Note(
            'madboots.streamlit.app carries the research surfaces: the fixture ticker, Team DNA and '
            'Trending — and the market-wide view of Signals, where this app shows only your own squad.',
          ),
          const _Note(
            // ⭐ The positioning, said out loud rather than implied by absence. Someone who cannot find
            // Team DNA here should learn that it is a decision, not an oversight.
            'That split is deliberate. This app is the decision layer — what to do this week, and what a '
            'move is worth. The web app stays the exploration layer, where a bigger screen earns its keep.',
            muted: true,
          ),
          const Padding(
            padding: EdgeInsets.only(top: 16),
            child: _Note(Brand.mantra, italic: true),
          ),
        ],
      );
}

/// One directory entry: icon, name, and **the line that makes the directory work**.
class _Row extends StatelessWidget {
  const _Row({
    required this.icon,
    required this.name,
    required this.why,
    required this.onTap,
  });

  final IconData icon;
  final String name;
  final String why;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(Brand.radiusSm),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 11),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.only(top: 1, right: 12),
                child: Icon(icon, size: 19, color: Brand.purpleLight),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name,
                        style: const TextStyle(
                            color: Colors.white, fontSize: 14.5, fontWeight: FontWeight.w600)),
                    Padding(
                      padding: const EdgeInsets.only(top: 3),
                      child: Text(why,
                          style: const TextStyle(
                              color: Colors.white38, fontSize: 11.5, height: 1.45)),
                    ),
                  ],
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(top: 2, left: 8),
                child: Icon(Icons.chevron_right, size: 18, color: Colors.white24),
              ),
            ],
          ),
        ),
      );
}

class _Heading extends StatelessWidget {
  const _Heading(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 26, bottom: 8),
        child: Text(text.toUpperCase(),
            style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1.2)),
      );
}

class _Note extends StatelessWidget {
  const _Note(this.text, {this.muted = false, this.italic = false});

  final String text;
  final bool muted;
  final bool italic;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text,
            style: TextStyle(
              color: muted ? Colors.white24 : Colors.white54,
              fontSize: 11.5,
              height: 1.5,
              fontStyle: italic ? FontStyle.italic : FontStyle.normal,
            )),
      );
}
