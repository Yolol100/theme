"""Build reproducible theme and source archives from explicit file lists.

Reject unexpected theme files and symlinks before writing either archive.
"""
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
import hashlib
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / 'theme' / 'webactueel-starter'
DIST = ROOT / 'dist'
THEME_ZIP = DIST / 'Webactueel-Block-Starter-1.0.5-STAGING.zip'
SOURCE_ZIP = DIST / 'Webactueel-Block-Starter-Source-1.0.5.zip'

RUNTIME_FILES = frozenset({
    'style.css', 'theme.json', 'LICENSE.txt',
    'templates/index.html', 'templates/page.html', 'templates/single.html',
    'templates/archive.html', 'templates/search.html', 'templates/404.html',
    'parts/header.html', 'parts/footer.html', 'parts/post-list.html',
})
SOURCE_FILES = frozenset({
    '.gitignore', '.github/workflows/ci.yml', 'README.md',
    'docs/QA.md', 'scripts/package.py', 'tests/test_starter.py',
    '.github/workflows/wordpress-runtime.yml',
    'docs/STAGING-ACCEPTANCE.md',
    'docs/77-scenarios.json',
    'docs/staging-acceptance.example.json',
    'scripts/validate_staging_acceptance.py', 'tests/test_staging_acceptance.py',
    'tests/runtime/woo_store_api.py',
    'tests/runtime/axe_audit.py',
    'tests/runtime/admin_smoke.py',
    'tests/runtime/rollback.sh',
    'tests/runtime/compose.yaml', 'tests/runtime/run.sh',
    'tests/runtime/browser_smoke.py', 'tests/runtime/seed_woo.php',
    'docs/ARCHITECTURE.md', 'tests/runtime/acf_smoke.php',
    'tests/runtime/acf_smoke.sh', 'tests/test_acf_contract.py',
})


def file_bytes(base: Path, name: str) -> bytes:
    if not name or '\\' in name or name.startswith('/') or any(
        part in ('.', '..') for part in PurePosixPath(name).parts
    ):
        raise ValueError(f'Unsafe file name: {name!r}')
    path = base
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Cannot package a symlink: {path}')
    if not path.is_file():
        raise FileNotFoundError(f'Required release file is missing: {path}')
    return path.read_bytes()


def build_zip(dest: Path, mapping: dict[str, bytes]) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not mapping or len({key.casefold() for key in mapping}) != len(mapping):
        raise ValueError('Empty archive or case-conflicting filenames')
    with NamedTemporaryFile(dir=dest.parent, prefix='.build-', suffix='.tmp', delete=False) as file:
        temporary = Path(file.name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name, data in sorted(mapping.items()):
                rel = name.rstrip('/')
                if (not rel or rel.startswith('/') or '\\' in rel or
                    '..' in PurePosixPath(rel).parts or '.' in PurePosixPath(rel).parts):
                    raise ValueError(f'Unsafe archive name: {name!r}')
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
                z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() or set(z.namelist()) != set(mapping):
                raise ValueError('Archive has CRC errors or missing entries')
            for name, data in mapping.items():
                if z.read(name) != data:
                    raise ValueError(f'Archive byte mismatch: {name}')
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        os.chmod(temporary, 0o644)
        os.replace(temporary, dest)
        return digest
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    # An ancestor symlink would bypass the checks on files inside THEME.
    # Resolve paths only after proving every component below ROOT is real.
    cursor = ROOT
    for component in THEME.relative_to(ROOT).parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise ValueError(f'Symlinked theme path is forbidden: {cursor}')
    if not THEME.is_dir():
        raise FileNotFoundError('Missing theme directory')
    actual = set()
    for path in THEME.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Theme symlink is forbidden: {path}')
        if path.is_file():
            actual.add(path.relative_to(THEME).as_posix())
    if actual != RUNTIME_FILES:
        raise ValueError(f'Unexpected/missing runtime files: extra={sorted(actual-RUNTIME_FILES)} '
                         f'missing={sorted(RUNTIME_FILES-actual)}')
    theme_map = {'webactueel-starter/' + name: file_bytes(THEME, name) for name in RUNTIME_FILES}
    source_map = {'theme/webactueel-starter/' + name: file_bytes(THEME, name) for name in RUNTIME_FILES}
    source_map.update({name: file_bytes(ROOT, name) for name in SOURCE_FILES})
    theme_sha = build_zip(THEME_ZIP, theme_map)
    source_sha = build_zip(SOURCE_ZIP, source_map)
    (DIST / 'SHA256SUMS.txt').write_text(
        f'{theme_sha}  {THEME_ZIP.name}\n{source_sha}  {SOURCE_ZIP.name}\n'
    )
    print('THEME:', len(theme_map), 'files;', theme_sha)
    print('SOURCE:', len(source_map), 'entries;', source_sha)


if __name__ == '__main__':
    main()
