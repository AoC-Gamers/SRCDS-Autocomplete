"""Package regressions use synthetic headers, never claim real ELF/PE builds."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/package'))
import artifact_contract as contract
spec = importlib.util.spec_from_file_location('release_identity', ROOT/'scripts/package/release-identity.py')
identity = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = identity
spec.loader.exec_module(identity)


def binary(platform):
    data = bytearray(128)
    if platform == 'linux':
        data[:7] = b'\x7fELF\x01\x01\x01'
        struct.pack_into('<HH', data, 16, 3, 3)
    else:
        data[:2] = b'MZ'
        struct.pack_into('<I', data, 60, 64)
        data[64:68] = b'PE\0\0'
        struct.pack_into('<H', data, 68, 0x14c)
        struct.pack_into('<H', data, 86, 0x2000)
        struct.pack_into('<H', data, 88, 0x10b)
    return bytes(data)


class Packages(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='autocomplete tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'source copy'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git','.build','.deps','dist','__pycache__','.env','env.secret'))
        self.raw = self.root/'.build/linux-l4d2/package'
        self.raw.mkdir(parents=True)
        for name in contract.expected(self.root, 'linux', False):
            p = self.raw/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(binary('linux') if name.endswith('.so') else (self.root/('extension/autocomplete.autoload' if name.endswith('.autoload') else name)).read_bytes())
        contract.write_receipt(self.raw, self.root, 'linux')

    def make(self, target, *args, success=True):
        result = subprocess.run(['make', '--no-print-directory', '-f', str(self.root/'Makefile'), target, *args], cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout+result.stderr)
        return result

    def test_linux_full_make_from_external_cwd_spaces_without_git(self):
        self.make('package-exts-linux')
        self.make('release-linux', 'RELEASE_BASENAME=srcds-autocomplete-develop-linux')
        self.make('validate-artifact-linux', 'RELEASE_BASENAME=srcds-autocomplete-develop-linux')
        z=self.root/'dist/release/srcds-autocomplete-develop-linux.zip'
        files=contract.validate_zip(z,self.root,'linux')
        self.assertEqual(set(files), contract.expected(self.root,'linux'))
        self.assertNotIn('scripts/package/package-map.json', files)

    def test_windows_make_packaging_with_synthetic_pe(self):
        raw=self.root/'.build/windows-l4d2/package'
        shutil.copytree(self.raw,raw)
        old=next(raw.rglob('*.so'));old.unlink()
        old.with_suffix('.dll').write_bytes(binary('windows'))
        contract.write_receipt(raw,self.root,'windows')
        self.make('package-exts-windows')
        self.make('release-windows')
        self.make('validate-artifact-windows')

    def test_missing_gamedata_rejected(self):
        (self.raw/'addons/sourcemod/gamedata/autocomplete.games.txt').unlink()
        self.make('package-exts-linux',success=False)

    def test_external_sdk_rejected(self):
        extra=self.raw/'addons/sourcemod/extensions/steamworks.ext.so'
        extra.write_bytes(binary('linux'))
        self.make('package-exts-linux',success=False)

    def test_wrong_architecture_rejected(self):
        next(self.raw.rglob('*.so')).write_bytes(b'\x7fELF\x02'+bytes(128))
        self.make('package-exts-linux',success=False)

    def test_source_change_rejects_old_build(self):
        with (self.root/'extension/src/extension.cpp').open('a') as f:f.write('\n// Changed source\n')
        self.make('package-exts-linux',success=False)

    def test_binary_tampering_rejected(self):
        with next(self.raw.rglob('*.so')).open('ab') as f:f.write(b'changed')
        self.make('package-exts-linux',success=False)

    def test_missing_success_receipt_rejected(self):
        contract.receipt_path(self.raw).unlink()
        self.make('package-exts-linux',success=False)

    def test_symlink_rejected(self):
        p=self.raw/'addons/sourcemod/gamedata/autocomplete.games.txt';p.unlink();p.symlink_to(self.root/'addons/sourcemod/gamedata/autocomplete.games.txt')
        self.make('package-exts-linux',success=False)

    def test_case_collision_rejected(self):
        p=self.raw/'addons/sourcemod/extensions/AUTOCOMPLETE.autoload';p.write_text('')
        self.make('package-exts-linux',success=False)

    def test_unsafe_basename_preserves_existing_zip(self):
        self.make('package-exts-linux');self.make('release-linux')
        z=self.root/'dist/release/srcds-autocomplete-local-linux.zip';before=z.read_bytes()
        self.make('release-linux','RELEASE_BASENAME=../escape',success=False)
        self.assertEqual(z.read_bytes(),before)

    def test_zip_extras_and_duplicates_rejected(self):
        self.make('package-exts-linux');self.make('release-linux')
        z=self.root/'dist/release/srcds-autocomplete-local-linux.zip'
        with zipfile.ZipFile(z,'a') as out:out.writestr('env.secret','example')
        self.make('validate-artifact-linux',success=False)

    def test_zip_traversal_and_links_rejected(self):
        z=self.root/'unsafe.zip'
        for name in ['../escape','/absolute','a/../escape','a\\escape']:
            with self.subTest(name=name):
                with zipfile.ZipFile(z,'w') as out:out.writestr(name,'bad')
                with self.assertRaises(ValueError):contract.validate_zip(z,self.root,'linux')
        with zipfile.ZipFile(z,'w') as out:
            info=zipfile.ZipInfo('link');info.external_attr=0o120777 << 16;out.writestr(info,'target')
        with self.assertRaises(ValueError):contract.validate_zip(z,self.root,'linux')

    def test_unknown_map_key_rejected(self):
        p=self.root/contract.MAP;data=json.loads(p.read_text());data['ignored']={};p.write_text(json.dumps(data))
        self.make('package-exts-linux',success=False)

    def test_failed_build_invalidates_old_receipt(self):
        self.make('build-exts-linux', 'LINUX_DEPS_DIR='+str(self.root/'missing-deps'), success=False)
        self.make('package-exts-linux', success=False)

    def test_clean_rejects_external_dependencies(self):
        external=Path(self.temp.name)/'external-sdk'
        external.mkdir();(external/'keep').write_text('keep')
        self.make('clean-linux','LINUX_BUILD_DIR='+str(external),success=False)
        self.assertTrue((external/'keep').is_file())

    def test_map_cannot_admit_secret(self):
        p=self.root/contract.MAP;data=json.loads(p.read_text());data['documentation'].append('env.secret');p.write_text(json.dumps(data))
        with self.assertRaises(ValueError):contract.expected(self.root,'linux')

    def test_final_zip_binary_tamper_rejected(self):
        self.make('package-exts-linux');self.make('release-linux')
        z=self.root/'dist/release/srcds-autocomplete-local-linux.zip'
        with zipfile.ZipFile(z) as src:files={n:src.read(n) for n in src.namelist()}
        for name in files:
            if name.endswith('.so'):files[name]+=b'changed'
        with zipfile.ZipFile(z,'w') as out:
            for name,data in files.items():out.writestr(name,data)
        self.make('validate-artifact-linux',success=False)

    def test_channel_publication_with_offline_gh(self):
        workflow=(self.root/'.github/workflows/build.yml').read_text()
        start=workflow.index('        run: |',workflow.index('      - name: Publish channel release'))
        end=workflow.index('      - name: Publish tagged release',start)
        script='\n'.join(line[10:] for line in workflow[start:end].splitlines()[1:])
        script=script.replace('${{ needs.build-exts-linux.outputs.release-tag }}','channel/develop').replace('${{ needs.build-exts-linux.outputs.release-name }}','Develop').replace('${{ needs.build-exts-linux.outputs.basename }}','srcds-autocomplete-develop-linux').replace('${{ needs.build-exts-windows.outputs.basename }}','srcds-autocomplete-develop-windows').replace('${{ needs.build-exts-linux.outputs.prerelease }}','true')
        release=self.root/'dist/release';release.mkdir(parents=True)
        for platform in ['linux','windows']:(release/f'srcds-autocomplete-develop-{platform}.zip').write_text('offline fixture')
        tools=self.root/'offline-bin';tools.mkdir()
        gh=tools/'gh';gh.write_text('#!'+sys.executable+'\nimport json,os,sys\nwith open(os.environ["GH_LOG"],"a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\nif os.environ.get("FAIL_UPLOAD") and "upload" in sys.argv:sys.exit(1)\n')
        gh.chmod(0o755)
        log=self.root/'gh-log.jsonl'
        env={**os.environ,'PATH':str(tools)+os.pathsep+os.environ['PATH'],'GH_LOG':str(log),'GITHUB_SHA':'a'*40,'GITHUB_SERVER_URL':'https://example.invalid','GITHUB_REPOSITORY':'test/repo','GITHUB_RUN_ID':'1','GITHUB_RUN_ATTEMPT':'1'}
        for fail in [False,True]:
            with self.subTest(fail_upload=fail):
                log.unlink(missing_ok=True)
                result=subprocess.run(['bash','-euo','pipefail','-c',script],cwd=self.root,env={**env,**({'FAIL_UPLOAD':'1'} if fail else {})},capture_output=True,text=True)
                self.assertEqual(result.returncode==0,not fail,result.stderr)
                calls=[json.loads(line) for line in log.read_text().splitlines()]
                verbs=[call[1] for call in calls]
                self.assertLess(verbs.index('create'),verbs.index('upload'))
                self.assertIn('--draft',calls[verbs.index('create')])
                self.assertEqual('edit' in verbs,not fail)
                if not fail:self.assertLess(verbs.index('upload'),verbs.index('edit'))

    def test_channel_identity(self):
        for platform in ['linux','windows']:
            for branch,channel in [('main','latest'),('develop','develop')]:
                result=identity.resolve('srcds-autocomplete',platform,'branch',branch)
                self.assertEqual(result.basename, f'srcds-autocomplete-{channel}-{platform}')
                self.assertEqual(result.prerelease,branch=='develop')
            self.assertEqual(identity.resolve('srcds-autocomplete',platform,'tag','v1.2.3').channel,'1.2.3')
            self.assertFalse(identity.resolve('srcds-autocomplete',platform,'branch','feature','a'*40).publishable)
            self.assertFalse(identity.resolve('srcds-autocomplete',platform).publishable)
        for ref in ['v../escape','v1/escape','v$(x)']:
            with self.assertRaises(ValueError):identity.resolve('srcds-autocomplete','linux','tag',ref)

    def test_make_identity(self):
        data=json.loads(self.make('release-identity-windows').stdout)
        self.assertEqual(data['basename'],'srcds-autocomplete-local-windows')


if __name__=='__main__':unittest.main()
