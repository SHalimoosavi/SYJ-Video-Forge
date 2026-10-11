#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
echo '=== Node.js tests ==='
node --test tests/*.test.js
echo '=== Python unittest suite (integration is explicitly skipped if ffmpeg/ffprobe are absent) ==='
python -m unittest discover -s backend/tests -v
echo '=== Python syntax ==='
python -m py_compile backend/*.py backend/providers/*.py backend/tests/*.py scripts/dev_server.py scripts/static_check.py
echo '=== JavaScript syntax ==='
node --check src/core.js
node --check src/providers.js
node --check src/app.js
echo '=== Build static site ==='
sh scripts/build-site.sh
echo '=== Static checks ==='
python scripts/static_check.py
echo '=== Git whitespace check for tracked/staged changes (when inside Git) ==='
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then git diff --check; git diff --cached --check; else echo 'SKIP: not a Git working tree'; fi
echo 'VERIFY: PASS'
