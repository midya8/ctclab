import json,sys,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from ctclab import audit

def build():
 cases=[]
 def add(name,z,y=(),b=0,symbols=None):
  spec=dict(symbols=symbols or ['_','A','B'],blank=b,logits=z,target=list(y));cases.append(dict(name=name,report=audit(spec)))
 add('Best path is not best collapsed output',[[0,0],[0,0]],symbols=['_','A'],y=[1])
 add('Repeated label needs a blank',[[0,1,0],[0,1,0]],[1,1])
 add('Repeated label at its minimum length',[[0,1,0],[2,0,0],[0,1,0]],[1,1])
 add('Two labels, many alignments',[[0,2,-1],[1,1,0],[0,-1,2]],[1,2])
 add('Empty target is all blanks',[[0,2,1],[2,1,0]],[])
 add('Empty input and empty target',[],[])
 add('Empty input and nonempty target',[],[1])
 add('Nonzero blank index',[[2,0,1],[0,2,1],[1,0,2]],[0,2],1,['A','_','B'])
 add('Likelihood underflows, loss stays finite',[[1000,-1000],[1000,-1000]],[1],symbols=['_','A'])
 add('Blank-dominant output',[[4,-2,-2],[4,-2,-2],[4,-2,-2]],[1])
 add('Frame shift invariance',[[100,102,99],[101,101,100],[100,99,102]],[1,2])
 add('Four symbols',[[0,1,2,-1],[1,-1,0,2]],[2,3],symbols=['_','A','B','C'])
 rng=random.Random(17)
 for i in range(8):add('Seeded finite control '+str(i),[[rng.randint(-3,3) for _ in range(3)] for _ in range(2+i%3)],[1]*(i%3))
 return dict(schema_version=1,cases=cases)
if __name__=='__main__':
 x=build();(R/'docs/audits.json').write_text(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n');(R/'examples/repeat.json').write_text(json.dumps(x['cases'][2]['report']['spec'],indent=2)+'\n');print('Retained',len(x['cases']),'complete CTC witnesses')
