import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('provenance',ROOT/'tests/helpers/coverage_provenance.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Coverage(unittest.TestCase):
    def test_stale_sources_and_tampered_report_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();source=root/'scripts/unit.py';source.write_text('value=1\n')
            raw=root/'.coverage';raw.write_bytes(b'raw fixture')
            report=root/'coverage.xml';p.write_report(report,{'scripts/unit.py':{1:True}})
            receipt={'schema':1,'kind':'python','source_state':p.source_state(root),'report':report.name,
                     'report_sha256':p.digest(report),'all_suites_passed':True,'coverage_version':'7.13.5','raw_data_sha256':p.digest(raw)}
            path=root/'receipt.json';path.write_text(json.dumps(receipt))
            self.assertEqual(p.validate_receipt(root,path,kind='python'),report)
            source.write_text('value=2\n')
            with self.assertRaises(ValueError):p.validate_receipt(root,path,kind='python')
            source.write_text('value=1\n');report.write_text('<coverage/>')
            with self.assertRaises(ValueError):p.validate_receipt(root,path,kind='python')
    def test_native_counter_tampering_and_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'extension').mkdir();(root/'extension/unit.cpp').write_text('int value=1;\n')
            output=root/'results';(output/'console').mkdir(parents=True)
            counter=output/'console/unit.gcda';counter.write_bytes(b'fixture counter')
            report=output/'coverage.xml';p.write_report(report,{'extension/unit.cpp':{1:True}})
            receipt={'schema':1,'kind':'native','source_state':p.source_state(root),'report':report.name,
                     'report_sha256':p.digest(report),'all_suites_passed':True,'test_flags':'-m32 --coverage -fprofile-abs-path',
                     'counter_inputs':[{'counter':'console/unit.gcda','sha256':p.digest(counter)}]}
            path=output/'receipt.json';path.write_text(json.dumps(receipt))
            p.validate_receipt(root,path)
            counter.write_bytes(b'changed')
            with self.assertRaises(ValueError):p.validate_receipt(root,path)
            receipt['counter_inputs']=[{'counter':'../extension/unit.cpp','sha256':p.digest(root/'extension/unit.cpp')}]
            path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):p.validate_receipt(root,path)
    def test_unexecuted_baseline_cannot_have_hits(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'extension').mkdir();(root/'extension/unit.cpp').write_text('int x=1;\n')
            data={'current_working_directory':directory,'files':[{'file':'extension/unit.cpp','lines':[{'line_number':1,'count':1}]}]}
            with self.assertRaises(ValueError):p.merge_lines(root,data,{},baseline=True)

if __name__=='__main__':unittest.main()
