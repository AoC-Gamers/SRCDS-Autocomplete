"""Execute unchanged canonical console code with controlled SDK providers in x86."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--coverage-output',type=Path)
a=p.parse_args()
parent=ROOT/'.build/tests';parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='console-',dir=parent) as temporary:
    output=a.coverage_output.resolve() if a.coverage_output else Path(temporary)
    output.mkdir(parents=True,exist_ok=True)
    fixtures=Path(temporary)/'server';fixtures.mkdir()
    binary=output/'console-test'
    flags=['--coverage','-fprofile-abs-path','-O0'] if a.coverage_output else ['-fsanitize=address,undefined','-fno-omit-frame-pointer']
    command=[*shlex.split(os.environ.get('CXX','g++')),'-m32','-std=c++17','-g','-Wall','-Wextra','-Werror',
             '-Wno-unused-parameter','-D_LINUX','-fno-pie','-no-pie',*flags,
             '-I'+str(ROOT/'tests/native/providers'),'-I'+str(ROOT/'extension/include'),
             str(ROOT/'tests/native/console-test.cpp'),str(ROOT/'extension/src/hex-string.cpp'),
             '-Wl,--wrap=dlopen','-Wl,--wrap=dlclose','-o',str(binary)]
    subprocess.run(command,check=True)
    subprocess.run([str(binary),str(fixtures)],check=True,env={**os.environ,
                   'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'})
