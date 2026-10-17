import assert from 'node:assert/strict';
import {test} from 'node:test';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {runProbes,validateConfig} from '../scripts/run_strategy_probes.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const fixture='./fixtures/mock_strategy_core.mjs';
const base={
  schema_version:1,adapter:fixture,source_id:'synthetic-fixture-only',dt_ms:16,
  max_steps:40,scenarios:[{id:'shortcut',seeds:[101,202,303]}],
  policies:[
    {name:'jump-only',kind:'jump-pulse',pulse_every:2,max_win_rate:0.1},
    {name:'right-jump',kind:'right-jump',pulse_every:2,max_win_rate:1}
  ]
};
const configPath=path.join(here,'example-config.json');

test('repeated jump finds same-seed shortcut',async()=>{
  const r=await runProbes(base,configPath);
  assert.equal(r.verdict,'RISK_DETECTED');
  assert.equal(r.attempts.length,6);
  assert.equal(r.errors.length,0);
  assert.equal(r.policies[0].win_rate,1);
  assert.equal(r.violations[0].policy,'jump-only');
  assert.ok(r.attempts.every(x=>x.trace.length>0));
});
test('legitimate input succeeds without mislabeling fun',async()=>{
  const r=await runProbes({...base,scenarios:[{id:'legitimate',seeds:[1,2]}]},configPath);
  assert.equal(r.verdict,'NO_DECLARED_LIMIT_BREACHED');
  assert.equal(r.policies[0].win_rate,0);
  assert.equal(r.policies[1].win_rate,1);
  assert.match(r.limitations.join(' '),/not a universal/);
});
test('undeclared ceilings are diagnostic, never PASS',async()=>{
  const r=await runProbes({...base,policies:[{name:'idle',kind:'idle'}]},configPath);
  assert.equal(r.verdict,'UNSCOPED_DIAGNOSTIC');
});
test('edge-camp and micro-scout work on observed state',async()=>{
  const c={...base,policies:[
    {name:'edge',kind:'edge-camp',edge_x:3,pulse_every:2,max_win_rate:1},
    {name:'micro',kind:'micro-scout',half_cycle_ticks:2,pulse_every:2,max_win_rate:1}
  ]};
  const r=await runProbes(c,configPath);
  assert.equal(r.errors.length,0);
  assert.equal(r.attempts.length,6);
});
test('invalid schemas are rejected',()=>{
  assert.throws(()=>validateConfig({...base,source_id:''}),/source_id/);
  assert.throws(()=>validateConfig({...base,scenarios:[{id:'x',seeds:[1,1]}]}),/duplicate seed/);
  assert.throws(()=>validateConfig({...base,policies:[{name:'x',kind:'cheat'}]}),/unsupported policy/);
});
test('CLI exit 1 and reproducible JSON on declared shortcut',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'h5-strategy-'));
  try{
    const cfg=path.join(dir,'config.json'),out=path.join(dir,'report.json');
    const args={...base,adapter:path.join(here,'fixtures/mock_strategy_core.mjs')};
    await fs.writeFile(cfg,JSON.stringify(args));
    const run=spawnSync(process.execPath,[path.join(here,'../scripts/run_strategy_probes.mjs'),
      '--config',cfg,'--out',out],{encoding:'utf8'});
    assert.equal(run.status,1,run.stderr);
    const report=JSON.parse(await fs.readFile(out,'utf8'));
    assert.equal(report.verdict,'RISK_DETECTED');
  }finally{await fs.rm(dir,{recursive:true,force:true});}
});
