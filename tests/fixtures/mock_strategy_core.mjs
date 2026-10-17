// Synthetic adapter: never treat this fixture as real player or gameplay evidence.
export function createSession({scenario}) {
  let x=0, presses=0, priorJump=false, status='PLAYING', ticks=0;
  return {
    observe(){
      return {x,progress:x,status,decision_marker:scenario+':'+Math.floor(x/3)};
    },
    step(a,dtMs) {
      if(!Number.isFinite(dtMs)||dtMs<=0)throw Error('invalid timestep');
      if(a.right)x++;
      if(a.left)x--;
      if(a.jump&&!priorJump)presses++;
      priorJump=a.jump;
      ticks++;
      if(scenario==='shortcut' && presses>=3) status='WIN';
      else if(scenario==='legitimate' && x>=9 && presses>=3) status='WIN';
      else if(!['shortcut','legitimate'].includes(scenario))throw Error('unknown fixture');
      if(ticks>500)status='LOSE';
      return this.observe();
    }
  };
}
