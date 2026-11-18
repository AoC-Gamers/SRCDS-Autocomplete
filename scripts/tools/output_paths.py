"""Validate destructive build/staging destinations before any filesystem mutation."""
import argparse
import os
from pathlib import Path


def managed_output(root, path, protected=()):
    root = root.resolve()
    target = Path(os.path.abspath(path))
    areas = (root / '.build', root / 'dist')
    if not any(target != area and target.is_relative_to(area) for area in areas):
        raise ValueError('Build/stage output must be a child of repository .build/ or dist/')
    current = target
    while current != root:
        if current.is_symlink():
            raise ValueError(f'Linked output path: {target}')
        current = current.parent
    if target.exists() and not target.is_dir():
        raise ValueError(f'Output is not a directory: {target}')
    for source in protected:
        source = Path(source).resolve()
        if source == target or source.is_relative_to(target) or target.is_relative_to(source):
            raise ValueError(f'Output overlaps an input/dependency directory: {target}')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('protected', nargs='*', type=Path)
    args = parser.parse_args()
    try:
        target = managed_output(args.root, args.output, args.protected)
    except ValueError as error:
        parser.error(str(error))
    print(target)


if __name__ == '__main__':
    main()
