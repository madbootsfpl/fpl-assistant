"""No signing material may ever be tracked by git (ADR-278).

⚠️⚠️ **This nearly shipped.** A keystore backed up to `backup/` in the repository root sat outside
Flutter's `mobile/android/.gitignore`, and `git add -A` would have committed the app's **private signing
key** to a public remote.

⭐ The private key is the app's identity: whoever holds it can publish an update that Android accepts as
genuine, for every device the app is installed on. ⚠️ *And a "backup" inside the repository is not a
backup — it is the same disk, plus a way to publish it.*

⭐⭐ **A rule in a subdirectory's ignore file protects that subdirectory.** The template's rule was
correct and simply did not reach where the file was put — *an ignore rule is only as wide as the
directory it lives in*, which is the same shape as ADR-261's hand-maintained `_CORE` list.
"""

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: ⚠️ Extensions, not names. A keystore called `backup.jks` and one called `madboots-release.jks` are
#: the same risk, and nobody will remember to add the second name to a list.
SECRET_SUFFIXES = (".jks", ".keystore", ".p12", ".pepk")
SECRET_NAMES = ("key.properties",)


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def test_no_keystore_or_key_properties_is_tracked():
    offenders = [
        f for f in tracked_files()
        if f.endswith(SECRET_SUFFIXES) or pathlib.Path(f).name in SECRET_NAMES
    ]
    assert not offenders, (
        f"signing material is tracked by git: {offenders}. "
        "Remove it from the index and rotate the key — a committed keystore is a published one."
    )


def test_the_ignore_rule_reaches_the_whole_tree():
    """⚠️ Not just `mobile/android/`. ⭐ *An ignore rule is only as wide as the directory it lives in*,
    and the file that nearly leaked was in the repository root."""
    probes = [
        "backup/anything.jks",
        "some/deep/path/release.keystore",
        "key.properties",
        "mobile/android/key.properties",
    ]
    for probe in probes:
        result = subprocess.run(["git", "check-ignore", probe], cwd=ROOT, capture_output=True)
        assert result.returncode == 0, f"{probe} is NOT ignored — it would be committed"


def test_the_example_file_carries_no_real_password():
    """⭐ A template that ships a working password is not a template."""
    example = ROOT / "mobile" / "android" / "key.properties.example"
    assert example.exists(), "the example is how anyone knows what key.properties needs"
    text = example.read_text()
    for line in ("storePassword", "keyPassword"):
        value = next(row.split("=", 1)[1] for row in text.splitlines() if row.startswith(line))
        assert value.startswith("<") and value.endswith(">"), (
            f"{line} in the example looks like a real value: {value!r}"
        )
