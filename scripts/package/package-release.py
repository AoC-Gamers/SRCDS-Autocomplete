from __future__ import annotations
import argparse
from pathlib import Path
import re
import os
import tempfile
import zipfile
from artifact_contract import validate_tree, validate_zip, verify_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--basename', required=True)
    parser.add_argument('--artifact-dir')
    parser.add_argument('--platform', required=True, choices=['linux', 'windows'])
    args = parser.parse_args()
    if not re.fullmatch(r'srcds-autocomplete-[A-Za-z0-9][A-Za-z0-9.+-]{0,80}-'+args.platform, args.basename) or '..' in args.basename:
        raise ValueError('Unsafe or mismatched release basename')
    root = Path(args.root).resolve()
    artifact = Path(args.artifact_dir).resolve() if args.artifact_dir else root/'dist/sourcemod/artifact'
    files = validate_tree(artifact, root, args.platform)
    verify_receipt(artifact, root, args.platform)
    release = root/'dist/release'
    release.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(suffix='.zip', dir=release)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for name in sorted(files):
                z.writestr(name, files[name])
        if validate_zip(temporary, root, args.platform) != files:
            raise ValueError('ZIP differs from staged product')
        os.replace(temporary, release/(args.basename+'.zip'))
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(f'Validated release ZIP: {release/(args.basename+".zip")}')


if __name__ == '__main__':
    main()
