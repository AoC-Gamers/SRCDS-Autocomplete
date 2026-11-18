import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'package'))
from artifact_contract import ROOT, validate_tree, validate_zip, verify_receipt

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, default=ROOT)
p.add_argument('--artifact-dir', required=True, type=Path)
p.add_argument('--platform', required=True, choices=['linux', 'windows'])
p.add_argument('--zip', required=True, type=Path)
a = p.parse_args()
tree = validate_tree(a.artifact_dir, a.root, a.platform)
verify_receipt(a.artifact_dir, a.root, a.platform)
if validate_zip(a.zip, a.root, a.platform) != tree:
    raise ValueError('ZIP differs from artifact tree')
print('ARTIFACT_AND_ZIP_VALIDATION_OK')
