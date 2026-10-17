#!/usr/bin/env node
// Adversarial policy diagnostic against an imported, authoritative game core.
// This is not a human fun score, normal-browser test, or game-exp gate.
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath, pathToFileURL} from 'node:url';

const KINDS = new Set(['idle','hold-jump','jump-pulse','right-jump',
                       'edge-camp','micro-scout','dash-spam','custom']);
const KEYS = ['left','right','jump','dash'];
function demand(ok, why) {if(!ok) throw Error(why);}
function pos(value, why) {demand(Number.isInteger(value)&&value>0,why); return value;}
function empty() {return {left:false,right:false,jump:false,dash:false};}
function pulse(tick, every) {return tick%pos(every,'pulse_every must be a positive integer')===0;}

export function validateConfig(c) {
  demand(c && c.schema_version===1,'schema_version must be 1');
  demand(typeof c.adapter==='string' && c.adapter.length>0,'adapter path required');
  demand(typeof c.source_id==='string' && c.source_id.length>0,'tested source_id required');
  demand(pos(c.dt_ms,'dt_ms must be positive')<=2000,'dt_ms must be <= 2000');
  pos(c.max_steps,'max_steps must be positive');
  demand(Array.isArray(c.scenarios)&&c.scenarios.length>0,'scenarios required');
  demand(Array.isArray(c.policies)&&c.policies.length>0,'policies required');
  const ids=new Set();
  for(const s of c.scenarios){
    demand(typeof s.id==='string'&&s.id.length>0&&!ids.has(s.id),'unique scenario id required');
    ids.add(s.id);
    demand(Array.isArray(s.seeds)&&s.seeds.length>0,'seeds required');
    demand(s.seeds.every(Number.isSafeInteger),'each seed must be an integer');
    demand(new Set(s.seeds).size===s.seeds.length,'duplicate seed');
  }
  const names=new Set();
  for(const p of c.policies){
    demand(typeof p.name==='string'&&p.name.length>0&&!names.has(p.name),'unique policy name required');
    names.add(p.name);
    demand(KINDS.has(p.kind),'unsupported policy kind: '+p.kind);
    demand(p.max_win_rate==null || (typeof p.max_win_rate==='number' &&
      p.max_win_rate>=0 && p.max_win_rate<=1),'max_win_rate must be 0..1');
  }
}
function actionFor(p,t,seen) {
  const a=empty(), every=p.pulse_every??12;
  switch(p.kind) {
    case 'idle': return a;
    case 'hold-jump': a.jump=true; return a;
    case 'jump-pulse': a.jump=pulse(t,every); return a;
    case 'right-jump': a.right=true; a.jump=pulse(t,every); return a;
    case 'edge-camp':
      demand(Number.isFinite(p.edge_x)&&Number.isFinite(seen.x),
        'edge-camp requires numeric edge_x and observed x');
      a.right=seen.x<p.edge_x;
      a.jump=!a.right && pulse(t,every);
      return a;
    case 'micro-scout':
      a.left=Math.floor(t/pos(p.half_cycle_ticks??2,'half_cycle_ticks invalid'))%2===0;
      a.right=!a.left;
      a.jump=pulse(t,every);
      return a;
    case 'dash-spam':
      a.right=true;
      a.dash=pulse(t,every);
      a.jump=pulse(t,p.jump_every??20);
      return a;
    default: throw Error('custom policy must be supplied by adapter');
  }
}
function checkAction(a) {
  demand(a && typeof a==='object' && !Array.isArray(a) &&
    KEYS.every(k=>typeof a[k]==='boolean'),'input must contain left/right/jump/dash booleans');
}
function checkState(s) {
  demand(s && typeof s==='object' && !Array.isArray(s) &&
    ['PLAYING','WIN','LOSE'].includes(s.status),'observe status must be PLAYING/WIN/LOSE');
  if(s.x!==undefined) demand(Number.isFinite(s.x),'observed x must be finite');
  if(s.progress!==undefined) demand(Number.isFinite(s.progress),'progress must be finite');
}
async function oneRun(adapter,scenario,seed,policy,c) {
  const session=await adapter.createSession({scenario:scenario.id,seed});
  demand(session && typeof session.step==='function'&&
    typeof session.observe==='function','createSession must return step/observe');
  let seen=await session.observe();
  checkState(seen);
  let steps=0, highest=seen.progress??null, truncated=false;
  const trace=[], counts={left:0,right:0,jump:0,dash:0}, markers=new Set();
  if(typeof seen.decision_marker==='string') markers.add(seen.decision_marker);
  for(let tick=0;tick<c.max_steps&&seen.status==='PLAYING';tick++){
    const input=policy.kind==='custom'
      ? await adapter.customPolicy(policy.name,{tick,observed:seen,scenario:scenario.id,seed})
      : actionFor(policy,tick,seen);
    checkAction(input);
    for(const key of KEYS) if(input[key]) counts[key]++;
    const result=await session.step(input,c.dt_ms);
    seen=result===undefined?await session.observe():result;
    checkState(seen);
    steps=tick+1;
    if(Number.isFinite(seen.progress))
      highest=highest===null?seen.progress:Math.max(highest,seen.progress);
    if(typeof seen.decision_marker==='string') markers.add(seen.decision_marker);
    if((KEYS.some(k=>input[k])&&(tick===0||input.jump||input.dash||tick%16===0))
      ||seen.status!=='PLAYING'){
      if(trace.length<120) trace.push({tick,action:input,status:seen.status,
        x:seen.x??null,progress:seen.progress??null});
      else truncated=true;
    }
  }
  return {scenario:scenario.id,seed,policy:policy.name,status:seen.status,
    won:seen.status==='WIN',terminal:seen.status!=='PLAYING',steps,
    max_progress:highest,action_counts:counts,
    distinct_observed_markers:markers.size,trace,trace_truncated:truncated};
}
export async function runProbes(c, configPath) {
  validateConfig(c);
  const modulePath=path.resolve(path.dirname(configPath),c.adapter);
  const adapter=await import(pathToFileURL(modulePath).href);
  demand(typeof adapter.createSession==='function','adapter must export createSession');
  if(c.policies.some(p=>p.kind==='custom'))
    demand(typeof adapter.customPolicy==='function','adapter must export customPolicy');
  const attempts=[],errors=[];
  for(const scenario of c.scenarios) for(const seed of scenario.seeds)
    for(const policy of c.policies){
      try {attempts.push(await oneRun(adapter,scenario,seed,policy,c));}
      catch(err) {errors.push({scenario:scenario.id,seed,policy:policy.name,
        message:String(err?.message??err)});}
    }
  const policies=c.policies.map(p=>{
    const rows=attempts.filter(a=>a.policy===p.name), wins=rows.filter(a=>a.won).length;
    const ceiling=p.max_win_rate??null, rate=rows.length?wins/rows.length:null;
    return {policy:p.name,kind:p.kind,completed_runs:rows.length,wins,
      win_rate:rate,max_expected_win_rate:ceiling,
      unexpected_success:ceiling!==null&&rate!==null&&rate>ceiling};
  });
  const violations=policies.filter(p=>p.unexpected_success).map(p=>({
    code:'TRIVIAL_POLICY_OVERSUCCEEDS',policy:p.policy,win_rate:p.win_rate,
    declared_ceiling:p.max_expected_win_rate}));
  const verdict=errors.length?'RUNTIME_ERRORS':violations.length?'RISK_DETECTED':
    policies.some(p=>p.max_expected_win_rate!==null)
    ? 'NO_DECLARED_LIMIT_BREACHED':'UNSCOPED_DIAGNOSTIC';
  return {schema_version:1,kind:'strategy_degeneracy_diagnostic',source_id:c.source_id,
    adapter:c.adapter,dt_ms:c.dt_ms,max_steps:c.max_steps,verdict,
    scenarios:c.scenarios,policies,violations,attempts,errors,limitations:[
      'Headless production-core diagnostic; not a real browser input path.',
      'Policy success never proves perceived fun, difficulty or player preference.',
      'No declared limit breached is not a universal exploit-resistance PASS.',
      'Missing decision markers only indicates missing instrumentation.'
    ]};
}
async function cli() {
  try {
    const args=process.argv.slice(2), parsed={};
    for(let i=0;i<args.length;i++){
      demand(['--config','--out'].includes(args[i]),'unknown argument: '+args[i]);
      demand(i+1<args.length,'missing value for '+args[i]);
      parsed[args[i].slice(2)]=args[++i];
    }
    demand(parsed.config&&parsed.out,'usage: --config config.json --out report.json');
    const configPath=path.resolve(parsed.config);
    const config=JSON.parse(await fs.readFile(configPath,'utf8'));
    const report=await runProbes(config,configPath);
    await fs.mkdir(path.dirname(path.resolve(parsed.out)),{recursive:true});
    await fs.writeFile(parsed.out,JSON.stringify(report,null,2)+'\n');
    process.stdout.write(report.verdict+': '+report.attempts.length+' runs, '+
      report.errors.length+' runtime errors\n');
    process.exitCode=report.errors.length?2:report.violations.length?1:0;
  } catch(err){
    console.error('Invalid strategy probe: '+String(err?.message??err));
    process.exitCode=3;
  }
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url))
  await cli();
