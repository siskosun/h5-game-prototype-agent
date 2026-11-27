import hashlib, importlib.util, pathlib, tempfile, unittest
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/"scripts/completion_checkpoints.py"
spec=importlib.util.spec_from_file_location("completion_checkpoints",SCRIPT); checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.root=pathlib.Path(self.t.name)
  for n,v in [("w.json",'{"p":"w"}'),("l.json",'{"p":"l"}')]: (self.root/n).write_text(v)
  self.art="a"*64; self.src="b"*40
  self.doc={"schema_version":2,"artifact_sha256":self.art,"source_sha":self.src,"checkpoints":[{"id":"start","requires":[],"source_files":["src/start.gd"],"status":"PASS","input_origin":"ENGINE_INPUT","normal_player_path":True,"evidence":[self.ev("w.json")]},{"id":"win","requires":["start"],"source_files":["src/rules.gd"],"status":"PASS","input_origin":"ENGINE_INPUT","terminal":True,"evidence":[self.ev("w.json")]},{"id":"lose","requires":["start"],"source_files":["src/rules.gd"],"status":"PASS","input_origin":"ENGINE_INPUT","terminal":True,"evidence":[self.ev("l.json")]}],"paths":[{"id":"win_path","checkpoints":["start","win"]},{"id":"lose_path","checkpoints":["start","lose"]}],"transitions":[{"from":"start","to":"win"},{"from":"start","to":"lose"}],"path_results":[self.result("win_path","w.json","win"),self.result("lose_path","l.json","lose")]}
 def ev(self,n):
  b=(self.root/n).read_bytes(); return {"type":"trace","path":n,"sha256":hashlib.sha256(b).hexdigest()}
 def result(self,p,n,d): return {"path_id":p,"status":"PASS","artifact_sha256":self.art,"source_sha":self.src,"trace":self.ev(n),"input_origin":"ENGINE_INPUT","transitions":[{"from":"start","to":d}]}
 def test_full_coverage(self):
  r=checker.verify(self.doc,self.root,require_path_coverage=True); self.assertEqual(r["status"],"PASS"); self.assertEqual(r["coverage"]["path_coverage"],1.0)
 def test_missing_path(self):
  self.doc["path_results"].pop(); r=checker.verify(self.doc,self.root,require_path_coverage=True); self.assertEqual(r["status"],"FAIL"); self.assertIn("lose_path",r["coverage"]["missing_paths"])
 def test_wrong_edge(self):
  self.doc["path_results"][0]["transitions"]=[{"from":"start","to":"lose"}]; self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
 def test_source_mismatch(self):
  self.doc["path_results"][0]["source_sha"]="c"*40; self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
 def test_trace_tamper(self):
  (self.root/"w.json").write_text("bad"); self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
 def test_change_invalidates(self):
  r=checker.verify(self.doc,self.root,changed=["src/rules.gd"],require_path_coverage=True); self.assertEqual(r["status"],"FAIL"); self.assertIn("win",r["invalidated"])
 def test_state_setup_rejected(self):
  self.doc["path_results"][0]["input_origin"]="STATE_SETUP"; self.assertEqual(checker.verify(self.doc,self.root)["status"],"FAIL")
 def test_v1_compatibility(self):
  old={"schema_version":1,"artifact_sha256":self.art,"checkpoints":[{"id":"s","requires":[],"source_files":["src/start.gd"],"status":"PASS","input_origin":"ENGINE_INPUT","normal_player_path":True,"evidence":[self.ev("w.json")]},{"id":"f","requires":["s"],"source_files":["src/rules.gd"],"status":"PASS","input_origin":"ENGINE_INPUT","terminal":True,"evidence":[self.ev("w.json")]}]}
  self.assertEqual(checker.verify(old,self.root,require_completion=True)["status"],"PASS")
 def test_unknown_edge(self):
  self.doc["transitions"].append({"from":"missing","to":"win"})
  with self.assertRaises(checker.EvidenceError): checker.verify(self.doc,self.root)
 def test_gate_opt_in(self):
  self.doc["path_results"].pop(); self.assertEqual(checker.verify(self.doc,self.root)["status"],"PASS"); self.assertEqual(checker.verify(self.doc,self.root,require_path_coverage=True)["status"],"FAIL")
if __name__=="__main__": unittest.main()
