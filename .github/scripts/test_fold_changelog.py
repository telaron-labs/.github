import tempfile
import unittest
from pathlib import Path

import fold_changelog as f

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- Old line
  continued.

## [v0.1.0] - 2026-01-01

### Added

- Earlier
"""


class FoldTest(unittest.TestCase):
    def test_merges_in_canonical_order_and_empties_unreleased(self):
        new, body = f.fold(CHANGELOG, ["### Fixed\n\n- A fix\n", "### Added\n\n- New thing\n"], "v0.2.0", "2026-02-02")
        self.assertIn("## [Unreleased]\n\n## [v0.2.0] - 2026-02-02\n\n### Added\n\n- Old line\n  continued.\n- New thing\n\n### Fixed\n\n- A fix\n", new)
        self.assertIn("## [v0.1.0] - 2026-01-01", new)
        self.assertTrue(body.startswith("### Added"))

    def test_nothing_to_release_fails(self):
        with self.assertRaises(ValueError):
            f.fold("## [Unreleased]\n\n## [v0.1.0] - x\n", [], "v0.2.0", "2026-02-02")

    def test_stray_text_fails(self):
        with self.assertRaises(ValueError):
            f.parse("### Added\n\nno bullet\n")

    def test_cli_deletes_fragments(self):
        import subprocess, sys
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CHANGELOG.md").write_text(CHANGELOG)
            (root / "changelog.d").mkdir()
            (root / "changelog.d" / "README.md").write_text("keep")
            (root / "changelog.d" / "b.md").write_text("### Fixed\n\n- x\n")
            subprocess.run([sys.executable, str(Path(__file__).with_name("fold_changelog.py")), "v0.2.0", "2026-02-02", "--root", d], check=True, capture_output=True)
            self.assertFalse((root / "changelog.d" / "b.md").exists())
            self.assertTrue((root / "changelog.d" / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
