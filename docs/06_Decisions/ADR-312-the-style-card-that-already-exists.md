# ADR-312 — The style card that already exists

**Date:** 2026-09-27
**Status:** ✅ **Built.** All four decided by the owner 2026-09-27; the sweep landed the same day.
**From:** the owner's list — *"Did we ever build a style card? We are not consistent across the apps, web &
Landing page. for example MADBOOTS (which is correct) vs…"*

---

## The answer to the question asked

**Yes — `src/web_streamlit/brand.py`.** It holds the name, tagline, disclaimer, palette, spacing scale,
mantra, descriptor and the badge assets, and it already states the rule the owner is asking about, in its
own comment on line 15:

> `NAME = "MADBOOTS"` — *the display name — **one word**; the wordmark is two-tone (MAD/BOOTS)*

⭐⭐ It is even **enforced onto one surface**: `scripts/generate_brand_dart.py` writes `mobile/lib/brand.dart`
and `tests/test_brand_dart.py` regenerates and compares, so a palette change that has not reached the phone
**fails the Python suite.**

⭐⭐⭐ **So the finding is not "there is no style card." It is that the style card is enforced on one surface
of four, and every unenforced surface has drifted.** 📌 The fifth time this month a thing turned out to
exist and not be reachable — after the swipe, Chatter, `converse()`, and the team name.

## The drift, measured

### 🔴 The name has four spellings, and a phone shows three of them

| where | what it says |
|---|---|
| `brand.py`, `brand.dart`, in-app wordmark, web `<title>` | **MADBOOTS** ✅ |
| `AndroidManifest.xml` `android:label`, iOS `CFBundleDisplayName` | **Madboots** — ⚠️ *this is the name under the icon on a home screen* |
| iOS `CFBundleName`, `pubspec.yaml` `name:` | **madboots** |
| the logo artwork (`boots.png`, the favicon art) | **MAD BOOTS** — two words |

⚠️ Also still there: `pubspec.yaml`'s `description: "A new Flutter project."` — the last of the Flutter
defaults, after the five icons and the manifest.

### 🔴 The wordmark is hand-built in six places and no two agree

| surface | MAD colour | weight | size | letter-spacing | italic |
|---|---|---|---|---|---|
| `brand.py` (Streamlit) | `PURPLE` #8B2FC9 | 900 | caller's | **−.01em** | **yes** |
| `site/index.html` | `--purple-lt` #B45CF0 | 900 | 1.15rem | **−.01em** | **yes** |
| `main.dart` | `purpleLight` | 700 | 15 | **+.5** | no |
| `welcome_view.dart` | `purpleLight` | 700/800 | 17/24 | **+1** | no |
| `pitch.dart` | `purpleLight` | 700 | 10.5 | **+.3** | no |
| `boot_battle.dart` | `purpleLight` | 700/800 | 10.5/11 | **+.3 / +1.2** | no |

⭐⭐ **The web tightens the word and the app loosens it** — opposite directions from the same brand — and
the app is **upright where the web is italic**, which is the difference a reader actually notices.

### 🟠 The palette has drifted and grown

- **`ink` disagrees**: `brand.py` **#17131F**, the landing page **#0c0a12**.
- **Five landing-page colours exist nowhere central**: `--bg`, `--panel`, `--text`, `--muted`, and the
  semantic `--green` / `--yellow`. ⚠️ `ACCENT_TEAL` exists in `brand.py` and nowhere on the landing page.

## ✅ The four decisions, as taken

| | decision | what shipped |
|---|---|---|
| **1** | **`PURPLE_LT` on dark, `PURPLE` on light** | `MAD_ON_DARK` / `MAD_ON_LIGHT` in `brand.py`; the ground picks the shade |
| **2** | **Italic** | `WORDMARK_ITALIC/WEIGHT/TRACKING_EM` — the app was the odd one out and moved |
| **3** | **`MADBOOTS`** under the icon | `android:label`, both iOS keys |
| **4** | **Art exempt, written down** | `brand.LOGO_ART_EXEMPT` |

⚠️ **One exception the sweep found and kept:** `pubspec.yaml`'s `name: madboots` stays lowercase. It is the
**Dart package identifier**, appears in every `package:madboots/…` import, and must be a lowercase
identifier — ⭐ *a language rule, not drift*, recorded beside it so the next person does not "fix" it and
take the build with them.

## The decisions as they were put

**1 — Which purple carries MAD?** `brand.py` defaults to **#8B2FC9**; the landing page and all four app
sites use **#B45CF0**. ⭐ *Recommend `PURPLE_LT` on dark grounds and `PURPLE` on light* — which is what
`mark_html`'s `purple` parameter was already built to allow, so this is naming an existing capability as
the rule rather than changing anything.

**2 — Italic or upright?** The web is **italic 900**, the app **upright 700**. ⭐ *Recommend italic*: it is
the distinctive form, it matches the logo art's energy, and the app is the odd one out rather than the
majority.

**3 — What goes under the icon on a home screen?** Today **"Madboots"**. ⭐ *Recommend `MADBOOTS`* for one
spelling everywhere — ⚠️ but this one is genuinely the owner's taste, because all-caps under an icon reads
louder than title case and it is the single most-seen instance of the name.

**4 — Is the logo art exempt?** It says **MAD BOOTS**, two words, against a one-word rule. ⭐ *Recommend
exempt and say so*: a logo is a drawn mark, not typeset text, and redrawing it is real work for a rule that
only applies to the word when it is set in type. ⚠️ *But the exemption has to be written down, or it reads
as the same drift as everything else* — which is exactly how it read to the owner.

## What the sweep would be, once those are settled

⭐ **Not "fix six files" — remove the ability to drift**, the same shape that already works for Dart:

1. **One wordmark per surface, not six.** A `Brand.wordmark()` widget in Dart replacing four hand-built
   `Text.rich`es; `brand.wordmark_html()` already exists for Python; the landing page already has `.brand`.
2. **Generate the landing page's CSS variables from `brand.py`**, the way `brand.dart` is generated, with
   the same regenerate-and-compare test. ⚠️ That is what stopped the Dart palette drifting and is the only
   reason `ink` drifted on the page and not on the phone.
3. **Promote the five orphan colours** into `brand.py` (or delete them), so "the palette" is one list.
4. **One spelling**, applied to `android:label`, both iOS keys and `pubspec.yaml` — plus that `description`.
5. **A test that fails on a hand-built wordmark**, so a seventh cannot appear.

## Consequences

- ⭐ **No new design work.** Every value in the proposal already exists somewhere; the question is only
  which existing value wins.
- 📌 **Decides item ⑥ (player-page icons) for free** — the owner's next list item should be chosen against
  this palette, which is why it is gated first.
- ⚠️ **Stated cost:** generating the landing page's CSS makes `site/index.html` partly a build output, and
  a hand edit to those variables would be overwritten. That is the same trade `brand.dart` already makes,
  and the reason it has not drifted.

---

## What actually shipped

- **One wordmark.** `mobile/lib/wordmark.dart` replaces four hand-built copies. ⭐ Tracking is declared in
  **em** so it scales with the size — *a fixed letter-spacing is why six copies read differently at 10.5pt
  and at 24pt.* ⚠️ `welcome_view`'s was **two plain `Text`s in a Row**, so the colour split was a *layout*
  rather than a word: it could not carry tracking across the break, and a screen reader read the product as
  two fragments.
- **A generated landing-page palette.** `scripts/generate_site_palette.py` + `tests/test_site_palette.py`,
  the same regenerate-and-compare that has kept `brand.dart` honest. ⭐ Only the brand block is generated —
  `--bg2`, `--line` and the font stacks stay hand-written, because *a generator that owns the whole file
  makes every edit a merge conflict with a script, and the next person simply stops running it.*
- **A generated share card.** `scripts/generate_og_image.py` renders `og-image.png` **through Chrome**,
  because the wordmark is Arial Black *italicised by synthesis* — there is no Arial Black Italic file, and
  ⚠️ *the asset a link shows is the worst place for an approximation of the brand.*
- **One spelling** across `android:label` and both iOS keys, plus the last two Flutter defaults
  (`pubspec`'s description, `mobile/README.md`).

## ⚠️ A five-minute mistake worth recording

Promoting the landing page's colours, I added `TEXT` and `MUTED` to `brand.py` — which **already defines
both**, as the *light* theme's ink. Streamlit runs on white; the landing page and the phone run on ink. The
later assignment silently won and my values vanished. ⭐⭐ *Two surfaces with opposite grounds cannot share
one unqualified name for "the text colour"* — they are `DARK_TEXT` / `DARK_MUTED` now.

⭐ It also caught a second error the same minute: I had changed `mark_html`'s default purple to the
dark-ground shade, which would have put `PURPLE_LT` on Streamlit's **white** pages. The default is
`MAD_ON_LIGHT`; the two dark-band callers ask for the other by name.

## Guards

`test_brand_dart.py` gains three: **no file but `wordmark.dart` may contain `'MAD'` and `'BOOTS'`** (a
seventh copy fails the suite — mutation-tested by reinstating one), the widget must read its setting from
the generated tokens (*moving a hard-coded value into a function does not stop it being hard-coded*), and
the launcher labels must be `brand.NAME`. `test_site_palette.py` adds four more, including the ink that
drifted, by name.

**2854 Python · 458 Dart.**
