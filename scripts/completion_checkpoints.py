#!/usr/bin/env python3
"""Validate legacy checkpoints and opt-in v2 declared path/transition coverage."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re
IDENTIFIER=re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
SHA256=re.compile(r"^[0-9a-f]{64}$")
STATUSES={"PASS","FAIL","UNVERIFIED","STALE"}
ORIGINS={"OS_INPUT","BROWSER_INPUT","ENGINE_INPUT","MODEL_CALL","STATE_SETUP"}
class EvidenceError(ValueError): pass
def ident(v,label):
 if not isinstance(v,str) or not IDENTIFIER.fullmatch(v): raise EvidenceError("invalid "+label)
 return v
def digest(v,label):
 if not isinstance(v,str) or not SHA256.fullmatch(v): raise EvidenceError("invalid "+label)
 return v
def confined(root,rel):
 if not isinstance(rel,str) or not rel or "\\" in rel or ":" in rel: raise EvidenceError("invalid relative evidence path")
 p=pathlib.PurePosixPath(rel)
 if p.is_absolute() or any(x in (".","..") for x in p.parts): raise EvidenceError("evidence path escapes workspace")
 f=root.joinpath(*p.parts)
 if f.is_symlink() or not f.resolve().is_relative_to(root.resolve()): raise EvidenceError("unsafe evidence file")
 return f
def verify(doc,root,*,changed=(),require_completion=False,expected_artifact=None,require_path_coverage=False):
 if not isinstance(doc,dict) or doc.get("schema_version") not in (1,2): raise EvidenceError("invalid schema version")
 v=doc["schema_version"]; art=digest(doc.get("artifact_sha256"),"artifact_sha256")
 if expected_artifact is not None and art!=expected_artifact: raise EvidenceError("artifact identity mismatch")
 src=doc.get("source_sha")
 if v==2 and (not isinstance(src,str) or not re.fullmatch(r"[0-9a-f]{40}",src)): raise EvidenceError("invalid source_sha")
 steps=doc.get("checkpoints")
 if not isinstance(steps,list) or not steps or len(steps)>512: raise EvidenceError("invalid checkpoint list")
 entries={}; order=[]; errors=[]
 for item in steps:
  if not isinstance(item,dict): raise EvidenceError("checkpoint must be object")
  cid=ident(item.get("id"),"checkpoint id")
  if cid in entries: raise EvidenceError("duplicate checkpoint id")
  req=item.get("requires",[])
  if not isinstance(req,list) or any(not isinstance(x,str) or x not in entries for x in req) or len(set(req))!=len(req): raise EvidenceError("unknown/later/duplicate checkpoint dependency")
  files=item.get("source_files",[])
  if not isinstance(files,list) or any(not isinstance(x,str) for x in files): raise EvidenceError("invalid source_files")
  for f in files: confined(root,f)
  st,origin=item.get("status"),item.get("input_origin")
  if st not in STATUSES or origin not in ORIGINS: raise EvidenceError("invalid checkpoint status/input_origin")
  evs=item.get("evidence",[])
  if not isinstance(evs,list): raise EvidenceError("invalid evidence list")
  if st=="PASS" and not evs: errors.append(cid+": PASS requires evidence")
  for ev in evs:
   if not isinstance(ev,dict) or ev.get("type") not in ("input","state","screen","log","trace"): raise EvidenceError("invalid evidence entry")
   f=confined(root,ev.get("path")); h=digest(ev.get("sha256"),"evidence sha256")
   if st=="PASS" and (not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=h): errors.append(cid+": evidence missing/digest mismatch")
  if st=="PASS" and origin in ("MODEL_CALL","STATE_SETUP") and item.get("normal_player_path"): errors.append(cid+": injected/model input cannot prove player path")
  if st=="PASS" and any(entries[x]["status"]!="PASS" for x in req): errors.append(cid+": dependency not PASS")
  entries[cid]=item; order.append(cid)
 invalid=set(); changed_set=set()
 for f in changed: confined(root,f); changed_set.add(f)
 for cid in order:
  it=entries[cid]
  if set(it.get("source_files",[]))&changed_set or any(x in invalid for x in it.get("requires",[])): invalid.add(cid)
 required=[x for x in order if entries[x].get("required",True)]
 terminals=[x for x in required if entries[x].get("terminal")]
 if require_completion and not terminals: errors.append("required terminal checkpoint missing")
 if require_completion and not any(entries[x].get("normal_player_path") and entries[x]["input_origin"] in ("OS_INPUT","BROWSER_INPUT","ENGINE_INPUT") for x in order): errors.append("normal player input path missing")
 if require_completion:
  for x in required:
   if entries[x]["status"]!="PASS" or x in invalid: errors.append(x+": required checkpoint not current PASS")
 coverage=None
 if v==2:
  paths=doc.get("paths"); edges=doc.get("transitions",[]); results=doc.get("path_results",[])
  if not isinstance(paths,list) or not paths or len(paths)>256 or not isinstance(edges,list) or not isinstance(results,list): raise EvidenceError("invalid v2 paths/transitions/path_results")
  pm={}
  for p in paths:
   if not isinstance(p,dict): raise EvidenceError("path must be object")
   pid=ident(p.get("id"),"path id"); seq=p.get("checkpoints")
   if pid in pm or not isinstance(seq,list) or not seq or len(seq)>256 or len(set(seq))!=len(seq) or any(x not in entries for x in seq): raise EvidenceError("invalid/duplicate path")
   if "required" in p and not isinstance(p["required"],bool): raise EvidenceError("path required must be boolean")
   pm[pid]=p
  em={}
  for e in edges:
   if not isinstance(e,dict): raise EvidenceError("transition must be object")
   a,b=ident(e.get("from"),"transition from"),ident(e.get("to"),"transition to")
   if a not in entries or b not in entries or a==b or (a,b) in em: raise EvidenceError("invalid/duplicate transition")
   if "required" in e and not isinstance(e["required"],bool): raise EvidenceError("transition required must be boolean")
   em[(a,b)]=e.get("required",True)
  for pid,p in pm.items():
   for edge in zip(p["checkpoints"],p["checkpoints"][1:]):
    if edge not in em: raise EvidenceError(pid+": undeclared path edge")
  rm={}
  for r in results:
   if not isinstance(r,dict): raise EvidenceError("path result must be object")
   pid=ident(r.get("path_id"),"path result id")
   if pid not in pm or pid in rm or r.get("status") not in STATUSES: raise EvidenceError("unknown/duplicate path result or invalid status")
   if digest(r.get("artifact_sha256"),"path artifact")!=art or r.get("source_sha")!=src: errors.append(pid+": source/artifact mismatch")
   if r.get("input_origin") not in ORIGINS: raise EvidenceError(pid+": invalid input origin")
   tr=r.get("trace")
   if not isinstance(tr,dict): raise EvidenceError(pid+": trace required")
   tf=confined(root,tr.get("path")); th=digest(tr.get("sha256"),"trace sha256")
   if r["status"]=="PASS" and (not tf.is_file() or hashlib.sha256(tf.read_bytes()).hexdigest()!=th): errors.append(pid+": trace missing/digest mismatch")
   obs=r.get("transitions",[])
   if not isinstance(obs,list): raise EvidenceError(pid+": observed transitions must be array")
   got=[]
   for x in obs:
    if not isinstance(x,dict): raise EvidenceError("observed transition must be object")
    pair=(ident(x.get("from"),"observed from"),ident(x.get("to"),"observed to"))
    if pair not in em: errors.append(pid+": undeclared observed transition")
    got.append(pair)
   if r["status"]=="PASS":
    if r["input_origin"] in ("MODEL_CALL","STATE_SETUP"): errors.append(pid+": non-player input cannot pass")
    if got!=list(zip(pm[pid]["checkpoints"],pm[pid]["checkpoints"][1:])): errors.append(pid+": observed path differs from declaration")
    if any(entries[x]["status"]!="PASS" or x in invalid for x in pm[pid]["checkpoints"]): errors.append(pid+": checkpoint stale/not PASS")
   rm[pid]=r
  reqp=[x for x,p in pm.items() if p.get("required",True)]
  passed=[x for x in reqp if x in rm and rm[x]["status"]=="PASS" and rm[x].get("input_origin") in ("OS_INPUT","BROWSER_INPUT","ENGINE_INPUT")]
  reqe=[e for e,r in em.items() if r]; covered=set()
  for r in rm.values():
   if r["status"]=="PASS" and r.get("input_origin") in ("OS_INPUT","BROWSER_INPUT","ENGINE_INPUT"):
    for e in r.get("transitions",[]): covered.add((e["from"],e["to"]))
  missing=sorted(a+"->"+b for a,b in reqe if (a,b) not in covered)
  coverage={"required_paths":len(reqp),"passed_paths":len(passed),"path_coverage":len(passed)/len(reqp) if reqp else 1.0,"required_transitions":len(reqe),"covered_transitions":sum(e in covered for e in reqe),"missing_paths":sorted(set(reqp)-set(passed)),"missing_transitions":missing}
  if require_path_coverage and (coverage["missing_paths"] or missing): errors.append("required path/transition coverage incomplete")
 return {"status":"PASS" if not errors else "FAIL","schema_version":v,"artifact_sha256":art,"source_sha":src,"checkpoints":len(steps),"required":len(required),"passed":sum(entries[x]["status"]=="PASS" and x not in invalid for x in required),"invalidated":sorted(invalid),"coverage":coverage,"errors":errors,"assurance":"EVIDENCE_INTEGRITY_AND_DECLARED_COVERAGE_ONLY_NOT_AUTONOMOUS_PLAY_PROOF"}
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("report",type=pathlib.Path); p.add_argument("--root",type=pathlib.Path,default=pathlib.Path.cwd()); p.add_argument("--changed",action="append",default=[]); p.add_argument("--expected-artifact"); p.add_argument("--require-completion",action="store_true"); p.add_argument("--require-path-coverage",action="store_true"); a=p.parse_args(argv)
 try: out=verify(json.loads(a.report.read_text(encoding="utf-8")),a.root.resolve(),changed=a.changed,require_completion=a.require_completion,expected_artifact=a.expected_artifact,require_path_coverage=a.require_path_coverage)
 except (ValueError,OSError,UnicodeError) as e: out={"status":"FAIL","errors":[str(e)]}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out["status"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
