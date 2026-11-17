"""Run product regressions in a fresh caller-relative output directory."""
import argparse
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('--output', required=True)
a=p.parse_args()
if not a.output:
    p.error('Set TEST_OUTPUT to a new directory')
output=Path(a.output).absolute()
output.mkdir(parents=True, exist_ok=False)
root=Path(__file__).resolve().parents[2]
result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(root/'tests/python'),'-p','package_test.py','-v'],capture_output=True,text=True)
log=result.stdout+result.stderr
(output/'tests.log').write_text(log)
print(log,end='')
raise SystemExit(result.returncode)
