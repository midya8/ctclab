#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; tmp="$(mktemp -d)";trap 'rm -rf "$tmp"' EXIT
python -m pip wheel --no-deps --wheel-dir "$tmp/dist" "$root"
python -m venv "$tmp/env"
"$tmp/env/bin/python" -m pip install --no-deps "$tmp"/dist/*.whl
cd "$tmp"
"$tmp/env/bin/python" -I "$root/tools/verify_installed.py" "$root"
"$tmp/env/bin/python" -I "$root/tools/verify_prefix_installed.py" "$root"
"$tmp/env/bin/ctclab" --spec "$root/examples/repeat.json" --json original.json
"$tmp/env/bin/python" -I - "$root" <<'PY'
import sys,json
from pathlib import Path
from ctclab import audit
assert json.load(open('original.json'))==audit(json.loads((Path(sys.argv[1])/'examples/repeat.json').read_text()))
print('original target atlas and exact prefix installed modes reproduced outside checkout')
PY
