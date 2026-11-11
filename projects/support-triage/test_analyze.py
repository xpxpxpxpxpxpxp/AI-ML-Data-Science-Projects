"""Focused checks for provenance and aggregate reconciliation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402


class SavedOutputTests(unittest.TestCase):
    def test_published_report_rebuilds_exactly(self):
        data = analyze.extract()
        self.assertEqual(data["total"], 21)
        self.assertEqual(data["priority"], {"High": 20, "Medium": 1})
        self.assertEqual(data["time_worded"], 10)
        self.assertEqual(analyze.render(data), analyze.REPORT.read_text(encoding="utf-8"))

    def test_archive_change_requires_review(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "changed.ipynb"
            source.write_bytes(analyze.ARCHIVE.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "archive hash changed"):
                analyze.extract(source)

    def test_cross_tab_mismatch_is_rejected(self):
        notebook = json.loads(analyze.ARCHIVE.read_text(encoding="utf-8"))
        lines = notebook["cells"][41]["outputs"][0]["data"]["text/plain"]
        notebook["cells"][41]["outputs"][0]["data"]["text/plain"] = [
            line.replace("High         6", "High         5") for line in lines
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "changed.ipynb"
            source.write_text(json.dumps(notebook), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cross-tab does not reconcile"):
                analyze.extract(source, verify_hash=False)


if __name__ == "__main__":
    unittest.main()
