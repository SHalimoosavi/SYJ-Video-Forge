#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
echo '=== Node.js tests ==='
node --test tests/*.test.js
echo '=== Python backend unittest suite (FFmpeg integration skips explicitly when unavailable) ==='
python -m unittest discover -s backend/tests -v
echo '=== Python worker unittest suite (no torch required; FFmpeg integration skips explicitly when unavailable) ==='
python -m unittest discover -s worker/tests -v
echo '=== Python syntax ==='
python -m py_compile backend/*.py backend/providers/*.py backend/tests/*.py worker/*.py worker/engines/*.py worker/tests/*.py scripts/dev_server.py scripts/static_check.py scripts/test_notebook.py
echo '=== JavaScript syntax ==='
for file in src/core.js src/providers.js src/app.js src/bundles.js src/bundle-flow.js; do node --check "$file"; done
echo '=== Notebook structure ==='
python scripts/test_notebook.py
echo '=== Build static site ==='
sh scripts/build-site.sh
echo '=== Static checks ==='
python scripts/static_check.py
echo '=== Git whitespace check (when inside Git) ==='
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then git diff --check; git diff --cached --check; else echo 'SKIP: not a Git working tree'; fi
echo 'VERIFY: PASS'
