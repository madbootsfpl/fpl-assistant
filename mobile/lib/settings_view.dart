/// Settings — the things you set once and then forget (ADR-238).
///
/// ⭐ Split out of More so that More can be a **directory**. The Hub's works because every row is a
/// destination with a one-line description; ours could not be, because half of it was controls.
///
/// ⚠️ **Free transfers lives here, two taps from the pitch.** That is a real cost and an acceptable one:
/// it changes at most weekly, where the screens it affects are opened daily. ⭐ *Frequency decides depth,
/// the same rule that ordered the bottom bar* (ADR-230).
library;

import 'package:flutter/material.dart';

import 'server.dart';

import 'api/models.dart';
import 'brand.dart';

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
    required this.baseUrl,
    required this.onServer,
    super.key,
  });

  final MyTeam team;
  final int managerId;
  final int freeTransfers;
  final ValueChanged<int> onManagerId;
  final ValueChanged<int> onFreeTransfers;

  /// Where the API is. ⭐ Runtime state, not a `const` — see [Server].
  final String baseUrl;
  final Future<void> Function(String) onServer;

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends State<SettingsView> {
  late int _freeTransfers = widget.freeTransfers;

  /// ⭐ Changing whose team this is **leaves the screen**. The facts below are this manager's, captured on
  /// the way in; staying here would show you one manager's name over another's bank balance.
  void _manager(int id) {
    widget.onManagerId(id);
    Navigator.of(context).maybePop();
  }

  @override
  Widget build(BuildContext context) {
    final team = widget.team;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
      children: [
        const _Heading('Your team'),
        _ManagerIdRow(managerId: widget.managerId, onChanged: _manager),
        _FreeTransfersRow(
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

        const _Heading('Server'),
        _ServerRow(baseUrl: widget.baseUrl, onServer: widget.onServer),

        const _Heading('On the web'),
        const _Note(
          'madboots.streamlit.app carries the research surfaces: the fixture ticker, Team DNA and '
          'Trending — and the market-wide view of Signals, where this app shows only your own squad.',
        ),
        const _Note(
          // ⭐ The positioning, said out loud rather than implied by absence. Someone who cannot find
          // Team DNA should learn that it is a decision, not an oversight.
          'That split is deliberate. This app is the decision layer — what to do this week, and what a '
          'move is worth. The web app stays the exploration layer, where a bigger screen earns its keep.',
          muted: true,
        ),

        const _Heading('About'),
        const _Note(Brand.mantra, italic: true),
        const _Note(Brand.disclaimer, muted: true),
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
  const _ManagerIdRow({required this.managerId, required this.onChanged});

  final int managerId;
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
        const Expanded(
          child: Text(
            'FPL manager id',
            style: TextStyle(color: Colors.white, fontSize: 14),
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
class _FreeTransfersRow extends StatelessWidget {
  const _FreeTransfersRow({required this.value, required this.onChanged});

  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                'Free transfers',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
            for (var n = 0; n <= 5; n++)
              GestureDetector(
                onTap: () => onChanged(n),
                behavior: HitTestBehavior.opaque,
                child: Container(
                  width: 30,
                  height: 30,
                  margin: const EdgeInsets.only(left: 4),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: n == value ? Brand.purple : Colors.white10,
                    borderRadius: BorderRadius.circular(Brand.radiusSm),
                  ),
                  child: Text(
                    '$n',
                    style: TextStyle(
                      color: n == value ? Colors.white : Colors.white54,
                      fontSize: 12.5,
                    ),
                  ),
                ),
              ),
          ],
        ),
        const Padding(
          padding: EdgeInsets.only(top: 5),
          child: Text(
            'FPL does not publish this, so the app has to ask. The week’s plan recommends this many '
            'moves.',
            style: TextStyle(
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
