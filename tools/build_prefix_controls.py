import json
from pathlib import Path
from ctclab.prefix_controls import definitions
p=Path(__file__).resolve().parents[1]
(p/'docs/prefix-data.js').write_text('globalThis.CTC_PREFIX_CONTROLS = '+json.dumps(definitions(),ensure_ascii=True,separators=(',',':'))+';\n')
(p/'examples/prefix-selection.json').write_text(json.dumps(definitions()[6]['request'],indent=2)+'\n')
