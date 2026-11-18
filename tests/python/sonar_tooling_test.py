import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sonar',ROOT/'scripts/tools/make_sonar.py')
sonar=importlib.util.module_from_spec(spec);spec.loader.exec_module(sonar)

class Sonar(unittest.TestCase):
    def test_dotenv_properties_without_project_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'.env').write_text('SONAR_SOURCES=extension\nSONAR_SOURCE_ENCODING=UTF-8\n')
            with patch.dict('os.environ', {'SONAR_SOURCES':'extension,scripts'}, clear=True):
                properties=sonar.scanner_properties(sonar.configuration(root))
            self.assertIn('-Dsonar.sources=extension,scripts', properties)
            self.assertIn('-Dsonar.sourceEncoding=UTF-8', properties)
            self.assertIn('-Dsonar.cxx.errorRecoveryEnabled=false', properties)
            self.assertFalse((root/'sonar-project.properties').exists())
    def test_dotenv_cannot_enable_parser_recovery(self):
        with self.assertRaises(sonar.SonarError):
            sonar.scanner_properties({'SONAR_CXX_ERROR_RECOVERY_ENABLED':'true'})
    def test_scanner_success_with_parser_error_rejected(self):
        result=subprocess.CompletedProcess([],0,'QUALITY GATE STATUS: PASSED','ERROR preprocessor: missing directory')
        with self.assertRaises(sonar.SonarError):sonar.validate_scanner(result)
    def test_analyzer_drops_only_absent_include_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'headers').mkdir()
            entry={'directory':directory,'file':str(root/'unit.cpp'),
                   'arguments':['c++','-m32','-Iheaders','-isystem','missing','-DX=1','-UX','-DX=2','-c',str(root/'unit.cpp')]}
            original=list(entry['arguments'])
            derived,includes=sonar.analyzer_entry(entry)
            self.assertEqual(entry['arguments'],original)
            self.assertNotIn('missing',derived['arguments'])
            self.assertIn(str(root/'headers'),derived['arguments'])
            self.assertEqual(includes,[str(root/'headers')])
            self.assertEqual(derived['arguments'][-5:],['-DX=1','-UX','-DX=2','-c',str(root/'unit.cpp')])
    def test_real_compiler_context_and_ordered_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            entries=[{'directory':directory,'file':str(root/name),
                      'arguments':['g++','-m32','-std=c++17','-O3','-fPIC','-DVALUE=1','-UVALUE','-DVALUE=2',
                                   '-I','missing','-c',str(root/name),'-o','unit.o']}
                     for name in ['one.cpp','two.cpp']]
            enriched,derived=sonar.compiler_identity(entries,dict(os.environ))
            self.assertEqual(derived[0]['defines']['VALUE'],'2')
            self.assertEqual(derived[0]['defines']['__SIZEOF_POINTER__'],'4')
            self.assertNotIn(str(root/'missing'),derived[0]['includes'])
            self.assertEqual(len(derived),3)
            self.assertIn('-m32',enriched[0]['arguments'])
    def test_compiler_probe_failure_rejected(self):
        with patch.object(sonar.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','')):
            with self.assertRaises(sonar.SonarError):sonar.probe_compiler({'directory':'/tmp'},['g++'],{})
    def test_missing_implicit_includes_rejected(self):
        with self.assertRaises(sonar.SonarError):sonar.implicit_includes('', '/tmp')
    def test_missing_cpp_context_rejected(self):
        with self.assertRaises(sonar.SonarError):sonar.global_cpp_context([],[])
    def test_database_must_cover_all_product_units_in_x86(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'extension').mkdir();source=root/'extension/unit.cpp';source.write_text('int value;')
            database=root/'commands.json'
            entry={'directory':directory,'file':str(source),'arguments':['g++','-m32','-c',str(source)]}
            database.write_text(json.dumps([entry]))
            self.assertEqual(len(sonar.compilation_database(root,database)),1)
            entry['arguments'].remove('-m32');database.write_text(json.dumps([entry]))
            with self.assertRaises(sonar.SonarError):sonar.compilation_database(root,database)
            database.write_text('[]')
            with self.assertRaises(sonar.SonarError):sonar.compilation_database(root,database)
    def test_valid_context_and_scanner_completion(self):
        context=sonar.scanner_context({'SONAR_HOST_URL':'http://127.0.0.1:9000','SONAR_TOKEN':'example'})
        self.assertEqual(context[3],'true')
        sonar.validate_scanner(subprocess.CompletedProcess([],0,'QUALITY GATE STATUS: PASSED',''))
        with self.assertRaises(sonar.SonarError):sonar.validate_scanner(subprocess.CompletedProcess([],1,'',''))
    def test_no_cppcheck_parser_failure_can_reach_scanner(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sonar.validate_cppcheck(subprocess.CompletedProcess([],0,'','<results><errors/></results>'),root,root,'')
            with self.assertRaises(sonar.SonarError):sonar.validate_cppcheck(subprocess.CompletedProcess([],1,'','failure'),root,root,'')
            with self.assertRaises(sonar.SonarError):sonar.validate_cppcheck(subprocess.CompletedProcess([],0,'','<results/>'),root,root,'')
    def test_remote_http_rejected(self):
        with self.assertRaises(sonar.SonarError):sonar.scanner_context({'SONAR_HOST_URL':'http://example.org','SONAR_TOKEN':'example'})
    def test_gate_cannot_be_disabled(self):
        with self.assertRaises(sonar.SonarError):sonar.scanner_context({'SONAR_HOST_URL':'https://example.org','SONAR_TOKEN':'example','SONAR_QUALITY_GATE_WAIT':'false'})
    def test_token_redacted(self):
        self.assertNotIn('example-token',sonar.redact('secret example-token','example-token'))
    def test_incomplete_parser_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=subprocess.CompletedProcess([],0,'','<results><errors><error id="syntaxError"/></errors></results>')
            with self.assertRaises(sonar.SonarError):sonar.validate_cppcheck(result,root,root,'')
    def test_malformed_xml_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(sonar.SonarError):sonar.validate_cppcheck(subprocess.CompletedProcess([],0,'','bad'),Path(d),Path(d),'')
    def test_compiler_query_preserves_flags_order(self):
        entry={'directory':'/tmp','file':'/tmp/unit.cpp','arguments':['c++','-m32','-O3','-fPIC','-DX=1','-UX','-DX=2','-c','/tmp/unit.cpp','-o','unit.o','-MD','-MF','unit.d']}
        query=sonar.compiler_query(entry)
        self.assertEqual(query[:7],['c++','-m32','-O3','-fPIC','-DX=1','-UX','-DX=2'])
        self.assertNotIn('-o',query);self.assertNotIn('-MD',query)
    def test_token_in_dotenv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.env').write_text('SONAR_TOKEN=example')
            with self.assertRaises(sonar.SonarError):sonar.configuration(root)

class ScannerOrchestration(unittest.TestCase):
    def setUp(self):
        import package_test
        package_test.Packages.setUp(self)
        self.contract=package_test.contract

    def cli(self, script, *args, **kwargs):
        import canonical_cli_test
        return canonical_cli_test.CanonicalCLI.cli(self, script, *args, **kwargs)

    def test_canonical_scanner_orchestration_with_offline_providers(self):
        spec=importlib.util.spec_from_file_location('scanner_product',ROOT/'scripts/tools/make_sonar.py')
        sonar=importlib.util.module_from_spec(spec);spec.loader.exec_module(sonar)
        database=self.raw.parent/'compile_commands.json'
        entries=[{'directory':str(self.root),'file':str(source),
                  'arguments':['g++','-m32','-std=c++17','-c',str(source),'-o','unit.o']}
                 for source in (self.root/'extension').rglob('*.cpp')]
        database.write_text(json.dumps(entries));self.contract.write_receipt(self.raw,self.root,'linux')
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
