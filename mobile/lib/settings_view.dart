/// Settings — the things you set once and then forget (ADR-238).
///
/// ⭐ Split out of More so that More can be a **directory**. The Hub's works because every row is a
/// destination with a one-line description; ours could not be, because half of it was controls.
///
/// ⚠️ **Free transfers lives here, two taps from the pitch.** That is a real cost and an acceptable one:
/// it changes at most weekly, where the screens it affects are opened daily. ⭐ *Frequency decides depth,
/// the same rule that ordered the bottom bar* (ADR-230).
library;

import 'api/client.dart';
import 'admin_view.dart';

import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';

import 'server.dart';

import 'api/models.dart';
import 'brand.dart';
import 'help_dot.dart';

/// ⚠️⚠️ **Stateful because it is a pushed route**, and a pushed route is built from values captured at the
/// moment it was pushed. Owning [_freeTransfers] locally was not a style choice: with the parent's value
/// read straight from the constructor, tapping a number told the parent and **redrew nothing** — the
/// highlight stayed where it was and the screen looked broken while working perfectly. ⭐ *A control one
/// route away from its state has no way to hear that the state changed.*
class SettingsView extends StatefulWidget {
  const SettingsView({
    required this.team,
    required this.managerId,
    required this.freeTransfers,
    required this.onManagerId,
    required this.onFreeTransfers,
    required this.client,
    required this.baseUrl,
    required this.onServer,
    super.key,
  });

  final MyTeam team;
  final ServiceClient client;
  final int managerId;
  /// The manager's override, or null while the server's derivation stands (ADR-321).
  final int? freeTransfers;
  final ValueChanged<int> onManagerId;
  /// `null` asks the app to go back to working it out from history.
  final ValueChanged<int?> onFreeTransfers;

  /// Where the API is. ⭐ Runtime state, not a `const` — see [Server].
  final String baseUrl;
  final Future<void> Function(String) onServer;

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

/// ⚠️ On the device, never on the server — it is a password the owner types, not one we issue.
const String _adminKeyPref = 'madboots.admin_key';

class _SettingsViewState extends State<SettingsView> {
  /// ⭐ Remembered so a reload does not ask again. Read once, on first build.
  String? _adminKey;
  late int? _freeTransfers = widget.freeTransfers;

  /// ⭐ Changing whose team this is **leaves the screen**. The facts below are this manager's, captured on
  /// the way in; staying here would show you one manager's name over another's bank balance.
  void _manager(int id) {
    widget.onManagerId(id);
    Navigator.of(context).maybePop();
  }

  @override
  @override
  void initState() {
    super.initState();
    // ⚠️ Best-effort and silent: ⭐ *a stats panel that cannot remember a password is an inconvenience;
    // a Settings screen that fails to open because of one is a bug.*
    SharedPreferences.getInstance()
        .then((prefs) {
          if (!mounted) return;
          final saved = prefs.getString(_adminKeyPref);
          if (saved != null && saved.isNotEmpty) {
            setState(() => _adminKey = saved);
          }
        })
        .catchError((Object _) => null);
  }

  @override
  Widget build(BuildContext context) {
    final team = widget.team;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
      children: [
        const _Heading('Your team'),
        _ManagerIdRow(
          managerId: widget.managerId,
          // ⭐ Whose team that id belongs to, so the number can be checked against something a person
          // recognises — ⚠️ *an id on its own is only verifiable by pasting it somewhere else.*
          squadName: widget.team.squadName,
          onChanged: _manager,
        ),
        _FreeTransfersRow(
          // ⭐⭐ **What FPL's history implies you hold** (a tester's *"how does FFH know?"*). The paid
          // tools log you in and read `transfers.limit`; this derives it from the transfers you have
          // made. ⚠️ Moves made in the current window are invisible until the deadline passes, so you
          // may still know something this does not — which is what the override is for.
          implied: widget.team.freeTransfersImplied,
          // ⭐ The number actually in force, so the highlighted chip is never a different number from
          // the one the pitch and the week's plan are using (ADR-321).
          effective: widget.team.freeTransfers,
          source: widget.team.freeTransfersSource,
          value: _freeTransfers,
          onChanged: (n) {
            setState(() => _freeTransfers = n);
            widget.onFreeTransfers(n);
          },
        ),

        const _Heading('This gameweek'),
        _Fact(label: 'Gameweek', value: '${team.gameweek ?? '—'}'),
        _Fact(
          label: 'In the bank',
          value: team.bank == null ? '—' : '£${team.bank!.toStringAsFixed(1)}m',
          // ⭐ Where each number comes from, because two of the three on the pitch header are FPL's and
          // one is yours — and a reader cannot tell by looking.
          note: 'from FPL',
        ),
        _Fact(
          label: 'Squad value',
          value: team.value == null
              ? '—'
              : '£${team.value!.toStringAsFixed(1)}m',
          note: 'from FPL · includes the bank',
        ),
        if (team.activeChip != null)
          _Fact(
            label: 'Chip in play',
            value: team.activeChip!,
            note: 'from FPL',
          ),
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text(
            team.deadlineLabel,
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 11,
              height: 1.45,
            ),
          ),
        ),

        _Fact(
          label: 'Data refreshed',
          value: team.data.age,
          // ⭐ Always here, even when nothing is wrong. The pitch banner answers *"are these numbers
          // safe?"* and only when they are not; this answers *"how old is this?"* whenever anyone asks.
          note: team.data.behind ? 'behind a finished gameweek' : 'up to date',
        ),

        // ⚠️ **Not built into a tester's app at all** (ADR-270) — see `kServerFieldEnabled`.
        if (kServerFieldEnabled) ...[
          const _Heading('Server'),
          _ServerRow(baseUrl: widget.baseUrl, onServer: widget.onServer),
        ],

        const _Heading('On the web'),
        const _Note(
          // ⚠️⚠️⚠️ **This paragraph has now gone false twice.** It once named the fixture ticker, Team
          // DNA and Trending as web-only — all three were already in this app (ADR-245/247/265). Then
          // it said *"the web app stays the exploration layer"*, which stopped being true the day
          // `madboots.com` started serving **this same app** on the desktop (ADR-301/304).
          //
          // ⭐ *Positioning copy outlives the positioning it describes*, twice now in the same nine
          // lines — so this version claims the smallest true thing: where the videos are.
          'On a desktop, madboots.com runs this same app in the browser — same screens, same numbers, '
          'a bigger window.',
        ),
        const _Note(
          'madboots.com/help has the walkthrough, the FPL rules and Maddie\'s videos.',
          muted: true,
        ),

        const _Heading('About'),
        // ⭐⭐ **Which build this is** (a tester asked). ⚠️ It already existed — `kAppBuild` drives the
        // update check — and was readable **only** when an update was available, which is exactly when a
        // tester does not need it. ⭐ *The number that settles "is this the version with the fix?" was
        // being shown only to people who were already behind.*
        _Note('Version $kAppVersion  ·  build $kAppBuild'),
        const _Note(Brand.mantra, italic: true),
        const _Note(Brand.disclaimer, muted: true),
        // ⭐⭐ **Last, behind a disclosure, and only where a table of medians fits** (ADR-305). The owner
        // asked for it *"buried in Settings … on my desktop only"*. ⚠️⚠️ *Hiding it is tidiness, not
        // security* — the lock is the key check on the server, and the door is shut for everyone who
        // does not have the key whether or not they can find it.
        if (MediaQuery.sizeOf(context).width >= kAdminMinWidth) ...[
          const _Heading('Owner'),
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              title: const Text(
                'Usage stats',
                style: TextStyle(color: Colors.white70, fontSize: 13.5),
              ),
              subtitle: const Text(
                'Requests, platforms and the slow tail. Needs the admin key.',
                style: TextStyle(color: Colors.white38, fontSize: 11.5),
              ),
              iconColor: Colors.white38,
              collapsedIconColor: Colors.white38,
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              children: [
                SizedBox(
                  height: 420,
                  child: AdminView(
                    client: widget.client,
                    savedKey: _adminKey,
                    onKey: (key) async {
                      setState(() => _adminKey = key);
                      final prefs = await SharedPreferences.getInstance();
                      // ⚠️ On the device only. *The server never stores a password on a client's
                      // behalf*, and this one is typed, not issued.
                      await prefs.setString(_adminKeyPref, key);
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 6),
    child: Text(
      text.toUpperCase(),
      style: const TextStyle(
        color: Colors.white38,
        fontSize: 10,
        letterSpacing: 1.2,
      ),
    ),
  );
}

class _ManagerIdRow extends StatefulWidget {
  const _ManagerIdRow({
    required this.managerId,
    required this.squadName,
    required this.onChanged,
  });

  final int managerId;
  final String squadName;
  final ValueChanged<int> onChanged;

  @override
  State<_ManagerIdRow> createState() => _ManagerIdRowState();
}

class _ManagerIdRowState extends State<_ManagerIdRow> {
  late final TextEditingController _controller = TextEditingController(
    text: '${widget.managerId}',
  );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final id = int.tryParse(_controller.text.trim());
    if (id != null && id > 0) widget.onChanged(id);
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'FPL manager id',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
              // ⭐⭐ The name FPL has for this id. ⚠️ Absent rather than blank when the team has not
              // loaded — *a label with nothing after it reads as a failure, not as "not yet".*
              if (widget.squadName.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 2, right: 8),
                  child: Text(
                    widget.squadName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                ),
            ],
          ),
        ),
        SizedBox(
          width: 110,
          height: 34,
          child: TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            textAlign: TextAlign.end,
            onSubmitted: (_) => _submit(),
            style: const TextStyle(color: Colors.white, fontSize: 13),
            decoration: InputDecoration(
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 10,
                vertical: 8,
              ),
              filled: true,
              fillColor: Colors.white10,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(Brand.radiusSm),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
        IconButton(
          onPressed: _submit,
          icon: const Icon(Icons.check, size: 18, color: Colors.white54),
          tooltip: 'Load this team',
        ),
      ],
    ),
  );
}

/// ⚠️⚠️ **The one number FPL will not tell us**, and it changes the advice (ADR-191/228).
/// One selectable pill in the free-transfer row.
///
/// ⭐ Extracted because "Auto" and the digits must look and behave identically — ⚠️ *a second copy of a
/// control is where the two quietly stop matching.*
class _Chip extends StatelessWidget {
  const _Chip({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    behavior: HitTestBehavior.opaque,
    child: Container(
      height: 30,
      // ⚠️ **Width by content, not a fixed 30.** "Auto" does not fit a square, and a clipped control
      // reads as a rendering bug rather than a word.
      constraints: const BoxConstraints(minWidth: 30),
      padding: const EdgeInsets.symmetric(horizontal: 7),
      margin: const EdgeInsets.only(left: 4),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: selected ? Brand.purple : Colors.white10,
        borderRadius: BorderRadius.circular(Brand.radiusSm),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: selected ? Colors.white : Colors.white54,
          fontSize: 12.5,
        ),
      ),
    ),
  );
}

class _FreeTransfersRow extends StatelessWidget {
  const _FreeTransfersRow({
    required this.value,
    required this.effective,
    required this.source,
    required this.onChanged,
    this.implied,
  });

  /// The manager's override, or null while the app works it out.
  final int? value;

  /// The number every other screen is using.
  final int effective;

  /// Where [effective] came from: `you` · `history` · `default` (ADR-321).
  final String source;

  /// `null` puts it back to automatic.
  final ValueChanged<int?> onChanged;

  /// What the manager's own transfer history implies they hold, or null if it could not be checked.
  final int? implied;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ⚠️⚠️ **The chips moved onto their own line when "Auto" joined them.** Label + seven pills
        // overflowed by 30px on a phone — ⭐ *a seventh option is not a copy problem, it is one option
        // more than the row was built for*, and squeezing "Auto" down to fit would have made the word
        // unreadable to keep a layout that had already run out.
        const Row(
          children: [
            Text(
              'Free transfers',
              style: TextStyle(color: Colors.white, fontSize: 14),
            ),
            HelpDot('free_transfers', size: 13),
          ],
        ),
        const SizedBox(height: 6),
        // ⚠️ `Wrap`, not `Row`: it survives a larger text scale and a narrower phone without either
        // clipping or shrinking the targets below a thumb.
        Wrap(
          spacing: 0,
          runSpacing: 4,
          children: [
            // ⭐⭐ **"Auto" is a state, not the absence of one.** Without it, correcting the number once
            // was a one-way door: the app would never trust the history again, including after the
            // deadline that made the history right. ⚠️ It is also the *normal* state, so it comes first.
            _Chip(
              label: 'Auto',
              selected: value == null,
              onTap: () => onChanged(null),
            ),
            for (var n = 0; n <= 5; n++)
              _Chip(
                label: '$n',
                // ⚠️ **Selected on the override, never on the effective number.** Highlighting `2`
                // because history says 2 would make "Auto" and "2" look like the same choice — ⭐ *and
                // the difference between them is the whole point: one keeps updating, the other does
                // not.*
                selected: n == value,
                onTap: () => onChanged(n),
              ),
          ],
        ),
        // ⚠️⚠️ **This caption used to say FPL does not publish it, so the app has to ask.** That was
        // half true and is now the wrong half: the number is **derivable** from the transfers you have
        // made (ADR-318). ⭐ *A caption that explains a limitation the app no longer has teaches people to
        // distrust the ones it does.*
        Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Text(
            // ⭐⭐⭐ **It states the number in force and where it came from** (ADR-321). Three screens
            // were showing three numbers and none of them said which week or which direction, so a
            // tester asked *"is that 1/3 used?"* — ⚠️ *two numbers on one screen is a question, not an
            // answer.*
            switch (source) {
              'you' =>
                'Using your $effective — every screen plans on this. '
                    '${implied == null ? '' : 'Your transfer history says $implied. '}'
                    'Tap Auto to go back to working it out.',
              'history' =>
                'Worked out from your transfer history: you have $effective free '
                    'transfer${effective == 1 ? '' : 's'} for the coming deadline. Moves you make before '
                    'it are not visible until it passes — set the number yourself if that is out of date.',
              _ =>
                'FPL does not publish this directly and your history could not be read, so the app is '
                    'assuming $effective. Set it yourself if that is wrong.',
            },
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 10.5,
              height: 1.45,
            ),
          ),
        ),
      ],
    ),
  );
}

class _Fact extends StatelessWidget {
  const _Fact({required this.label, required this.value, this.note});

  final String label;
  final String value;
  final String? note;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      children: [
        Expanded(
          child: Text(
            label,
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
        ),
        if (note != null)
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Text(
              note!,
              style: const TextStyle(color: Colors.white24, fontSize: 10.5),
            ),
          ),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 13.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    ),
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
    child: Text(
      text,
      style: TextStyle(
        color: muted ? Colors.white24 : Colors.white54,
        fontSize: 11.5,
        height: 1.5,
        fontStyle: italic ? FontStyle.italic : FontStyle.normal,
      ),
    ),
  );
}

/// Where the API is — ⭐ **the field that got the app off this machine** (ADR-239).
///
/// ⭐⭐ **The check is the feature, not the text box.** Anyone can store a string; what a person needs on a
/// phone is to be told *which* of the several indistinguishable failures they are looking at, because two
/// of them are a sleeping laptop rather than a broken app.
class _ServerRow extends StatefulWidget {
  const _ServerRow({required this.baseUrl, required this.onServer});

  final String baseUrl;
  final Future<void> Function(String) onServer;

  @override
  State<_ServerRow> createState() => _ServerRowState();
}

class _ServerRowState extends State<_ServerRow> {
  late final TextEditingController _controller = TextEditingController(
    text: widget.baseUrl,
  );
  bool _checking = false;
  ReachResult? _result;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// ⚠️⚠️ **It checks before it saves.** Storing an address that does not answer would leave the app
  /// broken on its next launch with no way back except reinstalling — ⭐ *a setting that can brick the
  /// screen it is set from has to prove itself first.* "Use anyway" is there for the case where the server
  /// is simply not up yet, and it says so.
  Future<void> _check({bool thenSave = true}) async {
    setState(() {
      _checking = true;
      _result = null;
    });
    final outcome = await reach(_controller.text);
    if (!mounted) return;
    setState(() {
      _checking = false;
      _result = outcome;
    });
    if (outcome.ok && thenSave) await widget.onServer(_controller.text);
  }

  Future<void> _useAnyway() => widget.onServer(_controller.text);

  Future<void> _reset() async {
    await Server.forget();
    _controller.text = kDefaultBaseUrl;
    await _check();
  }

  @override
  Widget build(BuildContext context) {
    final r = _result;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _controller,
          keyboardType: TextInputType.url,
          autocorrect: false,
          enableSuggestions: false,
          onSubmitted: (_) => _check(),
          style: const TextStyle(color: Colors.white, fontSize: 13.5),
          decoration: InputDecoration(
            hintText: kDefaultBaseUrl,
            hintStyle: const TextStyle(color: Colors.white24, fontSize: 12.5),
            isDense: true,
            filled: true,
            fillColor: Colors.white10,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(Brand.radiusSm),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        const Padding(
          padding: EdgeInsets.only(top: 6),
          child: Text(
            'On a phone this is your Mac’s address on the Wi-Fi — something like '
            'http://192.168.1.20:8078, not localhost. A phone’s localhost is the phone.',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 10.5,
              height: 1.45,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Row(
            children: [
              TextButton(
                onPressed: _checking ? null : () => _check(),
                style: TextButton.styleFrom(
                  backgroundColor: Brand.purple,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: Colors.white10,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 8,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                  ),
                ),
                child: Text(
                  _checking ? 'Checking…' : 'Check and use',
                  style: const TextStyle(fontSize: 12.5),
                ),
              ),
              const SizedBox(width: 8),
              TextButton(
                onPressed: _checking ? null : _reset,
                style: TextButton.styleFrom(foregroundColor: Colors.white54),
                child: const Text('Reset', style: TextStyle(fontSize: 12.5)),
              ),
            ],
          ),
        ),
        if (r != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              r.message,
              style: TextStyle(
                color: r.ok ? Brand.good : Brand.warn,
                fontSize: 11.5,
                height: 1.5,
              ),
            ),
          ),
        // ⭐ Offered only when the address itself is fine and nothing answered — never for a typo, where
        // saving it is simply the wrong thing to do.
        if (r != null && r.reach == Reach.refused)
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton(
              onPressed: _useAnyway,
              style: TextButton.styleFrom(
                foregroundColor: Brand.purpleLight,
                padding: const EdgeInsets.symmetric(vertical: 4),
              ),
              child: const Text(
                'Use it anyway — the server is not up yet',
                style: TextStyle(fontSize: 11.5),
              ),
            ),
          ),
      ],
    );
  }
}
