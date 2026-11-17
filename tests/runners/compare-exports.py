"""Compare ELF target and exported symbol names/types with a prior local ZIP."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import zipfile

p = argparse.ArgumentParser()
p.add_argument('--baseline-zip', required=True, type=Path)
p.add_argument('--current', required=True, type=Path)
a = p.parse_args()


def symbols(binary):
    result = subprocess.check_output(['nm', '-D', '--defined-only', str(binary)], text=True)
    return {tuple(line.split()[-2:]) for line in result.splitlines() if line.strip()}


with tempfile.TemporaryDirectory(prefix='autocomplete-exports-') as directory:
    old = Path(directory)/'baseline.so'
    with zipfile.ZipFile(a.baseline_zip) as z:
        old.write_bytes(z.read('addons/sourcemod/extensions/autocomplete.ext.2.l4d2.so'))
    before, after = old.read_bytes(), a.current.read_bytes()
    if before[:7] != after[:7] or before[16:20] != after[16:20]:
        raise SystemExit('ELF class/encoding/type/machine changed')
    removed = symbols(old) - symbols(a.current)
    added = symbols(a.current) - symbols(old)
    if removed or added:
        raise SystemExit(f'Export changes: removed={sorted(removed)}, added={sorted(added)}')
    print(f'ELF target and {len(symbols(old))} exported symbol names/types unchanged')
