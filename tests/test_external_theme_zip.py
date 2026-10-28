"""Positive and adversarial ZIP validation without WordPress or network."""
import hashlib
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_external_theme_zip import inspect


class ThemeZipAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "sample.zip"

    def archive(self, names=None):
        names = names if names is not None else {
            "sample/style.css": "/*\nTheme Name: Sample\n*/",
            "sample/theme.json": "{}", "sample/templates/index.html": "<h1>Welcome</h1>"}
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, value in names.items():
                z.writestr(name, value)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_block_theme_passes_without_activation_claim(self):
        r = inspect(self.path, self.archive(), "sample")
        self.assertEqual((r["status"], r["theme_type"], r["wordpress_activation"]),
                         ("PASS", "block", "NOT_RUN"))
        self.assertFalse(r["production_approved"])

    def test_classic_theme_passes(self):
        sha = self.archive({"sample/style.css": "/*\nTheme Name: Sample\n*/", "sample/index.php": "<?php ?>"})
        self.assertEqual(inspect(self.path, sha, "sample")["theme_type"], "classic")

    def test_malformed_theme_header_is_rejected_before_runtime(self):
        sha = self.archive({"sample/style.css": "Not a WordPress header",
                            "sample/index.php": "<?php ?>"})
        with self.assertRaisesRegex(ValueError, "Theme Name header"):
            inspect(self.path, sha, "sample")

    def test_case_sensitive_theme_paths_are_required(self):
        sha = self.archive({"sample/STYLE.CSS": "/*\nTheme Name: Sample\n*/",
                            "sample/index.php": "<?php ?>"})
        with self.assertRaisesRegex(ValueError, "exact-case"):
            inspect(self.path, sha, "sample")

    def test_wrong_sha_fails_closed(self):
        self.archive()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            inspect(self.path, "0" * 64, "sample")

    def test_invalid_sha_fails(self):
        with self.assertRaises(ValueError):
            inspect(self.path, "main", "sample")

    def test_parent_traversal_fails(self):
        sha = self.archive({"sample/../escape.php": "bad", "sample/style.css": "ok",
                            "sample/index.php": "ok"})
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            inspect(self.path, sha, "sample")

    def test_second_theme_root_fails(self):
        sha = self.archive({"sample/style.css": "ok", "sample/index.php": "ok",
                            "other/secret.php": "x"})
        with self.assertRaisesRegex(ValueError, "unexpected theme root"):
            inspect(self.path, sha, "sample")

    def test_case_insensitive_duplicate_fails(self):
        sha = self.archive({"sample/style.css": "x", "sample/STYLE.CSS": "y",
                            "sample/index.php": "ok"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            inspect(self.path, sha, "sample")

    def test_missing_entrypoint_fails(self):
        sha = self.archive({"sample/style.css": "x"})
        with self.assertRaisesRegex(ValueError, "entrypoint"):
            inspect(self.path, sha, "sample")

    def test_root_slug_must_match(self):
        sha = self.archive()
        with self.assertRaisesRegex(ValueError, "unexpected theme root"):
            inspect(self.path, sha, "different")

    def test_symlink_in_zip_fails(self):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("sample/style.css", "x")
            z.writestr("sample/index.php", "<?php")
            info = zipfile.ZipInfo("sample/link.php")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, "../../private")
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Links"):
            inspect(self.path, sha, "sample")

    def test_backslash_path_fails(self):
        sha = self.archive({"sample\\style.css": "x", "sample/index.php": "ok"})
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            inspect(self.path, sha, "sample")

    def test_archive_not_the_file_claimed_fails(self):
        sha = self.archive()
        self.path.write_bytes(self.path.read_bytes() + b"tampered")
        with self.assertRaises(ValueError):
            inspect(self.path, sha, "sample")


if __name__ == "__main__":
    unittest.main()
