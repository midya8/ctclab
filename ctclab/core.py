"""Established CTC, log-space target marginalization and bounded exact path witnesses."""
import itertools,json,math
NEG=-math.inf

def logsum(xs):
 xs=list(xs);m=max(xs,default=NEG)
 return NEG if m==NEG else m+math.log(math.fsum(math.exp(x-m) for x in xs))

def collapse(path,blank):
 return [x for i,x in enumerate(path) if x!=blank and (i==0 or path[i-1]!=x)]

def validate(spec):
 if not isinstance(spec,dict) or set(spec)!={'symbols','blank','logits','target'}:raise ValueError('Exact fields: symbols, blank, logits, target')
 symbols=spec['symbols'];c=len(symbols) if isinstance(symbols,list) else 0
 if not 2<=c<=4 or any(not isinstance(s,str) or not 1<=len(s)<=12 or any(ord(x)<33 or ord(x)>126 for x in s) for s in symbols) or len(set(symbols))!=c:raise ValueError('Two to four unique printable ASCII symbol labels, length 1..12')
 blank=spec['blank'];target=spec['target'];z=spec['logits']
 integer=lambda x:not isinstance(x,bool) and (isinstance(x,int) or (isinstance(x,float) and math.isfinite(x) and x==int(x)))
 if not integer(blank) or not 0<=blank<c:raise ValueError('Blank must be a symbol index')
 if not isinstance(target,list) or len(target)>6 or any(not integer(x) or not 0<=x<c or x==blank for x in target):raise ValueError('At most six target labels, excluding blank')
 if not isinstance(z,list) or len(z)>6 or c**len(z)>1024:raise ValueError('At most six frames and 1024 exhaustive paths')
 for row in z:
  if not isinstance(row,list) or len(row)!=c or any(isinstance(x,bool) or not isinstance(x,(int,float)) or abs(x)>1e6 or not math.isfinite(x) for x in row):raise ValueError('Rectangular finite numeric logits bounded by 1e6')
 return c,int(blank),[int(x) for x in target],z

def _marginal(logits,target,blank=0):
 """Finite logits. Alpha includes current emission; beta excludes it. No batch reduction."""
 c=len(logits[0]) if logits else max([blank]+list(target))+1
 logs=[[x-logsum(row) for x in row] for row in logits];p=[[math.exp(x) for x in row] for row in logs]
 ext=[blank]
 for x in target:ext += [x,blank]
 n=len(ext);t=len(logits)
 edges=[(s,d) for s in range(n) for d in [s,s+1,s+2] if d<n and (d!=s+2 or (ext[d]!=blank and ext[d]!=ext[s]))]
 incoming=[[s for s,d in edges if d==k] for k in range(n)];outgoing=[[d for s,d in edges if s==k] for k in range(n)]
 alpha=[[NEG]*n for _ in range(t)];beta=[[NEG]*n for _ in range(t)]
 ends=[n-1] if n==1 else [n-2,n-1]
 if t:
  alpha[0][0]=logs[0][blank]
  if n>1:alpha[0][1]=logs[0][ext[1]]
  for i in range(1,t):
   for s in range(n):alpha[i][s]=logs[i][ext[s]]+logsum(alpha[i-1][q] for q in incoming[s])
  for s in ends:beta[-1][s]=0.
  for i in range(t-2,-1,-1):
   for s in range(n):beta[i][s]=logsum(logs[i+1][ext[d]]+beta[i+1][d] for d in outgoing[s])
  logz=logsum(alpha[-1][s] for s in ends)
 else:logz=0. if not target else NEG
 possible=logz!=NEG
 statepost=[[math.exp(alpha[i][s]+beta[i][s]-logz) for s in range(n)] for i in range(t)] if possible else None
 labelpost=[[math.fsum(statepost[i][s] for s in range(n) if ext[s]==k) for k in range(c)] for i in range(t)] if possible else None
 grad=[[p[i][k]-labelpost[i][k] for k in range(c)] for i in range(t)] if possible else None
 clean=lambda mat:[[None if x==NEG else x for x in row] for row in mat]
 return dict(log_probabilities=logs,probabilities=p,extended_target=ext,transitions=[list(e) for e in edges],alpha=clean(alpha),beta=clean(beta),possible=possible,minimum_frames=len(target)+sum(a==b for a,b in zip(target,target[1:])),log_probability=logz if possible else None,probability=math.exp(logz) if possible else 0.,loss=-logz if possible else None,state_posteriors=statepost,label_posteriors=labelpost,logit_gradients=grad)

def audit(spec):
 c,b,y,z=validate(spec);m=_marginal(z,y,b);logs=m['log_probabilities'];paths=[];groups={}
 for path in itertools.product(range(c),repeat=len(z)):
  out=collapse(path,b);lp=math.fsum(logs[t][x] for t,x in enumerate(path));key=tuple(out);groups.setdefault(key,[]).append(lp)
  paths.append(dict(path=list(path),collapsed=out,log_probability=lp,probability=math.exp(lp),matches=out==y))
 outputs=[dict(labels=list(k),log_probability=logsum(v),probability=math.exp(logsum(v)),path_count=len(v),rank_bucket=math.floor(logsum(v)*1e8+0.5)) for k,v in groups.items()]
 outputs.sort(key=lambda r:(-r['rank_bucket'],r['labels']))
 greedy=[max(range(c),key=lambda k:(z[t][k],-k)) for t in range(len(z))]
 matched=[p for p in paths if p['matches']];oracle=logsum(p['log_probability'] for p in matched)
 return dict(schema_version=1,ranking_resolution_nats=1e-8,spec=json.loads(json.dumps(spec)),dynamic=m,paths=paths,outputs=outputs,oracle=dict(path_count=len(paths),matched_count=len(matched),log_probability=None if oracle==NEG else oracle,probability=0. if oracle==NEG else math.exp(oracle)),greedy=dict(path=greedy,collapsed=collapse(greedy,b)),best_output=outputs[0],greedy_is_canonical_best=collapse(greedy,b)==outputs[0]['labels'],greedy_output_log_probability=next(o['log_probability'] for o in outputs if o['labels']==collapse(greedy,b)),greedy_log_gap=max(o['log_probability'] for o in outputs)-next(o['log_probability'] for o in outputs if o['labels']==collapse(greedy,b)))
