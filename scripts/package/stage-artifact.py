from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from output_paths import managed_output
from artifact_contract import document_bytes, expected, source_file, validate_tree, verify_receipt, write_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('build_dir')
    parser.add_argument('output_dir', nargs='?')
    parser.add_argument('--platform', required=True, choices=['linux', 'windows'])
    args = parser.parse_args()
    root, source = Path(args.root).resolve(), Path(args.build_dir).resolve()
    target = managed_output(root, args.output_dir or root/'dist/sourcemod/artifact', (source, root/'.deps'))
    # Reject extras before selecting files: never silently filter SDKs or stale outputs.
    raw = source.name == 'package'
    validate_tree(source, root, args.platform, documentation=not raw)
    verify_receipt(source, root, args.platform)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=target.name+'-', dir=target.parent))
    try:
        for name in expected(root, args.platform):
            dst = temporary/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if name.startswith('addons/'):
                shutil.copy2(source_file(source, name), dst, follow_symlinks=False)
            else:
                dst.write_bytes(document_bytes(root, name, args.platform))
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
