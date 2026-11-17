import importlib.util
from pathlib import Path
import subprocess
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

if __name__=='__main__':unittest.main()
