import unittest,math,itertools,random,json,tempfile,subprocess,sys
from decimal import Decimal,localcontext
from pathlib import Path
from ctclab import audit,collapse
R=Path(__file__).resolve().parents[1]
def spec(z,y=(),b=0,c=3):return dict(symbols=['s'+str(i) for i in range(c)],blank=b,logits=z,target=list(y))
def independent_collapse(p,b):return [k for k,g in itertools.groupby(p) if k!=b]
class CTC(unittest.TestCase):
 def test_collapse_order(self):
  self.assertEqual(collapse([1,1,0,1,2,2],0),[1,1,2]);self.assertEqual(collapse([0,0],0),[])
 def test_every_collapse_small(self):
  for t in range(7):
   for p in itertools.product(range(3),repeat=t):self.assertEqual(collapse(p,0),independent_collapse(p,0))
 def test_decimal_path_probability_posteriors(self):
  rng=random.Random(13);checked=0
  with localcontext() as ctx:
   ctx.prec=90
   for i in range(90):
    c=2+i%3;t=1+i%4;b=i%c;labels=[k for k in range(c) if k!=b];y=[rng.choice(labels) for _ in range(i%3)];z=[[rng.randint(-4,4) for _ in range(c)] for _ in range(t)];r=audit(spec(z,y,b,c));p=[]
    for row in z:
     v=[Decimal(x).exp() for x in row];p.append([x/sum(v) for x in v])
    masses=[];post=[[Decimal(0)]*c for _ in range(t)]
    for path in itertools.product(range(c),repeat=t):
     if independent_collapse(path,b)!=y:continue
     mass=math.prod(p[j][k] for j,k in enumerate(path));masses.append(mass)
     for j,k in enumerate(path):post[j][k]+=mass
    total=sum(masses);self.assertEqual(r['dynamic']['possible'],bool(total));self.assertAlmostEqual(r['oracle']['probability'],float(total),places=13)
    if total:
     self.assertAlmostEqual(r['dynamic']['loss'],float(-total.ln()),places=12)
     for j in range(t):
      self.assertAlmostEqual(sum(r['dynamic']['state_posteriors'][j]),1,places=12)
      for k in range(c):
       self.assertAlmostEqual(r['dynamic']['label_posteriors'][j][k],float(post[j][k]/total),places=12);self.assertAlmostEqual(r['dynamic']['logit_gradients'][j][k],float(p[j][k]-post[j][k]/total),places=12);checked+=1
    self.assertAlmostEqual(sum(o['probability'] for o in r['outputs']),1,places=12)
  self.assertGreater(checked,300)
 def test_finite_difference_logits(self):
  rng=random.Random(3);checks=0
  for _ in range(25):
   z=[[rng.uniform(-3,3) for _ in range(3)] for _ in range(4)];s=spec(z,[1,2]);r=audit(s)
   for t in range(4):
    for k in range(3):
     h=1e-5;orig=z[t][k];z[t][k]=orig+h;a=audit(s)['dynamic']['loss'];z[t][k]=orig-h;b=audit(s)['dynamic']['loss'];z[t][k]=orig;self.assertAlmostEqual((a-b)/(2*h),r['dynamic']['logit_gradients'][t][k],places=8);checks+=1
  self.assertEqual(checks,300)
 def test_repeat_minimum(self):
  for t in range(1,6):
   r=audit(spec([[0,0,0]]*t,[1,1,2]));self.assertEqual(r['dynamic']['minimum_frames'],4);self.assertEqual(r['dynamic']['possible'],t>=4)
 def test_impossible_has_no_fake_gradient(self):
  r=audit(spec([[0,0,0]],[1,1]));self.assertIsNone(r['dynamic']['loss']);self.assertIsNone(r['dynamic']['logit_gradients']);self.assertEqual(r['oracle']['matched_count'],0)
 def test_empty_input_target(self):
  r=audit(spec([]));self.assertEqual(r['dynamic']['probability'],1);self.assertEqual(r['paths'][0]['path'],[]);self.assertEqual(r['dynamic']['logit_gradients'],[])
 def test_empty_input_nonempty_target(self):self.assertFalse(audit(spec([],[1]))['dynamic']['possible'])
 def test_empty_target(self):
  r=audit(spec([[0,0,0]]*3));self.assertAlmostEqual(r['dynamic']['probability'],1/27);self.assertEqual(r['oracle']['matched_count'],1)
 def test_greedy_counterexample(self):
  r=audit(spec([[0,0],[0,0]],[1],c=2));self.assertEqual(r['greedy']['collapsed'],[]);self.assertEqual(r['best_output']['labels'],[1]);self.assertAlmostEqual(r['best_output']['probability'],.75);self.assertGreater(r['greedy_log_gap'],1)
 def test_shift_invariance(self):
  z=[[0,2,-1],[1,1,0],[0,-1,2]];a=audit(spec(z,[1,2]));b=audit(spec([[v+100 for v in row] for row in z],[1,2]));self.assertAlmostEqual(a['dynamic']['loss'],b['dynamic']['loss'],places=12)
 def test_underflow_retains_log_loss(self):
  r=audit(spec([[1000,-1000]]*2,[1],c=2));self.assertEqual(r['dynamic']['probability'],0);self.assertAlmostEqual(r['dynamic']['loss'],2000-math.log(2));self.assertTrue(r['dynamic']['possible'])
 def test_all_transition_constraints(self):
  r=audit(spec([[0,0,0]]*4,[1,1,2]));ext=r['dynamic']['extended_target']
  for a,b in r['dynamic']['transitions']:
   self.assertIn(b-a,[0,1,2]);self.assertFalse(b-a==2 and (ext[b]==0 or ext[a]==ext[b]))
 def test_baseline_fixture_reproduction(self):
  x=json.loads((R/'docs/audits.json').read_text())
  for c in x['cases']:self.assertEqual(audit(c['report']['spec']),c['report'])
 def test_invalid_specs(self):
  base=spec([[0,0,0]])
  bad=[dict(base,target=[0]),dict(base,blank=True),dict(base,logits=[[0,float('nan'),0]]),dict(base,logits=[[0,float('inf'),0]]),dict(base,logits=[[0,0]]),dict(base,logits=[[True,0,0]]),dict(base,logits=[[1e7,0,0]]),dict(base,symbols=['A','A','_']),dict(base,target=[1.5]),dict(base,extra=1),dict(base,logits=[[0]*4]*6,symbols=['_','a','b','c'])]
  for x in bad:
   with self.assertRaises(ValueError):audit(x)
 def test_strict_cli_json(self):
  from ctclab.cli import main
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';o=Path(d)/'o.json';p.write_text('{"symbols":[],"symbols":[]}');self.assertEqual(main(['--spec',str(p),'--json',str(o)]),2);self.assertFalse(o.exists())
 def test_cli_roundtrip(self):
  from ctclab.cli import main
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';o=Path(d)/'o.json';s=spec([[0,1,0]]*3,[1,1]);p.write_text(json.dumps(s));self.assertEqual(main(['--spec',str(p),'--json',str(o)]),0);self.assertEqual(json.loads(o.read_text()),audit(s))
 def test_no_nonfinite_serialization(self):
  for y in [[],[1],[1,1],[1,2,1]]:json.dumps(audit(spec([[0,0,0]],y)),allow_nan=False)
 def test_blank_relabeling(self):
  z=[[1,0,2],[0,1,2]];a=audit(spec(z,[1]));b=audit(spec([[row[1],row[0],row[2]] for row in z],[0],1));self.assertAlmostEqual(a['dynamic']['loss'],b['dynamic']['loss'])
 def test_frame_posterior_is_target_conditioned(self):
  r=audit(spec([[0,0,0]]*3,[1]));self.assertTrue(all(row[2]==0 for row in r['dynamic']['label_posteriors']));self.assertTrue(all(row[2]>0 for row in r['dynamic']['logit_gradients']))
 def test_independent_state_sequence_oracle(self):
  rng=random.Random(81)
  for i in range(40):
   t=1+i%4;y=[1]*(i%3);z=[[rng.randint(-2,2) for _ in range(3)] for _ in range(t)];r=audit(spec(z,y));d=r['dynamic'];ext=[0]
   for k in y:ext.extend([k,0])
   n=len(ext);mass=0.;occupancy=[[0.]*n for _ in range(t)];count=0
   for states in itertools.product(range(n),repeat=t):
    if states[0] not in ([0] if n==1 else [0,1]) or states[-1] not in ([0] if n==1 else [n-2,n-1]):continue
    valid=True
    for a,b in zip(states,states[1:]):
     delta=b-a
     if delta not in [0,1,2] or (delta==2 and (ext[b]==0 or ext[a]==ext[b])):valid=False;break
    if not valid:continue
    prob=math.prod(d['probabilities'][j][ext[k]] for j,k in enumerate(states));mass+=prob;count+=1
    for j,k in enumerate(states):occupancy[j][k]+=prob
   self.assertEqual(count,r['oracle']['matched_count']);self.assertAlmostEqual(mass,d['probability'],places=12)
   if mass:
    for j in range(t):
     for k in range(n):self.assertAlmostEqual(occupancy[j][k]/mass,d['state_posteriors'][j][k],places=12)
 def test_maximum_path_boundary(self):
  r=audit(spec([[0]*4]*5,[1,2],c=4));self.assertEqual(len(r['paths']),1024);self.assertAlmostEqual(sum(o['probability'] for o in r['outputs']),1,places=12)
 def test_declared_rank_buckets(self):
  r=audit(spec([[0,0,0]]*3,[1]));self.assertEqual(r['ranking_resolution_nats'],1e-8);keys=[(-o['rank_bucket'],o['labels']) for o in r['outputs']];self.assertEqual(keys,sorted(keys))
  for o in r['outputs']:self.assertEqual(o['rank_bucket'],math.floor(o['log_probability']*1e8+.5))
 def test_integral_json_indices(self):
  r=audit(spec([[0,0,0]]*3,[1.0],0.0));self.assertTrue(r['dynamic']['possible']);self.assertEqual(r['oracle']['matched_count'],6)
 def test_huge_numbers_fail_cleanly(self):
  for s in [spec([[10**1000,0,0]]),spec([[0,0,0]],[10**1000]),spec([[0,0,0]],b=10**1000)]:
   with self.assertRaises(ValueError):audit(s)
if __name__=='__main__':unittest.main()
