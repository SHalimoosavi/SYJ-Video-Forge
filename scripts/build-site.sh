#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT="$ROOT/site"
rm -rf "$OUT"
mkdir -p "$OUT/src"
cp "$ROOT/index.html" "$ROOT/styles.css" "$OUT/"
cp "$ROOT/src/core.js" "$ROOT/src/providers.js" "$ROOT/src/app.js" "$ROOT/src/bundles.js" "$ROOT/src/bundle-flow.js" "$OUT/src/"
printf 'Built static site into %s\n' "$OUT"
