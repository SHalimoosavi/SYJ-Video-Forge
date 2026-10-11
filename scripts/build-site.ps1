$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Out = Join-Path $Root 'site'
if (Test-Path $Out) { Remove-Item -Recurse -Force $Out }
New-Item -ItemType Directory -Force -Path (Join-Path $Out 'src') | Out-Null
Copy-Item (Join-Path $Root 'index.html'), (Join-Path $Root 'styles.css') -Destination $Out
Copy-Item (Join-Path $Root 'src/core.js'), (Join-Path $Root 'src/providers.js'), (Join-Path $Root 'src/app.js'), (Join-Path $Root 'src/bundles.js'), (Join-Path $Root 'src/bundle-flow.js') -Destination (Join-Path $Out 'src')
Write-Output "Built static site into $Out"
