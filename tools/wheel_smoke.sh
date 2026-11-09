#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)";tmp="$(mktemp -d)";trap 'rm -rf "$tmp"' EXIT
python -m pip wheel --no-deps --wheel-dir "$tmp/dist" "$root" > "$tmp/build.log"
python -m venv "$tmp/env"
"$tmp/env/bin/python" -m pip install --no-deps "$tmp"/dist/*.whl > "$tmp/install.log"
cd "$tmp"
"$tmp/env/bin/python" -I "$root/tools/verify_installed.py" "$root"
"$tmp/env/bin/ctclab" --spec "$root/examples/repeat.json" --json cli.json
"$tmp/env/bin/python" -I - "$root" <<'PY'
import json,sys
from pathlib import Path
from ctclab import audit
r=Path(sys.argv[1]);assert json.load(open('cli.json'))==audit(json.load(open(r/'examples/repeat.json')))
assert json.load(open('cli.json'))['oracle']['matched_count']==1
print('Installed console CLI, repeated-label probability, all 20 reports and four module origins passed')
PY
