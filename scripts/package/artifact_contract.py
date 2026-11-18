"""Shared product allowlist, architecture checks and build provenance."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MAP = Path('scripts/package/package-map.json')


def safe_path(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or str(p) != name:
        raise ValueError(f'Unsafe package path: {name}')
    return name


def source_file(root, name):
    root = root.resolve()
    candidate = root / safe_path(name)
    current = candidate
    while current != root:
        if current.is_symlink():
            raise ValueError(f'Linked product source: {name}')
        current = current.parent
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root):
        raise ValueError(f'Missing, special or external product source: {name}')
    return candidate


def manifest_paths(tree, prefix=''):
    paths = set()
    for key, value in tree.items():
        if key == 'files':
            paths.update(safe_path(prefix + name) for name in value)
        elif isinstance(value, dict):
            paths.update(manifest_paths(value, prefix + safe_path(key) + '/'))
        else:
            raise ValueError(f'Unsupported artifact map key: {key}')
    return paths


def validate_documentation_paths(paths):
    for name in paths:
        safe_path(name)
        if name not in {'README.md', 'LICENSE', 'CHANGELOG.md'} and not (name.startswith('docs/') and name.endswith('.md')):
            raise ValueError(f'Not stable product documentation: {name}')


def expected(root, platform, documentation=True):
    if platform not in {'linux', 'windows'}:
        raise ValueError('Platform must be linux or windows')
    data = json.loads((root / MAP).read_text())
    if set(data) != {'build', 'artifact', 'documentation'} or data['build'] != {'extensions': {'root': ['autocomplete']}}:
        raise ValueError('Unsupported package map schema/components')
    suffix = 'so' if platform == 'linux' else 'dll'
    result = {f'addons/sourcemod/extensions/autocomplete.ext.2.l4d2.{suffix}'}
    result.update(manifest_paths(data['artifact']))
    allowed_runtime = {
        f'addons/sourcemod/extensions/autocomplete.ext.2.l4d2.{suffix}',
        'addons/sourcemod/extensions/autocomplete.autoload',
        'addons/sourcemod/gamedata/autocomplete.games.txt',
    }
    if result != allowed_runtime:
        raise ValueError('Map must select the complete owned runtime product only')
    validate_documentation_paths(data['documentation'])
    if documentation:
        result.update(data['documentation'])
    if len({p.casefold() for p in result}) != len(result):
        raise ValueError('Case collision in package map')
    return result


def check_binary(data, platform):
    if platform == 'linux':
        if len(data) < 52 or data[:7] != b'\x7fELF\x01\x01\x01' or struct.unpack_from('<HH', data, 16) != (3, 3):
            raise ValueError('Expected ELF32 little-endian i386 shared object')
    else:
        if len(data) < 64 or data[:2] != b'MZ':
            raise ValueError('Expected PE32 i386 DLL')
        offset = struct.unpack_from('<I', data, 60)[0]
        if (len(data) < offset + 26 or data[offset:offset+4] != b'PE\0\0'
                or struct.unpack_from('<H', data, offset+4)[0] != 0x14c
                or not struct.unpack_from('<H', data, offset+22)[0] & 0x2000
                or struct.unpack_from('<H', data, offset+24)[0] != 0x10b):
            raise ValueError('Expected PE32 i386 DLL')


def inventory(tree):
    if tree.is_symlink() or not tree.is_dir():
        raise ValueError(f'Missing or linked artifact tree: {tree}')
    files = {}
    seen = set()
    for p in tree.rglob('*'):
        name = safe_path(p.relative_to(tree).as_posix())
        if name.casefold() in seen or p.is_symlink():
            raise ValueError(f'Linked path or case collision: {name}')
        seen.add(name.casefold())
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError(f'Special file: {name}')
        files[name] = p.read_bytes()
    return files


def validate_files(files, root, platform, documentation=True):
    wanted = expected(root, platform, documentation)
    if set(files) != wanted:
        raise ValueError(f'Package content mismatch; missing={sorted(wanted-set(files))}; extra={sorted(set(files)-wanted)}')
    for name, data in files.items():
        if name.endswith(('.so', '.dll')):
            check_binary(data, platform)
        elif not name.startswith('addons/'):
            if data != source_file(root, name).read_bytes():
                raise ValueError(f'Stale documentation: {name}')
        elif data != source_file(root, 'extension/autocomplete.autoload' if name.endswith('.autoload') else name).read_bytes():
            raise ValueError(f'Stale runtime resource: {name}')


def validate_tree(tree, root, platform, documentation=True):
    files = inventory(tree)
    validate_files(files, root, platform, documentation)
    return files


def validate_zip(path, root, platform):
    with zipfile.ZipFile(path) as z:
        files = {}
        seen = set()
        for info in z.infolist():
            name = safe_path(info.filename.rstrip('/'))
            mode = info.external_attr >> 16
            if name.casefold() in seen or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}):
                raise ValueError(f'Duplicate or special ZIP member: {name}')
            seen.add(name.casefold())
            if not info.is_dir():
                files[name] = z.read(info)
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
    validate_files(files, root, platform)
    return files


def source_digest(root):
    paths = [root / name for name in ('AMBuilder', 'AMBuildScript', 'PackageScript', 'configure.py', 'Makefile', '.gitattributes')]
    for folder in ('extension', 'addons', 'scripts'):
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def receipt_path(tree):
    return tree.parent/'build-receipt.json' if tree.name == 'package' else tree.parent/(tree.name+'.receipt.json')


def write_receipt(tree, root, platform):
    binaries = {n: hashlib.sha256(d).hexdigest() for n,d in inventory(tree).items() if n.endswith(('.so', '.dll'))}
    receipt = {'sources': source_digest(root), 'platform': platform, 'binaries': binaries}
    database = tree.parent/'compile_commands.json'
    if tree.name == 'package' and database.is_file():
        receipt['compilation_database'] = hashlib.sha256(database.read_bytes()).hexdigest()
    receipt_path(tree).write_text(json.dumps(receipt, indent=2)+'\n')


def verify_receipt(tree, root, platform):
    receipt = json.loads(receipt_path(tree).read_text())
    binaries = {n: hashlib.sha256(d).hexdigest() for n,d in inventory(tree).items() if n.endswith(('.so', '.dll'))}
    wanted = {'sources': source_digest(root), 'platform': platform, 'binaries': binaries}
    database = tree.parent/'compile_commands.json'
    if tree.name == 'package' and database.is_file():
        wanted['compilation_database'] = hashlib.sha256(database.read_bytes()).hexdigest()
    if receipt != wanted:
        raise ValueError('Stale build/stage receipt; rebuild from current sources')
