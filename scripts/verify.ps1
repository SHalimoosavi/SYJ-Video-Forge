$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
Write-Output "== Node tests =="; node --test tests/*.test.js
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "== Static checks =="; python scripts/static_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "== Python syntax =="; python -m py_compile scripts/dev_server.py scripts/static_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "VERIFY: PASS"
