import json
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
root=Path(sys.argv[1]).resolve()
from ctclab.prefix import audit_prefix
from ctclab.prefix_verify import verify_prefix
from ctclab.prefix_controls import definitions
modules=['ctclab','ctclab.core','ctclab.cli','ctclab.__main__','ctclab.prefix_input','ctclab.prefix','ctclab.prefix_verify','ctclab.prefix_controls','ctclab.prefix_cli']
for name in modules:
    origin=Path(importlib.util.find_spec(name).origin).resolve()
    assert root not in origin.parents and 'site-packages'in str(origin),origin
script=str(Path(sys.executable).parent/'ctclab-prefix');forgeries=0
for c in definitions():
    Path('request.json').write_text(json.dumps(c['request']))
    a=audit_prefix(c['request']);assert verify_prefix(a)
    for cmd in [[script],[sys.executable,'-I','-m','ctclab.prefix_cli']]:
        out=subprocess.check_output(cmd+['audit','--input','request.json']);assert json.loads(out)==a;Path('report.json').write_bytes(out)
        result=json.loads(subprocess.check_output(cmd+['verify','--input','report.json']));assert result['valid']is True
        b=json.loads(out);b['discarded_mass']='1';Path('forged.json').write_text(json.dumps(b));bad=subprocess.run(cmd+['verify','--input','forged.json'],capture_output=True)
        assert bad.returncode==2 and not bad.stdout;forgeries+=1
print(json.dumps(dict(installed_modules=len(modules),controls=len(definitions()),entrypoints=2,forged_cli_rejections=forgeries)))
