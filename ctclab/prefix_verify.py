"""Independent path-enumerating verifier; never imports prefix generator."""
from fractions import Fraction as F
from itertools import product
from .prefix_input import SCHEMA, SCOPE, validate


def _collapse(path, blank):
    return tuple(c for t,c in enumerate(path) if c != blank and (not t or c != path[t-1]))


def _equal(actual, expected):
    if type(actual) is not type(expected):
        raise ValueError('Evidence primitive/container type mismatch')
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError('Evidence fields mismatch')
        for k in expected:
            _equal(actual[k], expected[k])
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError('Evidence sequence length mismatch')
        for a,b in zip(actual,expected):
            _equal(a,b)
    elif actual != expected:
        raise ValueError('Evidence value mismatch')


def verify_prefix(report):
    if type(report) is not dict or 'request' not in report:
        raise ValueError('Report required')
    request=report['request'];rows=validate(request);blank=request['blank'];width=request['beam_width'];S=len(request['symbols'])
    # Enumerate independent complete frame paths, carrying survival at each cut.
    live={():F(1)};steps=[];full={():[F(1),F(0)]};total=F(1)
    for t,row in enumerate(rows):
        full={};candidates={};edge_mass={};extensions={}
        for path in product(range(S),repeat=t+1):
            mass=F(1)
            for j,c in enumerate(path):mass*=rows[j][c]
            if not mass:continue
            p=_collapse(path,blank);end=0 if path[-1]==blank else 1
            full.setdefault(p,[F(0),F(0)])[end]+=mass
            if path[:-1] not in live:continue
            extensions[path]=mass;candidates.setdefault(p,[F(0),F(0)])[end]+=mass
            old=_collapse(path[:-1],blank);c=path[-1]
            kind=('blank'if c==blank else 'continue_run'if path[:-1] and path[-2]==c else 'repeat_after_blank'if old and old[-1]==c else 'extend')
            key=(old,p,kind,c,end);edge_mass[key]=edge_mass.get(key,F(0))+mass
        ordered=sorted(candidates,key=lambda p:(-sum(candidates[p]),p));chosen=set(ordered[:width]);retained=sum((sum(candidates[p])for p in chosen),F(0))
        edges=[]
        # Fixed semantic order independent of path enumeration order.
        for old in sorted({_collapse(path,blank)for path in live}):
            keys=[k for k in edge_mass if k[0]==old]
            keys.sort(key=lambda k:(0 if k[2]=='blank'else 1,k[3],0 if k[2]=='continue_run'else 1))
            for key in keys:
                source,destination,kind,token,endpoint=key
                edges.append(dict(source=list(source),destination=list(destination),kind=kind,token=token,endpoint='blank'if endpoint==0 else 'nonblank',mass=str(edge_mass[key])))
        records=[dict(prefix=list(p),blank_mass=str(candidates[p][0]),nonblank_mass=str(candidates[p][1]),mass=str(sum(candidates[p])),full_mass=str(sum(full[p])),missing_mass=str(sum(full[p])-sum(candidates[p])),rank=j+1,kept=p in chosen)for j,p in enumerate(ordered)]
        steps.append(dict(frame=t,incoming_mass=str(total),candidate_mass=str(sum((sum(v)for v in candidates.values()),F(0))),discarded_here=str(total-retained),retained_mass=str(retained),discarded_total=str(1-retained),transitions=edges,candidates=records))
        live={path:mass for path,mass in extensions.items()if _collapse(path,blank)in chosen};total=retained
    beam={}
    for path,mass in live.items():
        p=_collapse(path,blank);beam[p]=beam.get(p,F(0))+mass
    winner=min(beam,key=lambda p:(-beam[p],p));order=sorted(full,key=lambda p:(-sum(full[p]),p));best=sum(full[order[0]])
    greedy=[min(range(S),key=lambda c:(-row[c],c))for row in rows];gp=_collapse(greedy,blank);lost=1-total;runner=max((m for p,m in beam.items()if p!=winner),default=F(0))
    expected=dict(schema=SCHEMA,scope=SCOPE,request=request,steps=steps,greedy_path=greedy,greedy_transcript=list(gp),greedy_transcript_mass=str(sum(full.get(gp,[F(0)]))),beam_winner=list(winner),beam_winner_retained_mass=str(beam[winner]),beam_winner_full_mass=str(sum(full[winner])),exact_winners=[list(p)for p in order if sum(full[p])==best],exact_best_mass=str(best),exact_regret=str(best-sum(full[winner])),retained_mass=str(total),discarded_mass=str(lost),other_retained_max=str(runner),sufficient_unique_map=beam[winner]>runner+lost,transcripts=[dict(prefix=list(p),full_mass=str(sum(full[p])),retained_mass=str(beam.get(p,F(0))),missing_mass=str(sum(full[p])-beam.get(p,F(0))),exact_rank=j+1)for j,p in enumerate(order)])
    _equal(report,expected)
    return True
