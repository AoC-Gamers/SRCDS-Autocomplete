"""Measure canonical console/decoder execution and retain zero-hit baseline lines."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tests/helpers'))
import coverage_provenance as provenance

p=argparse.ArgumentParser()
p.add_argument('--output', required=True, type=Path)
p.add_argument('--compile-commands', required=True, type=Path)
a=p.parse_args()
output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
state=provenance.source_state(ROOT)
spec=importlib.util.spec_from_file_location('sonar',ROOT/'scripts/tools/make_sonar.py')
sonar=importlib.util.module_from_spec(spec);spec.loader.exec_module(sonar)
entries=sonar.compilation_database(ROOT,a.compile_commands)
flags='-m32 --coverage -fprofile-abs-path'
merged={};units={};inputs=[]
with (output/'build.log').open('w') as log:
    # Baseline every actual product unit with the build's compiler flags. Merge
    # real harness counters later; all other executable lines retain zero hits.
    for index,entry in enumerate(entries):
        command=[];args=iter(entry['arguments'])
        for arg in args:
            if arg in {'-o','-MF','-MT','-MQ'}:next(args)
            elif arg not in {'-MD','-MMD','-MP'}:command.append(arg)
        obj=output/f'unit-{index}.o'
        command+=['--coverage','-fprofile-abs-path','-O0','-o',str(obj)]
        subprocess.run(command,cwd=entry['directory'],stdout=log,stderr=subprocess.STDOUT,check=True)
        units[Path(entry['file']).name]=obj
    binary=output/'decoder-test'
    subprocess.run([os.environ.get('CXX','g++'),'-m32','-std=c++17','--coverage','-fprofile-abs-path',
                    '-I'+str(ROOT/'extension/include'),str(ROOT/'tests/native/hex-string-test.cpp'),
                    str(units['hex-string.cpp']),'-o',str(binary)],stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([str(binary)],stdout=log,stderr=subprocess.STDOUT,check=True)
console=output/'console'
subprocess.run([sys.executable,str(ROOT/'tests/runners/test-console.py'),'--coverage-output',str(console)],check=True)
for index,counter in enumerate(sorted(console.glob('*.gcda'))):
    payload=provenance.read_gcov(counter,ROOT)
    (output/f'console-gcov-{index}.json').write_text(json.dumps(payload))
    provenance.merge_lines(ROOT,payload,merged)
    inputs.append({'counter':counter.relative_to(output).as_posix(),'sha256':provenance.digest(counter)})
for index,obj in enumerate(units.values()):
    counter=obj.with_suffix('.gcda')
    executed=counter.is_file()
    source=counter if executed else obj.with_suffix('.gcno')
    payload=provenance.read_gcov(source,ROOT)
    (output/f'gcov-{index}.json').write_text(json.dumps(payload))
    provenance.merge_lines(ROOT,payload,merged,baseline=not executed)
    if executed:inputs.append({'counter':source.name,'sha256':provenance.digest(source)})
if provenance.source_state(ROOT)!=state:raise ValueError('Sources changed during coverage')
report=output/'coverage.xml';provenance.write_report(report,merged)
receipt={'schema':1,'kind':'native','source_state':state,'report':report.name,
         'report_sha256':provenance.digest(report),'all_suites_passed':True,'test_flags':flags,
         'counter_inputs':inputs,'runtime_acceptance':False,
         'line_count':sum(len(rows) for rows in merged.values()),
         'covered_line_count':sum(sum(rows.values()) for rows in merged.values())}
(output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(f"NATIVE_COVERAGE_OK {receipt['covered_line_count']}/{receipt['line_count']} canonical product lines")
