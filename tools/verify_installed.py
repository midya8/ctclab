import json,sys,importlib.util
from pathlib import Path
import ctclab
from ctclab import audit
root=Path(sys.argv[1]).resolve();origins={m:importlib.util.find_spec(m).origin for m in ['ctclab','ctclab.core','ctclab.cli','ctclab.__main__']}
for m,p in origins.items():assert 'site-packages' in p and not Path(p).resolve().is_relative_to(root),(m,p)
for case in json.loads((root/'docs/audits.json').read_text())['cases']:assert audit(case['report']['spec'])==case['report']
print(json.dumps(dict(cases=20,module_origins=origins)))
