import argparse,json
from pathlib import Path
from .core import audit

def main(argv=None):
 p=argparse.ArgumentParser(description='Bounded CTC target/gradient/path audit; no acoustic model');p.add_argument('--spec',required=True);p.add_argument('--json',required=True);a=p.parse_args(argv)
 try:
  f=Path(a.spec)
  if f.stat().st_size>65536:raise ValueError('Spec exceeds 64KiB')
  def unique(rows):
   o={}
   for k,v in rows:
    if k in o:raise ValueError('Duplicate JSON key')
    o[k]=v
   return o
  s=json.loads(f.read_text(),object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON token')))
  r=audit(s);Path(a.json).write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n');print('possible' if r['dynamic']['possible'] else 'impossible target; loss/gradients undefined');return 0
 except (ValueError,OSError,UnicodeError,OverflowError) as e:print('ERROR',e);return 2
