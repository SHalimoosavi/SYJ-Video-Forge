#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
echo "== Node tests =="; node --test tests/*.test.js
echo "== Static checks =="; python3 scripts/static_check.py
echo "== Python syntax =="; python3 -m py_compile scripts/dev_server.py scripts/static_check.py
echo "VERIFY: PASS"
