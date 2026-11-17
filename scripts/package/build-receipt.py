"""Record successful native build inputs and binary hashes; not installed."""
import json
from pathlib import Path
import subprocess
import sys
from artifact_contract import validate_tree, write_receipt

root, build = (Path(s).resolve() for s in sys.argv[1:3])
platform = sys.argv[3]
validate_tree(build/'package', root, platform, documentation=False)
write_receipt(build/'package', root, platform)
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
(build/'dependency-revisions.json').write_text(json.dumps(revisions, indent=2)+'\n')
