"""Compile and execute the actual decoder on Linux x86 with ASan/UBSan."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
parent = root / '.build/tests'
parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='hex-string-', dir=parent) as directory:
    binary = Path(directory) / 'hex-string-test'
    subprocess.run([*shlex.split(os.environ.get('CXX', 'g++')), '-std=c++17', '-m32',
                    '-Wall', '-Wextra', '-Werror', '-g', '-fno-omit-frame-pointer',
                    '-fno-pie', '-no-pie', '-fsanitize=address,undefined',
                    '-I'+str(root/'extension/include'), str(root/'extension/src/hex-string.cpp'),
                    str(root/'tests/native/hex-string-test.cpp'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True, env={**os.environ,
                   'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1',
                   'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'})
