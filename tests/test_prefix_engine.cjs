'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
test('independent endpoint-state BigInt reports match Fraction recurrence and enumerated-path native verifier',async()=>{
 await import(pathToFileURL(path.resolve(__dirname,'../docs/prefix-engine.js')));const engine=globalThis.CTC_PREFIX;
 const all=JSON.parse(execFileSync('python',['-c',`import random,json
from fractions import Fraction as F
from ctclab.prefix import audit_prefix
rng=random.Random(1783);reports=[]
for j in range(140):
 s=rng.randrange(2,5);frames=[]
 for t in range(rng.randrange(7)):
  v=[rng.randrange(7)for _ in range(s)]
  if not sum(v):v[0]=1
  frames.append([str(F(x,sum(v)))for x in v])
 reports.append(audit_prefix(dict(symbols=[str(i)for i in range(s)],blank=rng.randrange(s),frames=frames,beam_width=rng.choice([1,2,3,4,8,64]))))
from ctclab.prefix_controls import definitions
reports.extend(audit_prefix(c['request'])for c in definitions())
for w in [1,64]:reports.append(audit_prefix(dict(symbols=['_','A','B'],blank=0,frames=[['1/1000000','999999/1000000','0']]*6,beam_width=w)))
reports.append(audit_prefix(dict(symbols=['a','b','c','_'],blank=3,frames=[['1/4']*4]*6,beam_width=64)))
print(json.dumps(reports))`],{cwd:path.join(__dirname,'..'),maxBuffer:64*1024*1024}));let candidates=0,transitions=0,transcripts=0;const output=[];
 for(const r of all){const before=JSON.stringify(r.request),actual=engine.inspect(engine.parse(before));assert.deepEqual(actual,r);assert.equal(JSON.stringify(r.request),before);output.push(actual);candidates+=r.steps.reduce((s,x)=>s+x.candidates.length,0);transitions+=r.steps.reduce((s,x)=>s+x.transitions.length,0);transcripts+=r.transcripts.length;}
 assert.equal(execFileSync('python',['-c',`import sys,json
from ctclab.prefix_verify import verify_prefix
for r in json.load(sys.stdin):verify_prefix(r)
print('valid')`],{cwd:path.join(__dirname,'..'),input:JSON.stringify(output),maxBuffer:64*1024*1024}).toString().trim(),'valid');console.log(JSON.stringify({reports:all.length,candidates,transitions,transcripts}));
});
test('strict duplicate/noninteger JSON, probability/schema and hostile key refusal',async()=>{
 await import(pathToFileURL(path.resolve(__dirname,'../docs/prefix-engine.js')));const e=globalThis.CTC_PREFIX;
 for(const x of ['{"blank":0.0}','{"beam_width":1e0}','{"a":1,"a":2}','{"x":NaN}','['.repeat(1200)])assert.throws(()=>e.parse(x));
 for(const x of [{symbols:['_','A'],blank:0,frames:[['2/4','1/2']],beam_width:1},{symbols:['_','A'],blank:true,frames:[],beam_width:1},{symbols:['_','A'],blank:0,frames:[['1/2','1/3']],beam_width:1}])assert.throws(()=>e.inspect(x));
 assert.throws(()=>e.inspect(e.parse('{"__proto__":{},"symbols":["_","A"],"blank":0,"frames":[],"beam_width":1}')));assert.equal({}.polluted,undefined);
});
