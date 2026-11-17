from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import tempfile
from artifact_contract import expected, validate_tree, verify_receipt, write_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('build_dir')
    parser.add_argument('output_dir', nargs='?')
    parser.add_argument('--platform', required=True, choices=['linux', 'windows'])
    args = parser.parse_args()
    root, source = Path(args.root).resolve(), Path(args.build_dir).resolve()
    target = Path(args.output_dir).absolute() if args.output_dir else root/'dist/sourcemod/artifact'
    if target.is_symlink() or source == target.resolve() or source.is_relative_to(target.resolve()) or target.resolve().is_relative_to(source):
        raise ValueError('Stage source and destination must be separate, unlinked trees')
    # Reject extras before selecting files: never silently filter SDKs or stale outputs.
    raw = source.name == 'package'
    validate_tree(source, root, args.platform, documentation=not raw)
    verify_receipt(source, root, args.platform)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=target.name+'-', dir=target.parent))
    try:
        for name in expected(root, args.platform):
            src = source/name if name.startswith('addons/') else root/name
            dst = temporary/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        validate_tree(temporary, root, args.platform)
        if target.exists():
            shutil.rmtree(target)
        temporary.rename(target)
        write_receipt(target, root, args.platform)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    print(f'Staged validated {args.platform} product: {target}')


if __name__ == '__main__':
    main()
