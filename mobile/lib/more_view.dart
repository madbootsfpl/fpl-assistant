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
    required this.onOpenTeamDna,
    required this.onOpenPlayerDna,
    required this.onOpenSignals,
    required this.onOpenSettings,
    required this.onOpenLab,
    required this.onOpenLeagues,
    required this.onOpenTicker,
    required this.onOpenFeedback,
    required this.onOpenHelp,
    super.key,
  });

  final int managerId;
  final int freeTransfers;

  /// ⭐ Signals is time-sensitive and squad-scoped — decision layer, not research. It is here rather than
  /// in the bar because the audit's first release does not include it, and *frequency earns a slot*
  /// (ADR-230). ⚠️ The better answer is probably a badge on the pitch: **being told beats going to look**,
  /// which is the whole reason a phone suits this.
  final VoidCallback onOpenSignals;

  /// ⭐ In More rather than the bar: it is research, and *frequency earns a slot* (ADR-230). ⚠️ It is also
  /// the app's first **exploration** surface — the audit put those on the web, so it is worth watching
  /// whether it pulls the phone the wrong way.
  final VoidCallback onOpenTeamDna;

  /// ⭐ Beside Team DNA, because they answer the two halves of the same question: *what kind of player is
  /// he* and *what kind of side is he in.*
  final VoidCallback onOpenPlayerDna;

  /// ⭐ Chips lives here rather than in the bar — it works, and it is a handful of decisions per season.
  /// *Working earns a place; frequency earns a slot.*
  final VoidCallback onOpenChips;

  final VoidCallback onOpenSettings;
  final VoidCallback onOpenLab;
  final VoidCallback onOpenLeagues;
  final VoidCallback onOpenTicker;
  final VoidCallback onOpenFeedback;

  /// ⚠️ Leaves the app, which is the point: it is the one thing here that is better elsewhere.
  final VoidCallback onOpenHelp;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
    children: [
      _Row(
        icon: Icons.campaign_outlined,
        name: 'Signals',
        why:
            'FPL news, reported moves, sell-offs the data cannot explain, and what the crowd is '
            'buying — your fifteen or the whole market, strongest evidence first. Marks what is new.',
        onTap: onOpenSignals,
      ),
      _Row(
        icon: Icons.fingerprint,
        name: 'Player DNA',
        why:
            'What kind of player he is — goal threat, creativity, set pieces, minutes — ranked against '
            'others in his position, not against the whole league.',
        onTap: onOpenPlayerDna,
      ),
      _Row(
        icon: Icons.insights_outlined,
        name: 'Team DNA',
        why:
            'Every club ranked across eight things that decide points — attack, defence, set pieces, '
            'fixtures. Which side a player belongs to is half of what he is worth.',
        onTap: onOpenTeamDna,
      ),
      _Row(
        icon: Icons.style_outlined,
        name: 'Chips',
        why:
            'Wildcard, Bench Boost, Triple Captain and Free Hit — judged over the weeks you have '
            'left, not the next one.',
        onTap: onOpenChips,
      ),
      _Row(
        icon: Icons.science_outlined,
        name: 'Squad Lab',
        // ⭐ Named by what it lets you do, not by what it runs. "Optimiser" describes the solver; nobody
        // opens an app to run a solver.
        why:
            'Rebuild your fifteen on a wildcard — keep who you want, and see exactly who would come in '
            'and who would go. Nothing here touches your real team.',
        onTap: onOpenLab,
      ),
      _Row(
        icon: Icons.emoji_events_outlined,
        name: 'Mini-leagues',
        // ⭐ Named by the thing people actually open it for. "Leagues" describes a list; the head-to-head
        // is the reason to look, and a table you already know the top of is not.
        why:
            'Your league tables, what everyone captained, and you against any rival — what actually '
            'separates your two squads this week.',
        onTap: onOpenLeagues,
      ),
      _Row(
        icon: Icons.grid_on,
        name: 'Fixture ticker',
        // ⭐ Says what the grid is FOR, not what it contains. "Every club's next six fixtures" describes
        // a table; "whose run turns good" is the reason to open one.
        why:
            'Every club’s next six, easiest run first — so you can see whose fixtures turn good before '
            'you plan a transfer.',
        onTap: onOpenTicker,
      ),
      // ⭐⭐ **Help goes out; feedback stays in** (ADR-254). They look like one item and are two jobs.
      // Help is *content* — long, searchable, better on a big screen, and updatable without an App Store
      // release. Reporting happens the instant you notice something, and ⚠️ *every step between noticing
      // and reporting loses reports* — so that one keeps its two taps, and keeps the screen and build
      // number it already sends for free.
      _Row(
        icon: Icons.menu_book_outlined,
        name: 'Help & videos',
        // ⚠️ Trimmed to the clause the owner named — *"on the web where a bigger screen earns its
        // keep"* — and **no further**. ⭐ The destination stays: `test_help_link.py` exists because
        // *tapping a list item and landing in Safari is a surprise unless it was announced*, and my
        // first trim took that with it. The guard caught it.
        why:
            'The written walkthrough and Maddie’s 90-second explainers. '
            'Opens madboots.streamlit.app.',
        onTap: onOpenHelp,
      ),
      _Row(
        icon: Icons.chat_bubble_outline,
        name: 'Tell us something',
        why:
            'What worked, what broke, what you would add. It reaches us from here — you do not have '
            'to go and find a laptop.',
        onTap: onOpenFeedback,
      ),
      _Row(
        icon: Icons.tune,
        name: 'Settings',
        // ⭐⭐ **The row states its own current value**, the same idea as the filter chips: a directory
        // entry that says `Manager 2885974 · 2 free transfers` has already answered the question most
        // people open it to check. *Showing the state beats offering the options.*
        why:
            'Manager $managerId · $freeTransfers free transfer${freeTransfers == 1 ? '' : 's'} · '
            'this gameweek’s numbers, and where they come from.',
        onTap: onOpenSettings,
      ),

      // ⚠️⚠️ **The "On the web" block is gone, and it had become wrong twice over.** It advertised the
      // fixture ticker and Squad Lab as surfaces the web carried — ⭐ *and both are now in this app*
      // (ADR-265, ADR-268). Positioning copy outlives the positioning it describes, and this one had
      // started telling a reader the opposite of what the directory above it offers.
      //
      // ⭐ The directory is also the screen's job. Two paragraphs of philosophy pushed the last option
      // below the fold — *an option you have to scroll to find is an option most people never see.*
      const Padding(
        padding: EdgeInsets.only(top: 14),
        child: _Note(Brand.mantra, italic: true, accent: true),
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
                Text(
                  name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Text(
                    why,
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 11.5,
                      height: 1.45,
                    ),
                  ),
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

class _Note extends StatelessWidget {
  const _Note(this.text, {this.italic = false, this.accent = false});

  final String text;
  final bool italic;

  /// ⭐ The mantra, in the brand's orange. It is the one line here that is a **statement about the
  /// product** rather than a description of a row — ⚠️ *and set in the same grey as the rows it sits
  /// under, it read as one more caption nobody finishes.*
  final bool accent;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(
      text,
      style: TextStyle(
        color: accent ? Brand.orange : Colors.white54,
        fontSize: accent ? 12.5 : 11.5,
        height: 1.5,
        fontStyle: italic ? FontStyle.italic : FontStyle.normal,
      ),
    ),
  );
}
