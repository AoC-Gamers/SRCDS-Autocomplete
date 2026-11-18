"""Record successful native build inputs and binary hashes; not installed."""
from pathlib import Path
import subprocess
import sys
from artifact_contract import atomic_json, receipt_path, validate_tree, write_receipt

root, build = (Path(s).resolve() for s in sys.argv[1:3])
platform = sys.argv[3]
# A failed retry must not leave the previous operation marked successful.
receipt_path(build/'package').unlink(missing_ok=True)
(build/'dependency-revisions.json').unlink(missing_ok=True)
validate_tree(build/'package', root, platform, documentation=False)
# Record the effective dependency revisions, including recursive submodules.
revisions = {}
import os
for name in ('HL2SDK_DIR', 'SOURCEMOD_DIR', 'MMSOURCE_DIR', 'AMBUILD_DIR'):
    path = os.environ.get(name)
    if not path:
        continue
    revisions[name] = {
        'commit': subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip(),
        'submodules': subprocess.check_output(['git', '-C', path, 'submodule', 'status', '--recursive'], text=True).splitlines(),
        'dirty': bool(subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip()),
    }
atomic_json(build/'dependency-revisions.json', revisions)
# Commit the success marker only after every validation and inventory operation.
write_receipt(build/'package', root, platform)
