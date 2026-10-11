$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
function Run-Check([string]$Label, [scriptblock]$Command) {
    Write-Output "=== $Label ==="
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE" }
}
Run-Check 'Node.js tests' { node --test tests/*.test.js }
Run-Check 'Python backend unittest suite' { python -m unittest discover -s backend/tests -v }
Run-Check 'Python worker unittest suite' { python -m unittest discover -s worker/tests -v }
Run-Check 'Python syntax' { python -m compileall -q backend worker scripts }
Run-Check 'JavaScript syntax core' { node --check src/core.js }
Run-Check 'JavaScript syntax providers' { node --check src/providers.js }
Run-Check 'JavaScript syntax app' { node --check src/app.js }
Run-Check 'JavaScript syntax bundles' { node --check src/bundles.js }
Run-Check 'JavaScript syntax bundle flow' { node --check src/bundle-flow.js }
Run-Check 'Notebook structure' { python scripts/test_notebook.py }
Run-Check 'Build static site' { & (Join-Path $Root 'scripts/build-site.ps1') }
Run-Check 'Static checks' { python scripts/static_check.py }
Write-Output 'VERIFY: PASS'
