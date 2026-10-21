import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

SCRIPT=pathlib.Path(__file__).resolve().parents[1]/"scripts/completion_checkpoints.py"
spec=importlib.util.spec_from_file_location("completion_checkpoints",SCRIPT)
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class CompletionCheckpointsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        f=self.root/"trace.json"
        f.write_text('{"input":"click","terminal":true}',encoding="utf-8")
        e={"type":"input","path":"trace.json","sha256":hashlib.sha256(f.read_bytes()).hexdigest()}
        self.doc={"schema_version":1,"artifact_sha256":"a"*64,"checkpoints":[
            {"id":"launch","requires":[],"source_files":["game/main.js"],"status":"PASS",
             "normal_player_path":True,"input_origin":"BROWSER_INPUT","evidence":[e]},
            {"id":"finish","requires":["launch"],"source_files":["game/rules.js"],"status":"PASS",
             "terminal":True,"normal_player_path":True,"input_origin":"BROWSER_INPUT","evidence":[e]}
        ]}
    def test_complete_path_passes(self):
        self.assertEqual(checker.verify(self.doc,self.root,require_completion=True,
                                       expected_artifact="a"*64)["status"],"PASS")
    def test_change_invalidates_downstream(self):
        result=checker.verify(self.doc,self.root,changed=["game/main.js"],
                              require_completion=True,expected_artifact="a"*64)
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["invalidated"],["finish","launch"])
    def test_changed_evidence_cannot_pass(self):
        (self.root/"trace.json").write_text("modified")
        self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
    def test_state_injection_not_normal_path(self):
        self.doc["checkpoints"][0]["input_origin"]="STATE_SETUP"
        self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
    def test_future_dependency_disallowed(self):
        self.doc["checkpoints"][0]["requires"]=["finish"]
        with self.assertRaises(checker.EvidenceError):
            checker.verify(self.doc,self.root)
    def test_path_traversal_disallowed(self):
        self.doc["checkpoints"][0]["evidence"][0]["path"]="../escape"
        with self.assertRaises(checker.EvidenceError):
            checker.verify(self.doc,self.root)
    def test_artifact_identity_mismatch(self):
        with self.assertRaises(checker.EvidenceError):
            checker.verify(self.doc,self.root,expected_artifact="f"*64)
    def test_incomplete_critical_step_fails(self):
        self.doc["checkpoints"][1]["status"]="UNVERIFIED"
        self.assertEqual(checker.verify(self.doc,self.root,require_completion=True)["status"],"FAIL")

if __name__=="__main__":
    unittest.main()
