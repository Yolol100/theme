"""Fail-closed admission of one exact WordPress theme ZIP for isolated QA."""
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path
from pathlib import PurePosixPath

SHA = re.compile(r"[0-9a-f]{64}\Z")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,99}\Z")
MAX_ARCHIVE = 50 * 1024 * 1024
MAX_UNPACKED = 150 * 1024 * 1024
MAX_ENTRIES = 5000


def inspect(path: Path, expected_sha256: str, expected_slug: str) -> dict:
    if not SHA.fullmatch(expected_sha256) or not SLUG.fullmatch(expected_slug):
        raise ValueError("Expected SHA-256 or theme slug is invalid")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Archive is missing, symlinked or too large")
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected_sha256:
        raise ValueError("Exact ZIP SHA-256 does not match approval")
    unpacked, names = 0, set()
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ENTRIES:
            raise ValueError("Invalid archive entry count")
        for entry in entries:
            name = entry.filename
            components = PurePosixPath(name).parts
            if (not name or name.startswith("/") or "\\" in name or
                any(c in ("", ".", "..") for c in name.rstrip("/").split("/")) or
                any(ord(c) < 32 for c in name) or
                not components or components[0] != expected_slug):
                raise ValueError("Unsafe archive path or unexpected theme root")
            normalized = name.rstrip("/").casefold()
            if normalized in names:
                raise ValueError("Duplicate case-insensitive archive path")
            names.add(normalized)
            mode = (entry.external_attr >> 16) & 0xFFFF
            filetype = stat.S_IFMT(mode)
            if filetype not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Links and special archive files are forbidden")
            if entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("Encrypted or unsupported archive entry")
            unpacked += entry.file_size
            if unpacked > MAX_UNPACKED:
                raise ValueError("Unpacked archive exceeds safety limit")
            if entry.file_size > 1_000_000 and entry.file_size > max(1, entry.compress_size) * 150:
                raise ValueError("Suspicious archive compression ratio")
        if archive.testzip() is not None:
            raise ValueError("Archive CRC failed")
    stylesheet = f"{expected_slug}/style.css".casefold()
    classic = f"{expected_slug}/index.php".casefold() in names
    block = all(f"{expected_slug}/{p}".casefold() in names
                for p in ("theme.json", "templates/index.html"))
    if stylesheet not in names or not (classic or block):
        raise ValueError("Missing WordPress theme header or classic/block entrypoint")
    return {"status": "PASS", "scope": "archive-validation-only", "theme_slug": expected_slug,
            "theme_type": "block" if block else "classic", "zip_sha256": actual,
            "entry_count": len(entries), "unpacked_bytes": unpacked,
            "wordpress_activation": "NOT_RUN", "production_approved": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = inspect(args.zip, args.sha256, args.slug)
        code = 0
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        receipt = {"status": "FAIL", "scope": "archive-validation-only",
                   "reason": str(exc), "wordpress_activation": "NOT_RUN",
                   "production_approved": False}
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"External ZIP validation: {receipt['status']}")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
