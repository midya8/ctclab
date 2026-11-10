import copy
from fractions import Fraction as F
from itertools import product
import json
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from ctclab.prefix import audit_prefix
from ctclab.prefix_verify import verify_prefix
from ctclab.prefix_input import validate,loads


def request(rows=None,width=2,blank=0,symbols=None):
    return dict(symbols=symbols or ['_','A','B'],blank=blank,frames=rows if rows is not None else [['1/3']*3]*3,beam_width=width)

class PrefixTests(unittest.TestCase):
    def test_uniform_greedy_and_beam_loss(self):
        r=request([['1/2','1/2']]*2,1,symbols=['_','A']);a=audit_prefix(r)
        self.assertTrue(verify_prefix(a));self.assertEqual(a['beam_winner'],[]);self.assertEqual(a['exact_winners'],[[1]])
        self.assertEqual(a['discarded_mass'],'3/4');self.assertEqual(a['exact_regret'],'1/2')
        r['beam_width']=2;b=audit_prefix(r);verify_prefix(b)
        self.assertEqual(b['beam_winner'],[1]);self.assertEqual(b['beam_winner_full_mass'],'3/4');self.assertEqual(b['discarded_mass'],'0');self.assertTrue(b['sufficient_unique_map'])
    def test_empty_deterministic_and_repeat(self):
        for r,expected in [(request([],1),[]),(request([['0','1','0']]*6,1),[1]),(request([['0','1','0'],['1','0','0'],['0','1','0']],1),[1,1]),(request([['1','0','0'],['0','1','0'],['1','0','0']],1,1),[0,0])]:
            a=audit_prefix(r);verify_prefix(a);self.assertEqual(a['beam_winner'],expected);self.assertEqual(a['retained_mass'],'1');self.assertTrue(a['sufficient_unique_map'])
    def test_seeded_path_oracles_and_bounds(self):
        rng=random.Random(87210);allocations=0;certificates=0
        for j in range(120):
            S=rng.randrange(2,5);T=rng.randrange(7);frames=[]
            for t in range(T):
                v=[rng.randrange(6)for _ in range(S)]
                if not sum(v):v[0]=1
                frames.append([str(F(x,sum(v)))for x in v])
            r=request(frames,rng.choice([1,2,3,4,8,64]),rng.randrange(S),[str(s)for s in range(S)]);before=copy.deepcopy(r);a=audit_prefix(r);verify_prefix(a);self.assertEqual(r,before)
            self.assertEqual(F(a['retained_mass'])+F(a['discarded_mass']),1)
            self.assertEqual(sum(F(x['full_mass'])for x in a['transcripts']),1)
            self.assertEqual(sum(F(x['missing_mass'])for x in a['transcripts']),F(a['discarded_mass']))
            for x in a['transcripts']:
                self.assertLessEqual(F(x['retained_mass']),F(x['full_mass']));self.assertLessEqual(F(x['full_mass']),F(x['retained_mass'])+F(a['discarded_mass']))
            if a['sufficient_unique_map']:
                self.assertEqual(a['exact_winners'],[a['beam_winner']]);certificates+=1
            allocations+=S**T
        print('prefix independent path cases',120,'complete paths',allocations,'sufficient certificates',certificates)
    def test_wide_beam_exact_and_tie_lex(self):
        for S,T in [(2,6),(3,4),(4,3)]:
            a=audit_prefix(request([[str(F(1,S))]*S]*T,64,0,[str(s)for s in range(S)]));verify_prefix(a)
            self.assertEqual(a['discarded_mass'],'0');self.assertEqual(a['exact_regret'],'0');self.assertEqual(a['beam_winner'],min(a['exact_winners']))
        a=audit_prefix(request([['0','1/2','1/2']],1));self.assertEqual(a['beam_winner'],[1]);self.assertFalse(a['sufficient_unique_map'])
    def test_schema_probability_and_token_rejection(self):
        base=request()
        for key,values in [('beam_width',[True,0,65,1.0,'2']),('blank',[True,-1,3,0.0]),('symbols',[[],['a','a'],['_','雪'],['_','a b']]),('frames',[[['1/2']*3],[['01','0','1']],[['2/4','1/2','0']],[['-0','0','1']],[['1e0','0','0']],[['0','0','0']],[['1/1000001','1000000/1000001','0']],[[True,'0','1']]])]:
            for v in values:
                r=copy.deepcopy(base);r[key]=v
                with self.assertRaises(ValueError):validate(r)
        for text in ['{"a":1,"a":2}','{"blank":0.0}','{"blank":0e0}','{"x":NaN}','['*1200]:
            with self.assertRaises(ValueError):loads(text)
        for r in [{},dict(base,extra=0)]:
            with self.assertRaises(ValueError):validate(r)
    def test_all_nonrequest_primitive_mutations(self):
        a=audit_prefix(request());paths=[]
        def visit(x,p):
            if isinstance(x,dict):
                for k,v in x.items():
                    if k!='request':visit(v,p+[k])
            elif isinstance(x,list):
                for i,v in enumerate(x):visit(v,p+[i])
            else:paths.append(p)
        visit(a,[])
        for p in paths:
            b=copy.deepcopy(a);x=b
            for k in p[:-1]:x=x[k]
            old=x[p[-1]];x[p[-1]]=not old if type(old)is bool else old+1 if type(old)is int else old+'!'
            with self.assertRaises(ValueError):verify_prefix(b)
        for val in [1.0,True]:
            b=copy.deepcopy(a);b['steps'][0]['frame']=val
            with self.assertRaises(ValueError):verify_prefix(b)
        print('prefix individually rejected nonrequest primitive mutations',len(paths))
    def test_selected_wider_beam_regression(self):
        from ctclab.prefix_controls import definitions
        reports=[audit_prefix(c['request'])for c in definitions()]
        for a in reports:verify_prefix(a)
        a,b,c=reports[6:9]
        self.assertEqual(a['beam_winner'],[1,2]);self.assertEqual(b['beam_winner'],[2,1,2])
        self.assertEqual(a['beam_winner_full_mass'],'47403/226100');self.assertEqual(b['beam_winner_full_mass'],'11691/56525')
        self.assertLess(F(b['beam_winner_full_mass']),F(a['beam_winner_full_mass']))
        self.assertGreater(F(b['retained_mass']),F(a['retained_mass']))
        self.assertEqual(c['discarded_mass'],'0');self.assertEqual(c['exact_regret'],'0')
        self.assertEqual(reports[9]['exact_regret'],'0');self.assertFalse(reports[9]['sufficient_unique_map'])
        for a in reports:
            self.assertEqual(sum(F(x['discarded_here'])for x in a['steps']),F(a['discarded_mass']))
            for row in a['steps']:
                self.assertEqual(row['candidate_mass'],row['incoming_mass'])
                self.assertEqual(sum(F(x['mass'])for x in row['transitions']),F(row['incoming_mass']))
    def test_exhaustive_small_laws_and_large_denominators(self):
        n=0
        for probabilities in product([F(0),F(1,3),F(2,3),F(1)],repeat=3):
            for blank in [0,1]:
                for width in [1,2,4]:
                    r=request([[str(p),str(1-p)]for p in probabilities],width,blank,['_','A']);a=audit_prefix(r);verify_prefix(a);n+=1
        for width in [1,64]:
            a=audit_prefix(request([['1/1000000','999999/1000000','0']]*6,width));verify_prefix(a)
        print('exhaustive three-frame binary laws/blank/width cases',n)
    def test_boundary_and_atomic_cli(self):
        r=request([['1/4']*4]*6,64,3,['a','b','c','_']);a=audit_prefix(r);verify_prefix(a);self.assertLess(len(json.dumps(a).encode()),8*1024*1024)
        with tempfile.TemporaryDirectory()as d:
            src=Path(d)/'request.json';out=Path(d)/'out.json';src.write_text(json.dumps(r));root=Path(__file__).resolve().parents[1]
            def run(*args):return subprocess.run([sys.executable,'-m','ctclab.prefix_cli',*args],cwd=root,text=True,capture_output=True)
            p=run('audit','--input',str(src),'--output',str(out));self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(out.read_text()),a)
            p=run('verify','--input',str(out));self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)['valid'])
            original=out.read_bytes();src.write_text('{"beam_width":2,"beam_width":3}')
            p=run('audit','--input',str(src),'--output',str(out));self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertEqual(out.read_bytes(),original)
            p=run('audit','--input',str(out),'--output',str(out));self.assertEqual(p.returncode,2);self.assertEqual(out.read_bytes(),original);self.assertEqual(len(list(Path(d).glob('.ctc-prefix-*'))),0)
