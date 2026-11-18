"""Execute canonical product scripts; all mutable inputs/outputs stay in fixtures."""
import json
import os
from pathlib import Path
import pickle
import sqlite3
import subprocess
import sys
import unittest
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


    def test_documentation_symlinks_and_special_sources_rejected(self):
        stage=self.root/'.build/guarded-stage'
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux')
        original=(stage/'docs/build/README.md').read_bytes()
        document=self.root/'docs/build/README.md'
        external=Path(self.temp.name)/'external.md';external.write_text('synthetic external document')
        document.unlink();document.symlink_to(external)
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux',success=False)
        self.assertEqual((stage/'docs/build/README.md').read_bytes(),original)
        document.unlink();document.symlink_to(self.root/'README.md')
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux',success=False)
        document.unlink();os.mkfifo(document)
        self.cli('package/stage-artifact.py',self.root,self.raw,stage,'--platform','linux',success=False)

    def test_linked_documentation_directory_rejected(self):
        import shutil
        directory=self.root/'docs/build'
        external=Path(self.temp.name)/'external-docs'
        shutil.copytree(directory,external);shutil.rmtree(directory);directory.symlink_to(external,target_is_directory=True)
        self.cli('package/stage-artifact.py',self.root,self.raw,self.root/'.build/stage','--platform','linux',success=False)

    def test_build_forwards_exact_sdk_and_inventory_path_before_changing_cwd(self):
        deps=self.root/'fixture-deps';deps.mkdir()
        sdk=self.root/'chosen SDK';sdk.mkdir()
        for name in ('sourcemod-1.12','mmsource-1.12'):(deps/name).mkdir()
        venv=deps/'.venv-linux/bin';venv.mkdir(parents=True)
        (venv/'python').symlink_to(sys.executable)
        ambuild=venv/'ambuild';ambuild.write_text('#!/bin/sh\nexit 99\n');ambuild.chmod(0o755)
        record=self.root/'configure-arguments.json'
        config=self.root/'probe-configure.py'
        config.write_text('import os,sys,json\nfrom pathlib import Path\nPath(os.environ["SDK_PROBE_LOG"]).write_text(json.dumps({"args":sys.argv,"sdk":os.environ["HL2SDK_DIR"]}))\nraise SystemExit(1)\n')
        env={**os.environ,'HL2SDK_DIR':str(sdk.relative_to(Path(self.temp.name))),
             'CONFIGURE_SCRIPT':str(config),'ENV_FILE':str(self.root/'no-env'), 'SDK_PROBE_LOG':str(record)}
        result=subprocess.run(['make','--no-print-directory','-f',str(ROOT/'Makefile'),'build-exts-linux',
                               'LINUX_DEPS_DIR='+str(deps),'LINUX_BUILD_DIR='+str(self.root/'.build/sdk-build')],
                              cwd=self.temp.name,env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        data=json.loads(record.read_text())
        self.assertEqual(data['args'][data['args'].index('--hl2sdk-path')+1],str(sdk.resolve()))
        self.assertEqual(data['sdk'],str(sdk.resolve()))
        self.assertFalse((self.root/'.build/sdk-build/build-receipt.json').exists())

if __name__=='__main__':unittest.main()
