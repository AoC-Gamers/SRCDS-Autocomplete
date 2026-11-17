"""Delete only managed repository outputs, never external SDKs or sources."""
import argparse
from pathlib import Path
import shutil

p=argparse.ArgumentParser()
p.add_argument('root',type=Path)
p.add_argument('paths',nargs='+',type=Path)
a=p.parse_args()
root=a.root.resolve()
paths=[]
for path in a.paths:
    absolute=path.absolute()
    resolved=absolute.resolve()
    managed=[root/name for name in ('.build','dist','.deps')]
    if not any(resolved==base or resolved.is_relative_to(base) for base in managed) or absolute.is_symlink():
        p.error(f'Refusing to clean unmanaged or linked output: {path}')
    paths.append(absolute)
for path in paths:
    if path.is_dir():shutil.rmtree(path)
    else:path.unlink(missing_ok=True)
