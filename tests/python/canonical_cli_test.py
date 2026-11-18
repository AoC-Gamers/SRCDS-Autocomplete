"""Execute canonical product scripts; all mutable inputs/outputs stay in fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import pickle
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch
import package_test as package_fixtures
ROOT=package_fixtures.ROOT
contract=package_fixtures.contract

class CanonicalCLI(unittest.TestCase):
    setUp=package_fixtures.Packages.setUp

    def cli(self, script, *args, success=True, env=None):
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],
                              cwd=self.temp.name,capture_output=True,text=True,env=env)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr)
        return result

    def test_canonical_stage_zip_and_validation(self):
        stage=self.root/'.build/stage'
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux')
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux')
        self.cli('package/package-release.py','--root',self.root,'--artifact-dir',stage,
                 '--basename','srcds-autocomplete-local-linux','--platform','linux')
        archive=self.root/'dist/release/srcds-autocomplete-local-linux.zip'
        self.cli('ci/validate-artifact.py','--artifact-dir',stage,'--platform','linux','--zip',archive)
        self.cli('package/stage-artifact.py',self.root,self.raw,self.raw,'--platform','linux',success=False)
        self.cli('package/package-release.py','--root',self.root,'--artifact-dir',stage,
                 '--basename','../escape','--platform','linux',success=False)

    def test_canonical_build_receipt_and_identity(self):
        env={**os.environ,'HL2SDK_DIR':str(ROOT),'SOURCEMOD_DIR':str(ROOT),'MMSOURCE_DIR':str(ROOT),'AMBUILD_DIR':str(ROOT)}
        self.cli('package/build-receipt.py',self.root,self.raw.parent,'linux',env=env)
        revisions=json.loads((self.raw.parent/'dependency-revisions.json').read_text())
        self.assertEqual(set(revisions),{'HL2SDK_DIR','SOURCEMOD_DIR','MMSOURCE_DIR','AMBUILD_DIR'})
        result=self.cli('package/release-identity.py','--name','srcds-autocomplete','--platform','linux','--ref-type','branch','--ref','develop')
        self.assertEqual(json.loads(result.stdout)['release_tag'],'channel/develop')
        self.cli('package/release-identity.py','--name','INVALID',success=False)

    def test_canonical_clean_preserves_unmanaged_data(self):
        target=self.root/'.build/to-clean';target.mkdir();(target/'result').write_text('fixture')
        loose=self.root/'.build/loose';loose.write_text('fixture')
        self.cli('tools/clean.py',self.root,target,loose,self.root/'.build/absent')
        self.assertFalse(target.exists());self.assertFalse(loose.exists())
        self.cli('tools/clean.py',self.root,self.root/'extension',success=False)
        self.assertTrue((self.root/'extension/src/extension.cpp').exists())

    def test_compilation_database_reads_actual_successful_compiler_command(self):
        build=self.root/'.build/export';(build/'.ambuild2').mkdir(parents=True)
        source=build/'unit.cpp';source.write_text('int value=7;\n')
        command=['g++','-m32','-c',str(source),'-o','unit.o']
        subprocess.run(command,cwd=build,check=True)
        with sqlite3.connect(build/'.ambuild2/graph') as db:
            db.execute('CREATE TABLE nodes(id integer,type text,dirty integer,path text,folder integer,data blob)')
            db.execute('INSERT INTO nodes VALUES(1,\'mkd\',0,\'\',NULL,NULL)')
            db.execute('INSERT INTO nodes VALUES(2,\'cxx\',0,NULL,1,?)',(pickle.dumps({'argv':command}),))
        self.cli('build/export-compile-commands.py',build)
        result=json.loads((build/'compile_commands.json').read_text())
        self.assertEqual(result[0]['arguments'],command)
        with sqlite3.connect(build/'.ambuild2/graph') as db:db.execute('UPDATE nodes SET dirty=1 WHERE id=2')
        self.cli('build/export-compile-commands.py',build,success=False)
        with sqlite3.connect(build/'.ambuild2/graph') as db:
            db.execute('UPDATE nodes SET dirty=0,data=? WHERE id=2',(pickle.dumps(Path('forbidden-global')),))
        self.cli('build/export-compile-commands.py',build,success=False)
        with sqlite3.connect(build/'.ambuild2/graph') as db:db.execute('DELETE FROM nodes WHERE id=2')
        self.cli('build/export-compile-commands.py',build,success=False)

    def test_canonical_scanner_orchestration_with_offline_providers(self):
        spec=importlib.util.spec_from_file_location('scanner_product',ROOT/'scripts/tools/make_sonar.py')
        sonar=importlib.util.module_from_spec(spec);spec.loader.exec_module(sonar)
        database=self.raw.parent/'compile_commands.json'
        entries=[{'directory':str(self.root),'file':str(source),
                  'arguments':['g++','-m32','-std=c++17','-c',str(source),'-o','unit.o']}
                 for source in (self.root/'extension').rglob('*.cpp')]
        database.write_text(json.dumps(entries));contract.write_receipt(self.raw,self.root,'linux')
        cppcheck=self.root/'cppcheck-provider';scanner=self.root/'scanner-provider'
        cppcheck.write_text('#!'+sys.executable+'\nimport sys\nprint("<results><errors/></results>",file=sys.stderr)\n')
        scanner.write_text('#!'+sys.executable+'\nimport os,sys,json\nfrom pathlib import Path\nPath(os.environ["ARGV_LOG"]).write_text(json.dumps(sys.argv))\nprint("QUALITY GATE STATUS: PASSED")\n')
        cppcheck.chmod(0o755);scanner.chmod(0o755);log=self.root/'argv.json'
        env={'SONAR_CPPCHECK':str(cppcheck),'SONAR_SCANNER':str(scanner),'SONAR_HOST_URL':'https://example.invalid',
             'SONAR_TOKEN':'offline-fixture-secret','SONAR_COVERAGE_RECEIPT':'','SONAR_PYTHON_COVERAGE_RECEIPT':'','ARGV_LOG':str(log)}
        with patch.dict(os.environ,env):
            sonar.run('analyze',database,root=self.root)
            self.assertNotIn(env['SONAR_TOKEN'],log.read_text())
            sonar.run('cppcheck',database,root=self.root)
            scanner.write_text('#!'+sys.executable+'\nimport sys\nprint("ERROR parser failed",file=sys.stderr)\n')
            with self.assertRaises(sonar.SonarError):sonar.run('analyze',database,root=self.root)
        self.cli('tools/make_sonar.py','analyze','--compile-commands',database,
                 success=False,env={**os.environ,**env,'SONAR_HOST_URL':''})

if __name__=='__main__':unittest.main()
