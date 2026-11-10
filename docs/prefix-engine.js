'use strict';
(function(root){
const gcd=(a,b)=>{a=a<0n?-a:a;while(b){[a,b]=[b,a%b];}return a;};
class Q{
 constructor(n,d=1n){if(!d)throw Error('Zero denominator');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);this.n=n/g;this.d=d/g;}
 static parse(x,bounded=false){if(typeof x!=='string'||x.length>(bounded?16:2500)||! /^-?(?:0|[1-9]\d*)(?:\/[1-9]\d*)?$/.test(x))throw Error('Canonical rational string required');const p=x.split('/'),q=new Q(BigInt(p[0]),p.length===1?1n:BigInt(p[1]));if(q.toString()!==x||(bounded&&((q.n<0n?-q.n:q.n)>1000000n||q.d>1000000n)))throw Error('Bounded reduced rational required');return q;}
 add(x){return new Q(this.n*x.d+x.n*this.d,this.d*x.d);} sub(x){return new Q(this.n*x.d-x.n*this.d,this.d*x.d);} mul(x){return new Q(this.n*x.n,this.d*x.d);} div(x){return new Q(this.n*x.d,this.d*x.n);} cmp(x){const d=this.n*x.d-x.n*this.d;return d<0n?-1:d>0n?1:0;} toString(){return String(this.n)+(this.d===1n?'':'/'+this.d);}
}
const q=x=>new Q(BigInt(x)),sum=a=>a.reduce((s,x)=>s.add(x),q(0)),keys=(x,w)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join('|')===w.slice().sort().join('|');

function parse(text){
 if(typeof text!=='string'||new TextEncoder().encode(text).length>65536)throw Error('Input exceeds65536bytes');
 let i=0;const ws=()=>{while(i<text.length&&/[\x20\t\r\n]/.test(text[i]))i++;};
 function value(path){ws();const c=text[i];if(c==='"'){const start=i++;let escaped=false;for(;i<text.length;i++){const ch=text[i];if(!escaped&&ch==='"'){i++;return JSON.parse(text.slice(start,i));}if(!escaped&&ch==='\\')escaped=true;else escaped=false;}throw Error('Unterminated JSON string');}
 if(c==='['){i++;ws();const a=[];if(text[i]===']'){i++;return a;}for(;;){a.push(value([...path,a.length]));ws();if(text[i]===']'){i++;return a;}if(text[i++]!==',')throw Error('Expected array comma');}}
 if(c==='{'){i++;ws();const o={},keys=new Set();if(text[i]==='}'){i++;return o;}for(;;){ws();if(text[i]!=='"')throw Error('Object key must be a string');const k=value(path);if(keys.has(k))throw Error('Duplicate JSON key: '+k);keys.add(k);ws();if(text[i++]!==':')throw Error('Expected colon');Object.defineProperty(o,k,{value:value([...path,k]),writable:true,enumerable:true,configurable:true});ws();if(text[i]==='}'){i++;return o;}if(text[i++]!==',')throw Error('Expected object comma');}}
 for(const [token,result]of [['true',true],['false',false],['null',null]])if(text.startsWith(token,i)){i+=token.length;return result;}
 const token=text.slice(i).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);if(!token)throw Error('Invalid JSON value');i+=token[0].length;const result=Number(token[0]);if(!Number.isFinite(result))throw Error('Nonfinite JSON number');if(!/^-?(?:0|[1-9]\d*)$/.test(token[0]))throw Error('Integer JSON tokens required');return result;
 }
 const r=value([]);ws();if(i!==text.length)throw Error('Trailing JSON content');return r;
}

const scope='Supplied independent-frame CTC law; exact rational arithmetic. Beam mass is surviving path mass, not renormalized transcript probability or calibrated confidence. No model, language model, recognition benchmark or new method.';
function validate(r){
 if(!keys(r,['symbols','blank','frames','beam_width']))throw Error('Exactly symbols, blank, frames, beam_width required');
 if(!Array.isArray(r.symbols)||r.symbols.length<2||r.symbols.length>4||r.symbols.some(x=>typeof x!=='string'||! /^[!-~]{1,12}$/.test(x))||new Set(r.symbols).size!==r.symbols.length)throw Error('2..4 unique bounded printable nonspace ASCII labels required');
 if(!Number.isInteger(r.blank)||r.blank<0||r.blank>=r.symbols.length)throw Error('Integer blank index required');
 if(!Number.isInteger(r.beam_width)||r.beam_width<1||r.beam_width>64)throw Error('Integer beam width 1..64 required');
 if(!Array.isArray(r.frames)||r.frames.length>6)throw Error('0..6 frames required');
 return r.frames.map(row=>{if(!Array.isArray(row)||row.length!==r.symbols.length)throw Error('Aligned frame required');const a=row.map(x=>Q.parse(x,true));if(a.some(x=>x.cmp(q(0))<0||x.cmp(q(1))>0)||sum(a).cmp(q(1)))throw Error('Each frame must be exact probability law');return a;});
}
const lex=(a,b)=>{for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length;};
function order(states){return [...states.values()].sort((a,b)=>sum(b.m).cmp(sum(a.m))||lex(a.p,b.p));}
function stateMachine(states,row,blank,withEdges){
 const next=new Map(),edge=new Map();
 for(const old of states.values())for(let end=0;end<2;end++)for(let c=0;c<row.length;c++){
  const mass=old.m[end].mul(row[c]);if(!mass.n)continue;
  const repeat=c!==blank&&old.p.length&&old.p.at(-1)===c;
  const p=c===blank||(repeat&&end===1)?old.p:old.p.concat(c),endpoint=c===blank?0:1;
  const k=JSON.stringify(p);if(!next.has(k))next.set(k,{p,m:[q(0),q(0)]});next.get(k).m[endpoint]=next.get(k).m[endpoint].add(mass);
  if(withEdges){const kind=c===blank?'blank':repeat&&end===1?'continue_run':repeat?'repeat_after_blank':'extend';const ek=JSON.stringify([old.p,p,kind,c,endpoint]);if(!edge.has(ek))edge.set(ek,{source:old.p,destination:p,kind,token:c,endpoint:endpoint?'nonblank':'blank',mass:q(0)});edge.get(ek).mass=edge.get(ek).mass.add(mass);}
 }
 const edges=[...edge.values()].sort((a,b)=>lex(a.source,b.source)||(a.kind==='blank'?0:1)-(b.kind==='blank'?0:1)||a.token-b.token||(a.kind==='continue_run'?0:1)-(b.kind==='continue_run'?0:1)).map(x=>({...x,mass:String(x.mass)}));return {next,edges};
}
function inspect(request){
 const rows=validate(request),r=JSON.parse(JSON.stringify(request));let full=new Map([['[]',{p:[],m:[q(1),q(0)]}]]),beam=new Map(full),total=q(1);const steps=[];
 for(let t=0;t<rows.length;t++){
  full=stateMachine(full,rows[t],r.blank,false).next;const {next,edges}=stateMachine(beam,rows[t],r.blank,true),ranked=order(next),keep=new Set(ranked.slice(0,r.beam_width).map(x=>JSON.stringify(x.p))),retained=sum(ranked.filter(x=>keep.has(JSON.stringify(x.p))).map(x=>sum(x.m)));
  steps.push({frame:t,incoming_mass:String(total),candidate_mass:String(sum(ranked.map(x=>sum(x.m)))),discarded_here:String(total.sub(retained)),retained_mass:String(retained),discarded_total:String(q(1).sub(retained)),transitions:edges,candidates:ranked.map((x,j)=>{const f=sum(full.get(JSON.stringify(x.p)).m),v=sum(x.m);return {prefix:x.p,blank_mass:String(x.m[0]),nonblank_mass:String(x.m[1]),mass:String(v),full_mass:String(f),missing_mass:String(f.sub(v)),rank:j+1,kept:keep.has(JSON.stringify(x.p))};})});
  beam=new Map(ranked.slice(0,r.beam_width).map(x=>[JSON.stringify(x.p),x]));total=retained;
 }
 const ranked=order(beam),winner=ranked[0],sorted=order(full),best=sum(sorted[0].m),lower=sum(winner.m),lost=q(1).sub(total),runner=ranked.length>1?sum(ranked[1].m):q(0);
 const greedy=rows.map(row=>row.reduce((best,x,c)=>x.cmp(row[best])>0?c:best,0)),collapsed=greedy.filter((c,t)=>c!==r.blank&&(!t||c!==greedy[t-1])),winnerFull=sum(full.get(JSON.stringify(winner.p)).m);
 return {schema:'ctclab-rational-prefix-v1',scope,request:r,steps,greedy_path:greedy,greedy_transcript:collapsed,greedy_transcript_mass:String(sum(full.get(JSON.stringify(collapsed))?.m||[q(0)])),beam_winner:winner.p,beam_winner_retained_mass:String(lower),beam_winner_full_mass:String(winnerFull),exact_winners:sorted.filter(x=>sum(x.m).cmp(best)===0).map(x=>x.p),exact_best_mass:String(best),exact_regret:String(best.sub(winnerFull)),retained_mass:String(total),discarded_mass:String(lost),other_retained_max:String(runner),sufficient_unique_map:lower.cmp(runner.add(lost))>0,transcripts:sorted.map((x,j)=>{const fullMass=sum(x.m),retainedMass=sum(beam.get(JSON.stringify(x.p))?.m||[q(0)]);return {prefix:x.p,full_mass:String(fullMass),retained_mass:String(retainedMass),missing_mass:String(fullMass.sub(retainedMass)),exact_rank:j+1};})};
}
root.CTC_PREFIX={inspect,parse,validate,Q};if(typeof module!=='undefined')module.exports=root.CTC_PREFIX;
})(globalThis);
