"""Synthetic regression tests; no game assets are changed."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from check_ui_assets import check_assets


class AssetChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "assets"
        self.root.mkdir()
        cutout = Image.new("RGBA", (20, 20))
        cutout.paste((255, 255, 255, 255), (4, 4, 16, 16))
        cutout.save(self.root / "cutout.png")
        Image.new("RGB", (20, 20), "white").save(self.root / "opaque.png")
        Image.new("RGBA", (20, 20), (0, 0, 0, 128)).save(self.root / "shadow.png")

    def run_check(self, entries):
        manifest = self.base / "manifest.json"
        manifest.write_text(json.dumps(entries), encoding="utf-8")
        return check_assets(self.root, manifest, self.base / "qa")

    def test_valid_assets_and_source_unchanged(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        report = self.run_check([
            {"name": "cutout", "file": "cutout.png", "alpha_mode": "cutout", "border": [2, 2, 2, 2]},
            {"name": "background", "file": "opaque.png", "alpha_mode": "opaque"},
            {"name": "shadow", "file": "shadow.png", "alpha_mode": "translucent"},
        ])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["warning_count"], 0)
        self.assertTrue((self.base / "qa" / report["review_sheets"][0]).is_file())
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()})

    def test_invalid_alpha_and_border(self):
        report = self.run_check([{"name": "fake-alpha", "file": "opaque.png", "alpha_mode": "cutout", "width": 99, "border": [10, 0, 10, 0]}])
        self.assertEqual(report["error_count"], 4)

    def test_path_missing_duplicate(self):
        report = self.run_check([
            {"name": "same", "file": "cutout.png"},
            {"name": "same", "file": "cutout.png"},
            {"name": "escape", "file": "../outside.png"},
            {"name": "missing", "file": "missing.png"},
        ])
        self.assertEqual(report["error_count"], 4)

    def test_no_report_writes_inside_assets(self):
        manifest = self.base / "manifest.json"
        manifest.write_text('[{"name":"test","file":"cutout.png"}]', encoding="utf-8")
        with self.assertRaises(ValueError):
            check_assets(self.root, manifest, self.root / "qa")


if __name__ == "__main__":
    unittest.main()
